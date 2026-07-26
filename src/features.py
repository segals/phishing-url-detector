"""URL feature engineering.

The heart of a URL-based detector: turn a raw URL string into interpretable numeric
features. We stick to features computable from the URL *string alone* (no network
fetch), so the detector is fast, private, and reproducible.

Grouped as: length/count lexical, host/domain, TLD, path/query, entropy, and
brand/obfuscation signals. Brand look-alike uses Levenshtein edit distance to a small
list of frequently-impersonated brands (Ma et al. 2009; Garera et al. 2007).
"""
from __future__ import annotations
import math
import re
from collections import Counter
from urllib.parse import urlparse

import pandas as pd

# Frequently impersonated brands (for the look-alike / typo-squat feature).
BRANDS = ["paypal", "apple", "microsoft", "amazon", "google", "facebook", "netflix",
          "instagram", "whatsapp", "linkedin", "ebay", "bankofamerica", "chase",
          "wellsfargo", "dropbox", "office365", "outlook", "coinbase", "binance"]

# Common URL shorteners (redirection hides the true destination).
SHORTENERS = {"bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "is.gd", "buff.ly",
              "tiny.cc", "rebrand.ly", "cutt.ly", "shorturl.at", "rb.gy", "t.ly"}

# TLDs over-represented in abuse feeds (indicative, not decisive).
SUSPICIOUS_TLDS = {"zip", "mov", "xyz", "top", "tk", "ml", "ga", "cf", "gq", "click",
                   "link", "work", "kim", "country", "science", "party", "review"}

# Words phishing URLs use to look trustworthy or urgent.
CUE_WORDS = ["login", "signin", "secure", "account", "verify", "update", "confirm",
             "bank", "webscr", "ebayisapi", "password", "credential", "wallet",
             "invoice", "billing", "suspend", "unlock", "recover"]

_IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
_HEX_IP_RE = re.compile(r"^0x[0-9a-f]+$", re.I)


def _entropy(s: str) -> float:
    """Shannon entropy of a string (bits/char). High = random-looking."""
    if not s:
        return 0.0
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in Counter(s).values())


def _edit_distance(a: str, b: str) -> int:
    """Levenshtein distance (dynamic programming)."""
    m, n = len(a), len(b)
    prev = list(range(n + 1))
    for i in range(1, m + 1):
        cur = [i] + [0] * n
        for j in range(1, n + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[n]


def _brand_min_distance(host: str) -> int:
    """Smallest edit distance from any host label to a known brand.

    0 = brand present exactly (could be the real site or a sub-domain trick);
    1-2 = classic typo-squat / look-alike (paypa1, arnazon); large = unrelated.
    """
    labels = [part for part in host.split(".") if part]
    best = 99
    for label in labels:
        for brand in BRANDS:
            best = min(best, _edit_distance(label, brand))
            if best == 0:
                return 0
    return best


def extract(url: str) -> dict:
    """Extract all URL string features. Returns a flat dict of numbers."""
    url = str(url).strip()
    try:                                    # some corpora contain malformed URLs
        parsed = urlparse(url if "//" in url else "http://" + url)
        host = (parsed.hostname or "").lower()
        path, query = parsed.path or "", parsed.query or ""
        scheme, port = parsed.scheme, parsed.port
    except ValueError:
        host, path, query, scheme, port = "", "", "", "", None
    labels = [part for part in host.split(".") if part]
    tld = labels[-1] if labels else ""
    core = labels[-2] if len(labels) >= 2 else ""
    brand_dist = _brand_min_distance(host)

    f = {
        # --- length / character counts (lexical) ---
        "url_len": len(url),
        "host_len": len(host),
        "path_len": len(path),
        "query_len": len(query),
        "n_dots": url.count("."),
        "n_hyphen": url.count("-"),
        "n_underscore": url.count("_"),
        "n_slash": url.count("/"),
        "n_at": url.count("@"),
        "n_qmark": url.count("?"),
        "n_equal": url.count("="),
        "n_amp": url.count("&"),
        "n_percent": url.count("%"),
        "n_digit": sum(c.isdigit() for c in url),
        "n_upper": sum(c.isupper() for c in url),
        "digit_ratio": sum(c.isdigit() for c in url) / max(len(url), 1),
        "letter_ratio": sum(c.isalpha() for c in url) / max(len(url), 1),
        # --- host / domain ---
        "n_subdomain": max(0, len(labels) - 2),
        "host_hyphen": host.count("-"),
        "is_ip": int(bool(_IP_RE.match(host)) or bool(_HEX_IP_RE.match(host))),
        "has_port": int(port is not None),
        "core_len": len(core),
        # --- TLD ---
        "tld_len": len(tld),
        "suspicious_tld": int(tld in SUSPICIOUS_TLDS),
        # --- path / query ---
        "n_path_segments": path.count("/"),
        "n_query_params": query.count("=") if query else 0,
        "has_query": int(bool(query)),
        "double_slash_path": int("//" in path),
        # --- entropy (randomness) ---
        "url_entropy": _entropy(url),
        "host_entropy": _entropy(host),
        "core_entropy": _entropy(core),
        # --- scheme / encoding tricks ---
        "is_https": int(scheme == "https"),
        "has_punycode": int("xn--" in host),
        "has_at_symbol": int("@" in url),
        "has_hex_encoding": int(bool(re.search(r"%[0-9a-fA-F]{2}", url))),
        # --- brand / cue signals ---
        "brand_min_dist": min(brand_dist, 20),
        "brand_lookalike": int(1 <= brand_dist <= 2),   # typo-squat band
        "brand_in_subdomain": int(any(b in ".".join(labels[:-2]) for b in BRANDS) if len(labels) > 2 else 0),
        "is_shortener": int(host in SHORTENERS),
        "n_cue_words": sum(w in url.lower() for w in CUE_WORDS),
    }
    return f


FEATURE_NAMES = list(extract("http://example.com").keys())


def extract_frame(urls):
    """Build a feature DataFrame from a list/Series of URLs.

    The comprehension is unavoidable: every feature comes from parsing an individual
    URL string, which pandas cannot vectorise.
    """
    return pd.DataFrame([extract(u) for u in urls], columns=FEATURE_NAMES)


if __name__ == "__main__":
    import json
    for u in ["https://www.google.com",
              "http://paypa1-secure.verify-account.tk/login.php?id=1",
              "http://192.168.0.1/webscr/confirm",
              "https://xn--pypal-4ve.com/"]:
        print(u)
        print(json.dumps(extract(u), indent=0)[:400], "\n")
    print(f"{len(FEATURE_NAMES)} features:", FEATURE_NAMES)
