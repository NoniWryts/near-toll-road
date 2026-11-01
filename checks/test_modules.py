"""The optional modules (Chain Signatures, developers, cross-protocol) must agree with their KPIs when present."""
import json
import pandas as pd
from pipeline.common import ROOT

T = ROOT / "reports" / "tables"


def test_developer_table_matches_kpis():
    k = json.loads((T / "kpis.json").read_text())
    if "dev_all" not in k:
        return
    peers = pd.read_csv(T / "devs_peers.csv").set_index("ecosystem")
    assert int(peers.loc["NEAR", "all_devs"]) == k["dev_all"]
    assert peers.all_devs.is_monotonic_decreasing  # ranked table
    assert k["dev_full_time"] <= k["dev_all"] and k["dev_exclusive"] <= k["dev_all"]


def test_cross_protocol_rank_is_consistent():
    k = json.loads((T / "kpis.json").read_text())
    if "xp_bridge_rank" not in k:
        return
    ag = pd.read_csv(T / "aggregators.csv")
    br = ag[ag.llama_category == "bridge_aggregator"]
    me = br[br.displayName.str.startswith("NEAR Intents")].iloc[0]
    assert int(me.rank_30d) == k["xp_bridge_rank"]
    assert abs(br.share_of_list_30d.sum() - 1) < 1e-6
    assert (br.total30d.diff().dropna() <= 0).all()
