"""revenue.near.org has no API. We keep the raw HTML and pull the embedded wallet table out of it so the
dashboard's own numbers can be compared with the chain. The page footer calls its figures 'illustrative'."""
import re, json
from .common import save
import requests
from .common import UA

URL = "https://revenue.near.org/"


def run(snap):
    html = requests.get(URL, headers=UA, timeout=60).text
    (snap / "revenue_near_org.html").write_text(html)
    wallets = []
    for m in re.finditer(r'\\"name\\":\\"([a-z0-9._-]+\.near)\\",\\"nearAmount\\":([0-9.]+),\\"share\\":([0-9.]+)', html):
        wallets.append({"wallet": m.group(1), "near_amount": float(m.group(2)), "share_pct": float(m.group(3))})
    kpis = {}
    for key in ("totalFees", "netRevenue", "captureRate", "confidentialTvl", "intentVolume", "cumulativeRevenue"):
        m = re.search(r'\\"%s\\":([0-9.]+)' % key, html)
        if m:
            kpis[key] = float(m.group(1))
    illustrative = "illustrative" in html.lower()
    save(snap, "revenue_dashboard", {"wallets": wallets, "kpis_found": kpis, "says_illustrative": illustrative},
         URL, "scraped from the page's embedded Next.js payload; wallet NEAR amounts as the dashboard shows them")
