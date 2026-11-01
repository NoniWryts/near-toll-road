# Methodology

## Source hierarchy
1. On-chain records read directly: NEAR RPC (`validators`, `view_account`, `EXPERIMENTAL_protocol_config`), receipts of `buybacks.multisignature.near` via NearBlocks.
2. Reproducible public datasets with stated definitions: DefiLlama (NEAR Intents fees/revenue/volume adapter, chain fee adapters), NearBlocks daily series, CoinGecko.
3. Official dashboards and reports: revenue.near.org (scraped, labelled "illustrative" by its authors), NEAR Q2/Q3 updates, Nansen.
4. Media and social posts: used only as claims to test.

## Definitions
- **Intents volume**: USD notional of settled swaps, DefiLlama `dexs/near-intents`. Includes confidential volume as NEAR reports it.
- **Gross fees**: protocol fee plus the affiliate (distribution) fee on each swap, summed across integrators (DefiLlama `fees/near-intents`).
- **Captured revenue**: NEAR or wNEAR swept into NEAR's three revenue wallets (`fefundsadmin.sputnik-dao.near`, `buybacks.multisignature.near`, `1csfundsadmin.sputnik-dao.near`). Recognised when swept, so daily revenue can exceed daily fees; compare monthly.
- **Capture rate**: captured revenue / gross fees over the same window.
- **Buybacks**: successful `TRANSFER` receipts from `intents.near` to `buybacks.multisignature.near`. USD value = NEAR x CoinGecko daily close on that day.
- **Issuance**: day-over-day change in total supply (NearBlocks `total_supply`), which already nets out gas burn. Annualised rate = 30-day sum x 365/30 / total supply.
- **Coverage**: NEAR bought / NEAR issued over the same window. Price-free. Says nothing about burning.
- **Breakeven volume**: issuance value per day / (fee rate x capture rate x deployment share).
- **Chain Signatures calls**: receipts to `v1.signer` with method `sign`, from a time-boxed sample of the newest N pages of NearBlocks transactions; calls/day = sample count / sample span. Extrapolated and labelled as such.
- **Cross-protocol rank**: NEAR Intents' DefiLlama 30-day volume inserted into DefiLlama's bridge-aggregator and swap-aggregator lists and ranked; DefiLlama itself files Intents under its DEX overview, category Bridge.
- **Developers**: Electric Capital Open Dev Data. `all_devs` = developers with at least one public commit in the trailing 28 days in repos mapped to the ecosystem; `full_time_devs` = at least 10 active days in the trailing 84 days; `exclusive_devs` = active only in this ecosystem.
- **Staking ratio**: sum of current validator stake / total supply (RPC). Nakamoto coefficient: smallest number of validators holding more than one third of stake.

## Known gaps
- Sender-level Intents data (concentration, repeat use) needs the Explorer API partner token; not in this snapshot.
- Confidential shard state is not publicly observable.
- NEAR AI staking has no published pool account.
- Developer data covers public GitHub only.
- DefiLlama's canonical-bridge volumes (Across, Stargate, Wormhole) are behind a paid endpoint, so the cross-protocol table compares aggregators, not every bridge.
- Dune's official queries are fetched only when `DUNE_API_KEY` is set.
