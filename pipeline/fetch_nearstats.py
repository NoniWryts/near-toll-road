"""NearStats summary JSON: public vs confidential Intents split (confidential is a NEAR-reported residual)."""
from .common import get_json, save


def run(snap):
    d = get_json("https://nearstats.org/api/near/summary")
    save(snap, "nearstats_summary", d, "https://nearstats.org/api/near/summary",
         "secondary source; confidential volume = NEAR total minus observable public swaps")
