"""Optional: NEAR public BigQuery dataset. Runs sql/*.sql when GOOGLE_CLOUD_PROJECT is set, otherwise skips cleanly.
Each query takes an @end_date parameter and filters on block_date (the partition column)."""
import os
from datetime import date
from pathlib import Path
import pandas as pd
from .common import ROOT, save

SQL = ROOT / "sql"
DATASET = "bigquery-public-data.crypto_near_mainnet_us"


def run(snap):
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        print("  skipped: set GOOGLE_CLOUD_PROJECT (and gcloud application-default credentials) to run sql/*.sql")
        return
    from google.cloud import bigquery  # imported lazily so the keyless path has no GCP dependency
    client = bigquery.Client(project=project)
    end = os.environ.get("BQ_END_DATE", str(date.today()))
    cfg = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("end_date", "DATE", end)])
    for f in sorted(SQL.glob("*.sql")):
        job = client.query(f.read_text(), job_config=cfg)
        df = job.result().to_dataframe()
        meta = {"end_date": end, "bytes_processed": job.total_bytes_processed, "query_file": f"sql/{f.name}"}
        if "block_date" in df.columns and len(df):
            meta["max_block_date"] = str(pd.to_datetime(df.block_date).max().date())
        save(snap, f"bq_{f.stem}", df, DATASET, f"BigQuery public dataset via sql/{f.name}", meta)
