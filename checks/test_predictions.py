"""Pre-registration integrity: the predictions file is frozen, and the settler covers every call in it."""
import hashlib
import pandas as pd
from pipeline.common import ROOT


def test_predictions_file_is_frozen():
    body = (ROOT / "thesis" / "PREDICTIONS.md").read_bytes()
    assert hashlib.sha256(body).hexdigest() == (ROOT / "thesis" / "PREDICTIONS.sha256").read_text().strip()


def test_every_prediction_is_settled_or_pending():
    df = pd.read_csv(ROOT / "reports" / "tables" / "predictions.csv")
    assert list(df.id) == ["P1", "P2", "P3"]
    assert df.status.str.match(r"^(HIT|MISS|PENDING)").all()
