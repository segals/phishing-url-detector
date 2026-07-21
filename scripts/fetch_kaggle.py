"""Fetch the Kaggle 'Malicious URLs Dataset' (sid321axn) for the cross-dataset test.

651,191 URLs, classes benign/defacement/phishing/malware. Siddhartha, M. (2021), Kaggle.
An independent, mixed-class source (different from PhiUSIIL) -> a confound-free
generalization test. Uses the new Kaggle Bearer token at ~/.kaggle/access_token.
"""
import os, ssl, urllib.request, zipfile

OUT = "data/raw/malicious_urls"
os.makedirs(OUT, exist_ok=True)
tok = open(os.path.expanduser("~/.kaggle/access_token")).read().strip()
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
url = "https://www.kaggle.com/api/v1/datasets/download/sid321axn/malicious-urls-dataset"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}",
                                           "User-Agent": "Mozilla/5.0"})
data = urllib.request.urlopen(req, context=ctx, timeout=180).read()
zp = os.path.join(OUT, "_mal.zip")
open(zp, "wb").write(data)
with zipfile.ZipFile(zp) as z:
    z.extractall(OUT)
os.remove(zp)
print(f"saved {OUT}/malicious_phish.csv ({len(data)/1e6:.1f} MB)")
