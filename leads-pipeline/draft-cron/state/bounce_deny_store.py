# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: '/Users/vishnoiprem/PycharmProjects/data-etl-ml/leads-pipeline/draft-cron/state/bounce_deny_store.py'
# Bytecode version: 3.10.b1 (3439)
# Source timestamp: 2026-10-12 17:38:07 UTC (1791826687)

"""\nbounce_deny_store.py — JSON-backed BOUNCE_DENY persistence.\n\nWhy: BOUNCE_DENY was a module-level set in find_more_leads.py. Any\nmutation made inside refine_pipeline.dedup_and_deny() was visible in\n*that* process only — find_more_leads.py ran in a fresh subprocess,\nso the denylist was effectively the 30 hardcoded seed domains.\n\nThis module:\n  - reads state/bounce_deny.json on import\n  - exposes BOUNCE_DENY as a live set\n  - persists additions via save() (atomic write)\n\nUsage:\n    from state.bounce_deny_store import BOUNCE_DENY, save, add\n    if \"anthropic.com\" in BOUNCE_DENY: ...\n    add(\"newdomain.com\")    # also saves to disk\n    save()                  # force-flush\n"""
from __future__ import annotations
global _seed_cache
import json
import os
import threading
import tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
STATE_PATH = Path(os.getenv('AVILX_BOUNCE_DENY_PATH', HERE / 'bounce_deny.json'))
_lock = threading.Lock()
def _load_from_disk() -> set[str]:
    if not STATE_PATH.exists():
        return set()
    try:
        with open(STATE_PATH) as f:
            data = json.load(f)
        seeds = data.get('seed') or []
        added = data.get('added') or []
        return {d.lower() for d in seeds + added if isinstance(d, str)}
    except Exception:
        return set()
def _save_to_disk(domains: set[str]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {'version': 1, 'seed': sorted(_seed_set()), 'added': sorted((d for d in domains if d not in _seed_set()))}
    fd, tmp_path = tempfile.mkstemp(prefix='.bounce_deny.', suffix='.tmp', dir=str(STATE_PATH.parent))
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(payload, f, indent=2)
        os.replace(tmp_path, STATE_PATH)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
_seed_cache: set[str] | None = None
def _seed_set() -> set[str]:
    global _seed_cache
    if _seed_cache is not None:
        return _seed_cache
    else:
        if STATE_PATH.exists():
            try:
                with open(STATE_PATH) as f:
                    data = json.load(f)
                seeds = data.get('seed') or []
                _seed_cache = {d.lower() for d in seeds if isinstance(d, str)}
                return _seed_cache
            except Exception:
                pass
        _seed_cache = set()
        return _seed_cache
BOUNCE_DENY: set[str] = _load_from_disk()
def save() -> None:
    with _lock:
        _save_to_disk(BOUNCE_DENY)
def add(domain: str) -> bool:
    """Add a domain to the denylist (persisted). Returns True if added."""
    d = (domain or '').lower().strip()
    if not d:
        return False
    else:
        with _lock:
            if d in BOUNCE_DENY:
                return False
            else:
                BOUNCE_DENY.add(d)
                _save_to_disk(BOUNCE_DENY)
        return True
def remove(domain: str) -> bool:
    """Remove a domain from the denylist. Returns True if removed."""
    d = (domain or '').lower().strip()
    with _lock:
        if d not in BOUNCE_DENY:
            return False
        else:
            BOUNCE_DENY.discard(d)
            _save_to_disk(BOUNCE_DENY)
    return True
def __getattr__(name):
    raise AttributeError(name)
if __name__ == '__main__':
    print(f'BOUNCE_DENY ({len(BOUNCE_DENY)} domains) from {STATE_PATH}:')
    for d in sorted(BOUNCE_DENY):
        print(f'  {d}')