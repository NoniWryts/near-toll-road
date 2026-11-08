"""Volume-quality outputs are internally consistent when the samples are present."""
import json
import pandas as pd
from pipeline.common import ROOT

T = ROOT / "reports" / "tables"


def _k():
    return json.loads((T / "kpis.json").read_text())


def test_concentration_shares_are_ordered():
    k = _k()
    if "vq_dest_top1" not in k:
        return
    for p in ("vq_dest", "vq_signer", "vq_solver"):
        assert 0 <= k[f"{p}_top1"] <= k[f"{p}_top5"] <= k[f"{p}_top10"] <= k[f"{p}_top20"] <= 1
        assert 0 < k[f"{p}_hhi"] <= 10_000


def test_signer_kind_shares_sum_to_one():
    if not (T / "vq_signer_kinds.csv").exists():
        return
    assert abs(pd.read_csv(T / "vq_signer_kinds.csv").share_of_payout_usd.sum() - 1) < 1e-9


def test_block_mix_shares_and_scaling():
    if not (T / "block_mix.csv").exists():
        return
    b = pd.read_csv(T / "block_mix.csv")
    assert (b.share.between(0, 1)).all()
    assert (b.groupby("window").share.sum() <= 1 + 1e-9).all()
    assert ((b.share_p05 <= b.share + 1e-9) & (b.share <= b.share_p95 + 1e-9)).all()


def test_sample_is_seeded_and_recorded():
    m = json.loads(sorted((ROOT / "data" / "snapshots").glob("20*"))[-1].joinpath("manifest.json").read_text())["files"]
    if "intents_sample.parquet" not in m:
        return
    assert m["intents_sample.parquet"]["seed"] and m["intents_sample.parquet"]["pages_ok"] > 100
