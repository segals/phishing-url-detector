"""Cache a modern, independent test set (used for cross-dataset + temporal-drift):
 - phishing: OpenPhish community feed (recent, real).  https://openphish.com
 - legitimate: Majestic Million top domains (reputable ranking).  https://majestic.com
Both are public, no login.
"""
import os, ssl, io, urllib.request, pandas as pd
os.makedirs("data/raw", exist_ok=True)
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
def get(url):
    req=urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    return urllib.request.urlopen(req, context=ctx, timeout=60).read()

# phishing (live)
ph = get("https://openphish.com/feed.txt").decode("utf8","ignore").splitlines()
ph = [u.strip() for u in ph if u.strip().startswith("http")]
pd.DataFrame({"URL": ph, "label": 1}).to_csv("data/raw/openphish.csv", index=False)
print("openphish:", len(ph), "phishing URLs")

# legitimate (top-ranked domains -> https homepage URLs)
maj = get("https://downloads.majestic.com/majestic_million.csv").decode("utf8","ignore")
m = pd.read_csv(io.StringIO(maj)).head(100000)
legit = ["https://" + d for d in m["Domain"].astype(str)]
pd.DataFrame({"URL": legit, "label": 0}).to_csv("data/raw/majestic_top.csv", index=False)
print("majestic:", len(legit), "legit domains cached")
