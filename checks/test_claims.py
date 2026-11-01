import pandas as pd
from pipeline.common import ROOT

LEDGER = ROOT / "thesis" / "claims_ledger.csv"


def test_ledger_exists_and_is_complete():
    df = pd.read_csv(LEDGER)
    assert len(df) >= 16
    assert set(df.status) <= {"PASS", "FAIL", "PARTIAL", "UNVERIFIABLE"}
    assert df.evidence.notna().all() and df.observed.notna().all()


def test_buybacks_observed_on_chain():
    df = pd.read_csv(LEDGER).set_index("claim_id")
    assert df.loc["C01", "status"] == "PASS"


def test_bought_near_is_not_staked_or_locked():
    # This is a red row by design: the claim in the tokenomics post is not what the wallet shows.
    df = pd.read_csv(LEDGER).set_index("claim_id")
    assert df.loc["C02", "status"] == "FAIL"


def test_unverifiable_rows_have_no_fabricated_values():
    df = pd.read_csv(LEDGER)
    u = df[df.status == "UNVERIFIABLE"]
    assert (u.evidence == "none").all()
