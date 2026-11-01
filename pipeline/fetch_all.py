"""Refresh every source into data/snapshots/<UTC date>/. Keyless sources always run; keyed ones skip cleanly."""
import sys, traceback
from .common import snapshot_dir, save, utcnow
from . import fetch_nearblocks, fetch_rpc, fetch_fastnear, fetch_defillama, fetch_coingecko, fetch_nearstats, \
    fetch_revenue_dashboard, fetch_buybacks, fetch_dune

STEPS = [("nearblocks", fetch_nearblocks), ("rpc", fetch_rpc), ("fastnear", fetch_fastnear), ("defillama", fetch_defillama),
         ("coingecko", fetch_coingecko), ("nearstats", fetch_nearstats), ("revenue_dashboard", fetch_revenue_dashboard),
         ("buybacks", fetch_buybacks), ("dune", fetch_dune)]


def main():
    snap = snapshot_dir()
    print(f"snapshot -> {snap}")
    health = {}
    for name, mod in STEPS:
        print(f"[{name}]")
        try:
            mod.run(snap)
            health[name] = {"status": "ok", "at": utcnow()}
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            health[name] = {"status": "failed", "error": str(e), "at": utcnow()}
    save(snap, "source_health", health, "pipeline.fetch_all", "a failed source never overwrites an older file")
    failed = [k for k, v in health.items() if v["status"] == "failed"]
    print("failed:", failed or "none")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
