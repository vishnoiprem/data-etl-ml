"""Hash + base62 helpers used by the URL shortener and key generation.

base62 is the alphabet TinyURL-style short links use: a–z, A–Z, 0–9.
With 6 characters you get ~56 billion unique keys; with 7 you get ~3.5T.
"""

from __future__ import annotations

import hashlib

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
_BASE = len(ALPHABET)


def short_hash(url: str, length: int = 7) -> str:
    """Return a stable, deterministic short key for ``url``.

    We use the first 8 bytes of SHA-256 and convert to base62. Collisions
    are extremely rare at length=7 for any realistic workload, and the
    URL shortener service has a collision-check loop to handle them.
    """
    digest = hashlib.sha256(url.encode("utf-8")).digest()[:8]
    n = int.from_bytes(digest, "big")
    return base62_encode(n, length)


def base62_encode(n: int, length: int = 0) -> str:
    """Encode a non-negative integer as base62, zero-padded to ``length``."""
    if n < 0:
        raise ValueError("n must be non-negative")
    chars = []
    while n > 0:
        n, rem = divmod(n, _BASE)
        chars.append(ALPHABET[rem])
    encoded = "".join(reversed(chars)) or "0"
    if length and len(encoded) < length:
        encoded = encoded.rjust(length, "0")
    return encoded
