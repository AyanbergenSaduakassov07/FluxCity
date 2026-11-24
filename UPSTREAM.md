# Upstream sources

Each audited upstream is listed here at its pinned commit. When any file is extracted, add a row under "Extracted files" in the same PR.

## Audited (Phase 0, 2026-11-24)
| Repo | Commit | License | Verdict |
|---|---|---|---|
| TrafficTwin | 53a0d4ea | Apache-2.0 | **fork base** (ADR-001 rev. 2026-11-24) |
| UrbanFlow-AI | 98e8edb1 | Apache-2.0 | extract import pieces |
| agentsumo-mcp (PyPI sdist) | 0.1.3 | MIT | extract tool logic |
| kra35-prismx-agentsumo | 22798bfa | MIT | reject |
| ASTRA-SUMO | 946468b4 | MIT | extract patterns, GEH |
| demandify | fc801a15 | MIT | optional dep / extract |
| video-to-sumo-rl | d9c28dbe | MIT | extract GEH, demandlib |
| sumo-rl | 86f0fc41 | MIT | dependency |
| websumo | 5bad2df1 | EUPL-1.2 | reference only |
| open_controller | 445fc45c | EUPL-1.2 | reference only |
| RESCO | f1ed9a17 | GPL-3.0 | reference only |
| sumolights | 62a4f4ce | GPL-3.0 | reference only |
| flow_state | c57700d1 | none | reference only |
| LibSignal | 127af9f9 | none | reject |
| smart-traffic-rl | 2392dfed | none | reject |
| sumo-traffic-network-builder | e2bfe84e | none | reject |

## Fork base
The repository is a modified fork of TrafficTwin@53a0d4ea (Apache-2.0). All Python under `api/`, `sim/`, `strategist/`, `scripts/` (except `check_licenses.py`, `make_fixtures.py`), `tests/` and the `web/` app originate there; the upstream NOTICE is kept in `NOTICE`. Removed at fork time: films (`movies/`, `scripts/movies/`, `web/src/cinema/`), the docs site and upstream agent configs.

## Extracted files
| FluxCity path | Upstream repo@commit:path | License | Changes |
|---|---|---|---|
| — | — | — | (none yet) |
