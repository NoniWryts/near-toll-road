"""Electric Capital Open Dev Data (CC BY 4.0): monthly-active developers per ecosystem.
Downloads the public manifest and the two ecosystem-level parquet files (~77 MB) from data.opendevdata.org,
then keeps only a peer set so the snapshot stays small. Raw files are cached under data/raw/opendevdata/ (gitignored).
Definitions (Electric Capital): all_devs = developers with >=1 commit in the trailing 28 days; exclusive_devs = active only
in this ecosystem; full_time_devs = >=10 active days in the trailing 84 days (contribution ranks)."""
import hashlib
from pathlib import Path
import pandas as pd
import requests
from .common import ROOT, get_json, save

BASE = "https://data.opendevdata.org"
PEERS = ["NEAR", "Ethereum", "Solana", "Bitcoin", "Base", "Arbitrum", "Polygon", "Sui", "Aptos", "Avalanche", "Cardano",
         "TON", "Internet Computer", "Polkadot", "Cosmos"]
RAW = ROOT / "data" / "raw" / "opendevdata"


def _download(path: str, version: str) -> Path:
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / version / Path(path).name
    if out.exists():
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(BASE + path, stream=True, timeout=600) as r:
        r.raise_for_status()
        tmp = out.with_suffix(".part")
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
        tmp.rename(out)
    return out


def run(snap):
    man = get_json(f"{BASE}/manifest.json")["dataset"]
    version = man["version"]
    res = {Path(r["path"]).name: r for r in man["resources"]}
    eco = pd.read_parquet(_download(res["ecosystems.parquet"]["path"], version))
    mads = pd.read_parquet(_download(res["eco_mads.parquet"]["path"], version), columns=[
        "ecosystem_id", "day", "all_devs", "exclusive_devs", "multichain_devs", "num_commits",
        "devs_0_1y", "devs_1_2y", "devs_2y_plus", "one_time_devs", "part_time_devs", "full_time_devs"])
    sel = eco[eco.name.isin(PEERS) & (eco.is_chain == 1)][["id", "name", "launch_date"]]
    df = mads[mads.ecosystem_id.isin(sel.id)].merge(sel.rename(columns={"id": "ecosystem_id", "name": "ecosystem"}), on="ecosystem_id")
    df["day"] = pd.to_datetime(df["day"])
    df = df.sort_values(["ecosystem", "day"]).reset_index(drop=True)
    save(snap, "opendevdata_mads", df, f"{BASE}/snapshots/{version}/eco_mads.parquet",
         "Electric Capital Open Dev Data, CC BY 4.0; peer set only; all_devs = >=1 commit in trailing 28 days",
         {"dataset_version": version, "dataset_created": man.get("created"), "peers": sorted(df.ecosystem.unique().tolist()),
          "license": "CC BY 4.0 (https://github.com/electric-capital/open-dev-data)",
          "b3sum_eco_mads": res["eco_mads.parquet"].get("b3sum")})
