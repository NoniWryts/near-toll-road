"""FastNear API: staking pools and token holdings of the revenue wallets (to test the 'staked or locked' claim)."""
from .common import get_json, save

BASE = "https://api.fastnear.com/v1/account"
WALLETS = ["buybacks.multisignature.near", "fefundsadmin.sputnik-dao.near", "1csfundsadmin.sputnik-dao.near"]


def run(snap):
    out = {}
    for w in WALLETS:
        out[w] = {"staking": get_json(f"{BASE}/{w}/staking"), "full": get_json(f"{BASE}/{w}/full")}
    save(snap, "fastnear_wallets", out, BASE, "staking pools (empty list = nothing delegated) and FT holdings")
