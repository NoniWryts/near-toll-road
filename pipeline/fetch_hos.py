"""House of Stake: read HSP proposals straight from the voting contract (vote.dao) over RPC. Keyless, on-chain."""
import base64, json
from .common import post_json, save, utcnow

RPC = "https://rpc.mainnet.fastnear.com"
VOTING = "vote.dao"
PROPOSALS = [29]  # HSP-029 issuance ramp 2.5% -> 1.6%


def view(contract, method, args):
    r = post_json(RPC, {"jsonrpc": "2.0", "id": "1", "method": "query", "params": {
        "request_type": "call_function", "finality": "final", "account_id": contract, "method_name": method,
        "args_base64": base64.b64encode(json.dumps(args).encode()).decode()}})
    return json.loads(bytes(r["result"]["result"]))


def run(snap):
    out = {}
    for pid in PROPOSALS:
        p = view(VOTING, "get_proposal", {"proposal_id": pid})
        y = 1e24
        votes = p["votes"]  # index 0 = for, 1 = against, 2 = abstain (contract convention, matches the app)
        snap_ve = float(p["snapshot_and_state"]["total_venear"]) / y
        f, a, ab = (float(v["total_venear"]) / y for v in votes)
        rec = {"id": pid, "title": p["title"], "status": p["status"], "proposer_id": p["proposer_id"],
               "voting_start": int(p["voting_start_time_ns"]) / 1e9, "voting_duration_days": int(p["voting_duration_ns"]) / 86400e9,
               "timelock_days": int(p["timelock_duration_ns"]) / 86400e9, "snapshot_block": p["snapshot_and_state"]["snapshot"]["block_height"],
               "snapshot_total_venear": snap_ve, "for_venear": f, "against_venear": a, "abstain_venear": ab,
               "for_votes": votes[0]["total_votes"], "against_votes": votes[1]["total_votes"], "abstain_votes": votes[2]["total_votes"],
               "turnout": (f + a + ab) / snap_ve, "approval_for_over_for_plus_against": f / (f + a) if f + a else None,
               "quorum_threshold_bps": p["quorum_threshold_bps"], "approval_threshold_bps": p["approval_threshold_bps"],
               "description_head": p["description"][:600], "fetched_at": utcnow()}
        out[str(pid)] = rec
        print(f"  HSP-{pid:03d}: status={rec['status']} for={f:,.0f} against={a:,.0f} abstain={ab:,.0f} veNEAR, turnout {rec['turnout']:.1%}")
    save(snap, "hos_proposals", out, f"{RPC} call_function {VOTING}.get_proposal", "House of Stake voting contract state, read at fetch time")
