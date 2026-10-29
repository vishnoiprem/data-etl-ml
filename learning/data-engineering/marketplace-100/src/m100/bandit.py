"""
bandit.py — UCB1 multi-armed bandit for category selection.

This replaces the hand-rolled `categories_to_rotate()` policy
in marketplace_client.py. Instead of cycling through
categories, the bandit **learns** which categories produce
higher quality_score and biases selection toward them.

Why this is the right thing:

  * The naive rotate policy treats every category as equal.
    But over 100 iterations, you'll discover that some
    categories consistently produce thin data (lots of
    `quality_score=0.2` retries) and others produce rich
    data (0.8+). Rotating wastes iterations on the bad
    arms.

  * UCB1 (Auer, Cesa-Bianchi, Fischer 2002) is the
    textbook solution. After each pull, update the
    estimated reward for the chosen arm. To choose the
    next arm, take the one with the highest upper
    confidence bound:

        UCB(a) = mean_reward(a) + c * sqrt(2 * ln(N) / n_a)

    Where N = total pulls, n_a = pulls of arm a, c is
    the exploration constant (default sqrt(2), the
    theoretical optimum for [0,1] rewards).

  * The exploration term shrinks as n_a grows, so
    well-explored arms get picked less; the bandit
    naturally moves from exploration to exploitation.

  * Crash-safety: state is persisted to Lakebase
    `bandit_state` (Postgres) AND a Delta fallback
    table. On boot, we read the most recent state.

  * The agent can also override the bandit's choice
    with its own `next_category` from the tool-use
    response. We blend: bandit default → agent
    override (with a cooldown so the agent doesn't
    flip-flop).

State shape (one row per arm):

    arm              STRING  -- category name
    pulls            BIGINT  -- n_a
    sum_reward       DOUBLE  -- for mean computation
    last_pulled_at   TIMESTAMP

UCB computation reads all arms at once.
"""

from __future__ import annotations

import logging
import math
import os
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================
# Arm state
# ============================================================

@dataclass
class Arm:
    """A single category arm."""
    name: str
    pulls: int = 0
    sum_reward: float = 0.0
    last_pulled_at: Optional[float] = None  # epoch seconds

    @property
    def mean_reward(self) -> float:
        return self.sum_reward / self.pulls if self.pulls > 0 else 0.0

    def ucb(self, total_pulls: int, c: float = math.sqrt(2)) -> float:
        """Upper confidence bound. Inf if arm hasn't been pulled.

        `c=sqrt(2)` is the theoretical optimum for [0,1] rewards
        (Auer et al. 2002). Higher c → more exploration.
        """
        if self.pulls == 0:
            return float("inf")  # always pull an unpulled arm first
        return self.mean_reward + c * math.sqrt(2 * math.log(total_pulls) / self.pulls)

    def update(self, reward: float) -> None:
        """Update after a pull."""
        self.pulls += 1
        self.sum_reward += reward
        self.last_pulled_at = time.time()


# ============================================================
# Bandit
# ============================================================

# The 10 categories the bandit plays over. We intentionally
# keep this list stable so the bandit has a fixed arm set —
# adding a category mid-run would require a Bayesian cold-start
# trick (we don't do that in v1).
DEFAULT_ARMS = [
    "Finance", "Healthcare", "Geospatial", "Retail",
    "Transportation", "Energy", "Climate", "Public Sector",
    "Marketing", "Sports",
]


class CategoryBandit:
    """UCB1 multi-armed bandit over marketplace categories.

    Usage:
        bandit = CategoryBandit(arms=DEFAULT_ARMS)
        for i in range(100):
            cat = bandit.choose()
            listing = mkt.pick_top(category=cat, ...)
            quality = agent.evaluate(...)
            bandit.update(cat, quality)

    Persistence:
        * `snapshot()` → dict ready for DB write
        * `restore(snap)` → rebuild from dict
        * See `bandit_state.py` for the Lakebase/Delta wiring.
    """

    def __init__(
        self,
        arms: Optional[list[str]] = None,
        c: float = math.sqrt(2),
        agent_override_cooldown: int = 3,
    ):
        self.arms = {name: Arm(name=name) for name in (arms or DEFAULT_ARMS)}
        self.c = c
        # Cooldown on the agent's `next_category` override — so
        # the bandit has a chance to update before the agent
        # flips the choice again.
        self._override_cooldown = agent_override_cooldown
        self._last_override_iter: Optional[int] = None
        self._last_override_arm: Optional[str] = None
        self._iter_count = 0

    # ----- core --------------------------------------------------------

    def choose(self, agent_override: Optional[str] = None) -> str:
        """Pick the next category to explore.

        `agent_override`: if the M100Agent's tool-use response
        included `next_category`, use it (unless we're still
        in cooldown from the last override).
        """
        self._iter_count += 1

        # Honor the agent's override, but enforce cooldown so the
        # bandit can update before the next flip.
        if (
            agent_override
            and agent_override in self.arms
            and not self._in_cooldown(agent_override)
        ):
            self._last_override_iter = self._iter_count
            self._last_override_arm = agent_override
            logger.info("bandit: honoring agent override → %s", agent_override)
            return agent_override

        # Standard UCB1 pick
        total = sum(a.pulls for a in self.arms.values()) + 1
        best_arm = max(self.arms.values(), key=lambda a: a.ucb(total, self.c))
        logger.info(
            "bandit: chose %s (pulls=%d mean=%.3f ucb=%.3f)",
            best_arm.name, best_arm.pulls,
            best_arm.mean_reward, best_arm.ucb(total, self.c),
        )
        return best_arm.name

    def update(self, arm_name: str, reward: float) -> None:
        """Update the chosen arm with the observed reward.

        `reward` is the agent's `quality_score` (clipped to
        [0, 1] so a bad agent response can't poison the bandit).
        """
        if arm_name not in self.arms:
            logger.warning("bandit: unknown arm %s; skipping update", arm_name)
            return
        reward = max(0.0, min(1.0, float(reward)))
        self.arms[arm_name].update(reward)

    # ----- diagnostics -------------------------------------------------

    def summary(self) -> dict:
        """For the digest / agent tool-use."""
        return {
            arm.name: {
                "pulls": arm.pulls,
                "mean_reward": round(arm.mean_reward, 3),
                "last_pulled_at": arm.last_pulled_at,
            }
            for arm in self.arms.values()
        }

    def best_arm(self) -> str:
        """The current best (highest mean reward, with at least 2 pulls).

        We use `>= 2` (not `>= 3`) so an arm with 2 high-reward
        pulls can outrank an arm with 5 low-reward pulls. UCB1
        already handles the exploration; best_arm is for the
        digest's "what's the agent's best category so far?"
        KPI, not the next-step decision.
        """
        candidates = [a for a in self.arms.values() if a.pulls >= 2]
        if not candidates:
            return max(self.arms.values(), key=lambda a: a.pulls).name
        return max(candidates, key=lambda a: a.mean_reward).name

    # ----- snapshot / restore ------------------------------------------

    def snapshot(self) -> dict:
        return {
            "arms": {
                name: {
                    "pulls": a.pulls,
                    "sum_reward": a.sum_reward,
                    "last_pulled_at": a.last_pulled_at,
                }
                for name, a in self.arms.items()
            },
            "c": self.c,
            "iter_count": self._iter_count,
        }

    def restore(self, snap: dict) -> None:
        arms = snap.get("arms", {})
        for name, state in arms.items():
            if name not in self.arms:
                self.arms[name] = Arm(name=name)
            self.arms[name].pulls = int(state.get("pulls", 0))
            self.arms[name].sum_reward = float(state.get("sum_reward", 0.0))
            self.arms[name].last_pulled_at = state.get("last_pulled_at")
        self.c = float(snap.get("c", self.c))
        self._iter_count = int(snap.get("iter_count", 0))

    # ----- internals ---------------------------------------------------

    def _in_cooldown(self, arm_name: str) -> bool:
        """True if the agent just overrode to this arm and we're still cooling down."""
        if self._last_override_arm != arm_name:
            return False
        if self._last_override_iter is None:
            return False
        return (self._iter_count - self._last_override_iter) < self._override_cooldown


# ============================================================
# Persistence — Lakebase (primary) + Delta (fallback)
# ============================================================

# Lakebase DDL — added to the main connect() schema setup
BANDIT_DDL = """
CREATE TABLE IF NOT EXISTS bandit_state (
    name            TEXT PRIMARY KEY,
    pulls           BIGINT NOT NULL DEFAULT 0,
    sum_reward      DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    last_pulled_at  TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


def save_to_lakebase(conn, bandit: CategoryBandit) -> None:
    """Upsert every arm's state. Idempotent."""
    if conn is None:
        return
    with conn.cursor() as cur:
        for arm in bandit.arms.values():
            cur.execute("""
                INSERT INTO bandit_state (name, pulls, sum_reward, last_pulled_at, updated_at)
                VALUES (%s, %s, %s, to_timestamp(%s), NOW())
                ON CONFLICT (name) DO UPDATE SET
                    pulls = EXCLUDED.pulls,
                    sum_reward = EXCLUDED.sum_reward,
                    last_pulled_at = EXCLUDED.last_pulled_at,
                    updated_at = NOW()
            """, (
                arm.name, arm.pulls, arm.sum_reward,
                arm.last_pulled_at or 0.0,
            ))
    conn.commit()


def load_from_lakebase(conn, bandit: CategoryBandit) -> None:
    """Restore bandit state from Lakebase. No-op if table empty."""
    if conn is None:
        return
    with conn.cursor() as cur:
        cur.execute("SELECT name, pulls, sum_reward, "
                    "COALESCE(EXTRACT(EPOCH FROM last_pulled_at), 0) "
                    "FROM bandit_state")
        for name, pulls, sum_reward, ts in cur.fetchall():
            if name not in bandit.arms:
                bandit.arms[name] = Arm(name=name)
            bandit.arms[name].pulls = int(pulls)
            bandit.arms[name].sum_reward = float(sum_reward)
            bandit.arms[name].last_pulled_at = float(ts) if ts else None
