"""Test-time evasion attacks on URLs.

The attacker keeps the URL usable (it still resolves to their page) but changes its
*surface* so the classifier's features shift toward "legitimate". Attacks range from
cheap look-alike domains (defendable) to hosting the page on legitimate HTTPS
infrastructure (the honest ceiling for any URL-only detector).

For defensive evaluation only.

References: Boucher et al. 2022 (Bad Characters / imperceptible perturbations);
Le et al. 2018 (URLNet); Ma et al. 2009 (Beyond Blacklists); Unicode TR39 (confusables).
"""
from __future__ import annotations
import re
from urllib.parse import urlparse, urlunparse

# Latin -> Cyrillic/Greek look-alikes (the character-level domain-spoofing family).
CONFUSABLES = {
    "a": "а", "c": "с", "e": "е", "i": "і", "j": "ј", "o": "о", "p": "р",
    "s": "ѕ", "x": "х", "y": "у", "d": "ԁ", "h": "һ", "l": "ӏ", "n": "ո",
    "b": "ь", "g": "ɡ", "m": "м", "t": "т", "k": "к",
}
# Legitimate hosting services attackers abuse to inherit a trusted domain + HTTPS.
LEGIT_HOSTS = ["sites.google.com", "storage.googleapis.com", "s3.amazonaws.com",
               "web.app", "firebaseapp.com", "weebly.com", "blogspot.com",
               "azurewebsites.net", "netlify.app", "github.io"]
CUE_RE = re.compile(r"(login|signin|secure|account|verify|update|confirm|bank|webscr|"
                    r"password|credential|wallet|invoice|billing|suspend|unlock|recover)", re.I)


def _parts(url):
    return urlparse(url if "//" in str(url) else "http://" + str(url))


def attack_homoglyph(url, rng, rate=0.6):
    """Swap domain letters for identical-looking foreign characters (spoofed domain)."""
    p = _parts(url)
    host = "".join(CONFUSABLES.get(ch, ch) if (ch in CONFUSABLES and rng.random() < rate) else ch
                   for ch in (p.hostname or ""))
    return urlunparse(p._replace(netloc=host + (f":{p.port}" if p.port else "")))


def attack_typosquat(url, rng, **_):
    """Insert/duplicate a character in the registered domain label (paypa1 / paypall)."""
    p = _parts(url); host = p.hostname or ""
    labels = host.split(".")
    if len(labels) >= 2:
        core = list(labels[-2])
        if core:
            i = rng.integers(0, len(core)); core.insert(i, core[i])
            labels[-2] = "".join(core)
    return urlunparse(p._replace(netloc=".".join(labels)))


def attack_shortener(url, rng, **_):
    """Hide the destination behind a URL-shortener-style link."""
    slug = "".join(rng.choice(list("abcdefghijkmnpqrstuvwxyz23456789"), size=7))
    return f"https://bit.ly/{slug}"


def attack_https(url, rng=None, **_):
    """Cheapest real evasion: serve the same page over HTTPS (flips the biggest artifact).

    String-level swap so ONLY the scheme changes (nothing else is reformatted).
    """
    u = str(url)
    if u.startswith("http://"):
        return "https://" + u[len("http://"):]
    if "://" not in u:
        return "https://" + u
    return u


def attack_legit_host(url, rng, **_):
    """Host the phishing page on a legitimate HTTPS service (the strong attack).

    The path is kept but its cue words are stripped, so the URL looks like ordinary
    cloud-hosted content. This is what real phishing increasingly does.
    """
    p = _parts(url)
    host = str(rng.choice(LEGIT_HOSTS))
    slug = "".join(rng.choice(list("abcdefghijklmnopqrstuvwxyz0123456789"), size=8))
    path = CUE_RE.sub("page", p.path or "")
    if host in ("sites.google.com",):
        path = f"/view/{slug}"
    return urlunparse(("https", host, path or f"/{slug}", "", "", ""))


def attack_mimicry(url, rng, **_):
    """Homepage mimicry: HTTPS + a short, clean, bare domain with no path or cue words.

    Upper-bound illustration of the collection artifact: PhiUSIIL's legitimate URLs are
    clean HTTPS home-pages, so the closer a phishing URL is made to look like one, the
    less a URL-only detector sees. (Real phishing needs a path; the live OpenPhish test
    in the drift section is the honest real-world version of this.)
    """
    word = "".join(rng.choice(list("abcdefghijklmnopqrstuvwxyz"),
                              size=int(rng.integers(6, 12))))
    tld = str(rng.choice(["com", "org", "net", "io", "co"]))
    return f"https://www.{word}.{tld}"


ATTACKS = {
    "homoglyph": attack_homoglyph,
    "typosquat": attack_typosquat,
    "https_upgrade": attack_https,
    "homepage_mimicry": attack_mimicry,
}


def apply_attack(urls, kind, seed=0):
    """Apply one attack to a list/Series of URLs."""
    import numpy as np
    rng = np.random.default_rng(seed)
    fn = ATTACKS[kind]
    return [fn(u, rng) for u in urls]
