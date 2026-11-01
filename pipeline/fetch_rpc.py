"""NEAR JSON-RPC: validator set and stake, protocol config (issuance cap), account state of the revenue wallets."""
from .common import post_json, save, yocto

RPC = "https://rpc.mainnet.fastnear.com"
ACCOUNTS = [
    "buybacks.multisignature.near",   # receives NEAR bought with Intents fees (revenue.near.org)
    "fefundsadmin.sputnik-dao.near",  # front-end fee funds (revenue.near.org)
    "1csfundsadmin.sputnik-dao.near", # 1Click service fee funds (revenue.near.org)
    "intents.near",                   # the NEAR Intents verifier contract
    "v1.signer",                      # Chain Signatures MPC contract
    "treasury.near",                  # protocol treasury (10% of issuance)
]


def rpc(method, params):
    return post_json(RPC, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})["result"]


def run(snap):
    v = rpc("validators", [None])
    rows = [{"account_id": x["account_id"], "stake_near": yocto(x["stake"]),
             "num_produced_blocks": x.get("num_produced_blocks"), "num_expected_blocks": x.get("num_expected_blocks")}
            for x in v["current_validators"]]
    import pandas as pd
    df = pd.DataFrame(rows).sort_values("stake_near", ascending=False).reset_index(drop=True)
    save(snap, "rpc_validators", df, f"{RPC} validators", f"epoch_start_height={v.get('epoch_start_height')}",
         {"epoch_start_height": v.get("epoch_start_height")})
    cfg = rpc("EXPERIMENTAL_protocol_config", {"finality": "final"})
    keep = {k: cfg.get(k) for k in ("protocol_version", "max_inflation_rate", "protocol_reward_rate",
                                     "num_blocks_per_year", "epoch_length", "protocol_treasury_account")}
    save(snap, "rpc_protocol_config", keep, f"{RPC} EXPERIMENTAL_protocol_config",
         "max_inflation_rate [1,40] = 2.5%/yr cap on total supply")
    accts = {}
    for a in ACCOUNTS:
        r = rpc("query", {"request_type": "view_account", "finality": "final", "account_id": a})
        accts[a] = {"amount_near": yocto(r["amount"]), "locked_near": yocto(r["locked"]),
                    "block_height": r["block_height"], "code_hash": r["code_hash"]}
    save(snap, "rpc_accounts", accts, f"{RPC} query view_account", "balances in NEAR; locked = staked directly")
    st = rpc("status", [])
    save(snap, "rpc_status", {"latest_block_height": st["sync_info"]["latest_block_height"],
                              "latest_block_time": st["sync_info"]["latest_block_time"],
                              "protocol_version": st.get("protocol_version")}, f"{RPC} status")
