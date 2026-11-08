"""MPC network behind Chain Signatures: participants and signing threshold, read from v1.signer's `state` view."""
from .common import save
from .fetch_hos import view, RPC


def run(snap):
    s = view("v1.signer", "state", {})
    run_ = s.get("Running") or next(iter(s.values()))
    p = run_["parameters"]
    parts = p["participants"]["participants"]
    ids = [x[0] if isinstance(x, list) else x.get("account_id", x) for x in parts]
    out = {"state": next(iter(s.keys())), "threshold": p["threshold"], "participants": ids, "n_participants": len(ids),
           "keyset_epoch": run_.get("keyset", {}).get("epoch_id"),
           "domains": [{"id": d["id"], "protocol": d["protocol"], "purpose": d.get("purpose"), "reconstruction_threshold": d.get("reconstruction_threshold")}
                       for d in run_.get("domains", {}).get("domains", [])]}
    print(f"  v1.signer: {out['n_participants']} participants, threshold {out['threshold']}")
    save(snap, "mpc_state", out, f"{RPC} call_function v1.signer.state", "MPC participants and threshold at fetch time")
