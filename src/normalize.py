"""URL canonicalization defense.

Fold a URL back to a canonical ASCII form before the detector reads it: decode
punycode/IDN, map look-alike (confusable) characters back to their Latin skeleton,
lowercase, drop a leading www. This neutralizes the homoglyph/IDN domain-spoofing
family (Unicode TR39's original purpose). It does NOT help against structural
mimicry (HTTPS on a legitimate host) -- that is the honest ceiling of a URL-only view.
"""
from __future__ import annotations
from urllib.parse import urlparse, urlunparse
from .attacks import CONFUSABLES

SKELETON = {v: k for k, v in CONFUSABLES.items()}   # foreign look-alike -> Latin


def _skeleton(s: str) -> str:
    return "".join(SKELETON.get(ch, ch) for ch in s)


def normalize_url(url: str) -> str:
    p = urlparse(url if "//" in str(url) else "http://" + str(url))
    host = (p.hostname or "").lower()
    if "xn--" in host:                       # punycode -> unicode
        try:
            host = host.encode("ascii").decode("idna")
        except Exception:
            pass
    host = _skeleton(host)                    # unicode look-alikes -> Latin
    netloc = host + (f":{p.port}" if p.port else "")
    return urlunparse((p.scheme or "http", netloc, p.path, p.params, p.query, ""))


def normalize_many(urls):
    return [normalize_url(u) for u in urls]
