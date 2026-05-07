"""Prompt registry — versioning, environments, promotion, rollback.

Models:
  - PromptVersion: an immutable (template_body, defaults, content_hash, metadata)
  - Registry: stores versions; environment labels point at a version

In production this is a DynamoDB table with two indexes:
  PK = prompt_id        SK = content_hash    → versions
  PK = prompt_id#env    SK = "current"       → environment pointers
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from src.templates import Template


@dataclass
class PromptVersion:
    prompt_id: str
    content_hash: str
    template: str
    defaults: dict
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def of(cls, prompt_id: str, template: str, defaults: dict | None = None, notes: str = "") -> "PromptVersion":
        defaults = dict(defaults or {})
        # Hash over the template + sorted default keys (not values — values are runtime)
        h = hashlib.sha256(json.dumps(
            {"t": template, "k": sorted(defaults.keys())}, sort_keys=True
        ).encode()).hexdigest()[:12]
        return cls(prompt_id=prompt_id, content_hash=h, template=template,
                   defaults=defaults, notes=notes)


@dataclass
class Registry:
    versions: dict[str, dict[str, PromptVersion]] = field(default_factory=dict)  # id -> hash -> version
    env_pointers: dict[str, dict[str, str]] = field(default_factory=dict)        # id -> env -> hash
    path: Path | None = None

    def __post_init__(self):
        if self.path and self.path.exists():
            self._load()

    def _load(self):
        data = json.loads(self.path.read_text())
        self.versions = {
            pid: {h: PromptVersion(**v) for h, v in versions.items()}
            for pid, versions in data.get("versions", {}).items()
        }
        self.env_pointers = data.get("env_pointers", {})

    def _persist(self):
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        out = {
            "versions": {
                pid: {h: asdict(v) for h, v in versions.items()}
                for pid, versions in self.versions.items()
            },
            "env_pointers": self.env_pointers,
        }
        self.path.write_text(json.dumps(out, indent=2))

    # --- API -----------------------------------------------------------------

    def register(self, version: PromptVersion) -> PromptVersion:
        self.versions.setdefault(version.prompt_id, {})[version.content_hash] = version
        self._persist()
        return version

    def promote(self, prompt_id: str, content_hash: str, env: str):
        if prompt_id not in self.versions or content_hash not in self.versions[prompt_id]:
            raise KeyError(f"unknown version {prompt_id}@{content_hash}")
        self.env_pointers.setdefault(prompt_id, {})[env] = content_hash
        self._persist()

    def rollback(self, prompt_id: str, env: str, prior_hash: str):
        self.promote(prompt_id, prior_hash, env)

    def get(self, prompt_id: str, env: str) -> PromptVersion:
        h = self.env_pointers.get(prompt_id, {}).get(env)
        if not h:
            raise KeyError(f"no version of {prompt_id} promoted to {env}")
        return self.versions[prompt_id][h]

    def render(self, prompt_id: str, env: str, **vars) -> str:
        v = self.get(prompt_id, env)
        merged = {**v.defaults, **vars}
        return Template(name=prompt_id, body=v.template).render(**merged)
