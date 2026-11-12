"""Shared helpers: HTTP with retries, dated snapshot directory, manifest with provenance."""
from __future__ import annotations
import hashlib, json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOTS = ROOT / "data" / "snapshots"
UA = {"User-Agent": "near-toll-road/0.1 (reproducible research; github.com/NoniWryts/near-toll-road)"}


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def snapshot_dir(date: str | None = None) -> Path:
    date = date or os.environ.get("SNAPSHOT_DATE") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    d = SNAPSHOTS / date
    d.mkdir(parents=True, exist_ok=True)
    return d


def latest_snapshot() -> Path:
    dirs = sorted(p for p in SNAPSHOTS.glob("20*") if p.is_dir())
    if not dirs:
        raise SystemExit("no snapshot found; run `make refresh`")
    return dirs[-1]


def get_json(url: str, params: dict | None = None, headers: dict | None = None, retries: int = 7, timeout: int = 60):
    h = dict(UA)
    if headers:
        h.update(headers)
    last = None
    for i in range(retries):
        try:
            r = requests.get(url, params=params, headers=h, timeout=timeout)
            if r.status_code == 429:
                last = "HTTP 429 rate limited"
                time.sleep(min(60, 2 ** i * 5))
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 ** i)
    raise RuntimeError(f"GET {url} failed after {retries} tries: {last}")


def post_json(url: str, payload: dict, retries: int = 4, timeout: int = 60):
    last = None
    for i in range(retries):
        try:
            r = requests.post(url, json=payload, headers=UA, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 ** i)
    raise RuntimeError(f"POST {url} failed after {retries} tries: {last}")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def save(snap: Path, name: str, obj, source: str, note: str = "", extra: dict | None = None) -> Path:
    """Write a DataFrame as parquet or a dict/list as JSON, and record provenance in manifest.json."""
    if isinstance(obj, pd.DataFrame):
        path = snap / f"{name}.parquet"
        obj.to_parquet(path, index=False)
        rows = len(obj)
    else:
        path = snap / f"{name}.json"
        path.write_text(json.dumps(obj, indent=1, default=str))
        rows = len(obj) if hasattr(obj, "__len__") else 1
    manifest_path = snap / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"snapshot": snap.name, "files": {}}
    manifest["files"][path.name] = {
        "source": source, "fetched_at": utcnow(), "rows": rows, "sha256": _sha256(path), "note": note, **(extra or {}),
    }
    manifest_path.write_text(json.dumps(manifest, indent=1))
    print(f"  saved {path.name:40s} rows={rows:<8} <- {source}")
    return path


def load_df(snap: Path, name: str) -> pd.DataFrame:
    return pd.read_parquet(snap / f"{name}.parquet")


def load_json(snap: Path, name: str):
    return json.loads((snap / f"{name}.json").read_text())


def yocto(x) -> float:
    return float(x) / 1e24


def log(msg: str):
    print(msg, file=sys.stderr)
