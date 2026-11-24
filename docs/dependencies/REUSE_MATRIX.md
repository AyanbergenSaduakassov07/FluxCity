# Reuse Matrix and License Inventory (single source of truth)

**Method key**
- **dep**: package dependency.
- **wrap**: call it behind our typed interface.
- **extract**: copy and adapt, keeping the header and adding an `UPSTREAM.md` entry.
- **ref**: concepts only, no code.
- **reject**: not used.

Upstream commits are pinned in `UPSTREAM.md`. Audit evidence is in `docs/upstream/*.md`.

## 1. Feature → upstream
| Feature | Source | File(s) | Method | License | Phase |
|---|---|---|---|---|---|
| Traffic engine | Eclipse SUMO 1.28 | PyPI `eclipse-sumo`, `libsumo`, `sumolib` | dep | EPL-2.0 | 1 |
| OSM fetch (multi-mirror) | UrbanFlow-AI | `server/app/simulation/sumo_scenario.py:323-376`, `osm/client.py` | extract | Apache-2.0 | 2 |
| netconvert flags + TLS retry ladder + `repair_unknown_tls_references` | UrbanFlow-AI | `sumo_scenario.py:379-618` | extract | Apache-2.0 | 2 |
| OSM→net pipeline, district polygons | TrafficTwin | `sim/network/build_city.py`, `geo.py` | extract + parametrize | Apache-2.0 | 2 |
| Run registry (traversal-safe, nested runs) + output contract | TrafficTwin | `api/runs.py`, `docs/contracts/run-outputs.md` | extract | Apache-2.0 | 1 |
| Stats/tripinfo → parquet, teleports, emissions | TrafficTwin | `sim/metrics.py`, `sim/runner.py` (stats parsing) | extract | Apache-2.0 | 1 |
| deck.gl edge-bin timeline, binary geometry, diff mode | TrafficTwin | `web/src/engine.ts`, `binCache.ts`, Timeline, color/legend | extract | Apache-2.0 | 2–3 |
| Scenario patch + diff report pattern | TrafficTwin | `sim/policies/transforms.py`, `report.py`, `sweep.py` | ref | Apache-2.0 | 3 |
| Fork-state / evaluate / rank / approve log | TrafficTwin | `strategist/*` | ref | Apache-2.0 | 7 |
| Calibration: routeSampler + GEH | TrafficTwin | `sim/calibrate.py`, `sim/adapters/counts.py` | extract | Apache-2.0 | 5 |
| Road closure patch | agentsumo-mcp 0.1.3 | `edge_edit` (main.py tool 6) | extract | MIT | 3 |
| Lane reduction (touched-node rebuild) | agentsumo-mcp | `reduce_lanes` (tool 7) | extract + fix lane choice / ID validation | MIT | 3 |
| Speed limit, vehicle mix, flow generation | agentsumo-mcp | tools 8, 12, 10 | extract | MIT | 3 |
| TLS offset / cycle adaptation wrappers | agentsumo-mcp → SUMO `tlsCoordinator.py`, `tlsCycleAdaptation.py` | tools 13, 14 | wrap | MIT / EPL-2.0 | 4 |
| Results → SQLite schema | agentsumo-mcp | `xml_to_sqlite` (tool 15) | extract (+ run_id, patch hash) | MIT | 7 |
| Network summary, OD validation, route compare, road-name→edges | agentsumo-mcp | tools 17, 11, 18, 24–25 | extract | MIT | 7 |
| Tool result envelope, annotations, `pass/review_required/blocked` | ASTRA-SUMO | `mcp_contract_tools.py`, `server.py`, `claim_tiers.py` | extract pattern | MIT | 7 |
| GEH / MAE / RMSE / bias | ASTRA-SUMO | detector_demand `geh_value`, `summarize_comparison` (~40 LOC) | extract | MIT | 5 |
| GEH per movement per interval; counts→routes, largest-remainder | video-to-sumo-rl | `release_v2/code/tools/twin_geh.py`, `demandlib.py` | extract | MIT | 5 |
| GA demand calibration (speed objective) | demandify | `calibration/optimizer.py`, `worker.py`, `objective.py` | dep (pinned) or extract; add count/GEH objective | MIT | 5 (optional) |
| Offline data bundles, cache keys, exporter | demandify | `offline_data.py`, `cache/keys.py`, `export/exporter.py` | extract | MIT | 5 |
| RL env (Gymnasium/PettingZoo), obs/reward registry | sumo-rl | `environment/env.py`, `traffic_signal.py`, `observations.py` | dep + subclass | MIT | 6 |
| DQN / PPO training scripts | sumo-rl | `experiments/dqn_*.py`, `ppo_4x4grid.py`, `sb3_grid4x4.py` | extract (examples) | MIT | 6 |
| RL algorithms | Stable-Baselines3 | — | dep | MIT | 6 |
| Optimization | Optuna | — | dep | MIT | 6 |
| Map rendering | deck.gl, MapLibre GL JS | — | dep | MIT, BSD-3 | 2 |
| Telemetry playout buffer, channel split, seed test | flow_state | `frontend/src/lib/*`, `backend/flowstate/api/*` | **ref** (unlicensed) | none | 2 |
| Versioned WS protocol | websumo | — | **ref** | EUPL-1.2 | 2 |
| Intergreen / conflict-group supervisor concepts | open_controller | `services/control_engine/src/signal_group_controller.py` | **ref** | EUPL-1.2 | 4 |
| Classical controllers (max-pressure, Webster, SOTL) | sumolights, RESCO, LibSignal, smart-traffic-rl | various | **ref** → reimplement from papers | GPL-3 / none | 4 |
| Webster | SUMO `tools/tlsCycleAdaptation.py` | — | wrap (subprocess) | EPL-2.0 | 4 |
| Native actuated / delay_based TLS | SUMO | tlLogic `type` | dep | EPL-2.0 | 4 |

## 2. Rejected
| Item | Reason |
|---|---|
| UrbanFlow session store, `sumo_engine.py`, training "registry", polling API, metrics | global state, no learning, no teleport counting |
| kra35 agent loop, web UI, prompts | path traversal, raw SQL, filesystem MCP, no approval gate |
| agentsumo `simulation_report` (HTML), `visualize_*`, `web_search`, Nominatim geocode | XSS, matplotlib PNGs, injection vector, silent all-edges fallback |
| RESCO nets bundled in sumo-rl | CC BY-NC-* |
| LibSignal, smart-traffic-rl, sumo-traffic-network-builder | no license |
| video-to-sumo-rl `stage1_track.py` | ultralytics AGPL |
| TrafficTwin population/day-type/events/film code | Jeddah-specific |

## 3. License inventory (dependencies planned for MVP)
| Package | License | Use |
|---|---|---|
| eclipse-sumo, libsumo, sumolib | EPL-2.0 (+GPL-2.0-or-later secondary) | runtime |
| fastapi, starlette, pydantic, uvicorn | MIT / BSD-3 | backend |
| numpy, pandas, pyarrow, duckdb | BSD-3 / Apache-2.0 / MIT | data |
| sumo-rl, gymnasium, pettingzoo, stable-baselines3, torch | MIT / MIT / MIT / MIT / BSD-3 | RL |
| optuna | MIT | optimization |
| hypothesis, pytest | MPL-2.0 / MIT | tests only |
| openai SDK (OpenAI-compatible client for Gemini / OpenRouter) | Apache-2.0 | copilot |
| react, vite, zustand, @tanstack/react-query | MIT | web |
| deck.gl, maplibre-gl | MIT / BSD-3 | web |
| OSM data | ODbL-1.0 | attribution required |

To verify at install: run `uv pip licenses` (or `pip-licenses`) and `license-checker` for the web app in CI (ADR-014).
