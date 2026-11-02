# Submission checklist (against nearhackathon.com/HACKATHON.md, read 2026-11-01)

Re-read the live rules file before submitting; dates and rules may change.

| Requirement | Status | Where |
| --- | --- | --- |
| Build window 2026-11-01 to 2026-11-14T23:59Z | in window; first commit 2026-11-01 | `git log` |
| Public repository by the deadline | **not yet public**; Daniel decides when | this repo |
| README a machine reader can follow, "do X, see Y", no marketing | done | `README.md` |
| LICENSE file | MIT | `LICENSE` |
| No secrets in the repo | `.env.example` only; keys via env vars | `.gitignore`, `.env.example` |
| Track ids | `thesis` (primary). Others do not fit | submission `tracks` |
| Demo post on X with video or screenshots, "built at NEAR HACKATHON", tags @NEARProtocol #NEARHackathon | **Daniel records and posts**; draft in `docs/DEMO.md` | |
| Hosted demo (a plus, keep up to 2026-11-18, ideally 11-25) | `dashboard/` is static; enable GitHub Pages on the repo once public | |
| Second project disclosure (Q-015: one person, at most 2 projects, each README names the other) | this README names Clearance; Clearance's README must name Toll Road | `README.md` "Other entries" |
| NEAR mainnet account for payout | **Daniel provides**; never invented | submission `nearAddress` |
| Team lead name, email, team size | **Daniel provides** | submission |
| Submit once, POST only after Daniel confirms the exact payload | not sent | `docs/SUBMISSION.md` payload below |

## Payload draft (fill the bracketed fields; nothing is sent until confirmed)

```json
{"requestId":"<uuid4>","projectName":"Toll Road: does NEAR's fee switch pay for the chain?","leadName":"<lead>","email":"<email>","size":"1","tracks":["thesis"],"nearAddress":"<account.near>","projectUrl":"<public repo url>","demoUrl":"<x post url>","idea":"An evidence-first investment thesis for NEAR built as a re-runnable repo. It measures the NEAR Intents fee switch end to end on-chain (volume, fees, captured revenue, NEAR bought back vs NEAR issued), models the breakeven volume under current and HSP-029 issuance, ranks Intents against every DefiLlama aggregator, adds Chain Signatures usage and Electric Capital developer data, and re-tests 19 public claims in a ledger with PASS/PARTIAL/UNVERIFIABLE/FAIL. One command rebuilds every table, chart and the thesis text from a dated snapshot.","consent":true}
```

## Before sending
1. `make refresh && make report && make check` on the day of submission so the snapshot is fresh.
2. HSP-029 result is in (`params.yaml`, ledger C20); `make refresh` re-reads `vote.dao` so the status moves from Timelock when it executes.
3. Make the repo public, enable GitHub Pages from `dashboard/`, confirm the pages open logged out.
4. Daniel posts the demo on X and pastes the link.
5. Print the payload, get a yes, send once.
