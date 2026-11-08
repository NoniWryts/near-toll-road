"""1Click token list (keyless): asset id, decimals and a current USD price per Intents asset. Used to value sampled
intents. Prices are as of fetch time, not as of each transaction; shares and concentration use one common price scale."""
import pandas as pd
from .common import get_json, save

URL = "https://1click.chaindefuser.com/v0/tokens"


def run(snap):
    d = pd.DataFrame(get_json(URL))
    save(snap, "oneclick_tokens", d, URL, "asset ids, decimals and spot USD prices at fetch time")
