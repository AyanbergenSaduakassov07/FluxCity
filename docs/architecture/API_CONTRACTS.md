# API Contracts (v1)

REST lives at `/api/v1`. It uses JSON, with pydantic models from `core/models.py`. TS types are generated (`scripts/gen_types.py`, from OpenAPI to `web/src/api/types.ts`). Errors use `application/problem+json` with `{type, title, status, code, detail}`. List endpoints take `?limit&cursor`.

## REST
| Method | Path | Body → Response |
|---|---|---|
| POST | /regions | `{name, country, bbox|polygon}` → Region |
| POST | /networks/import | `{region_id, bbox|polygon|osm_file_ref, options}` → Job |
| GET | /networks/{id} | RoadNetworkVersion |
| GET | /networks/{id}/geometry | binary edges (TrafficTwin `edges.bin` format) |
| GET | /networks/{id}/quality | QualityReport |
| GET | /networks/{id}/edges?q= | edge search (id or exact name) → candidates with geometry |
| POST | /demand | `{network_version_id, method, params, seed}` → Job |
| POST | /scenarios | `{region_id, name, network_v, demand_v, signal_config?, sim_config}` → Scenario |
| GET | /scenarios/{id}/versions | ScenarioVersion[] |
| POST | /scenarios/{id}/patches | `{parent_version_id, patch}` → Job → new ScenarioVersion |
| GET | /scenario-versions/{a}/diff/{b} | VersionDiff |
| POST | /runs | `{scenario_version_id, seed, mode}` → Run |
| GET | /runs/{id} | Run + RunResult (when completed) |
| POST | /runs/{id}/cancel | → Run |
| GET | /runs/{id}/timeseries?kpi= | rows (DuckDB over parquet) |
| GET | /runs/{id}/edges?t0&t1&metric= | edge bins (binary) |
| POST | /experiments | `{arms[], seeds[] | n_seeds, sim_config?}` → Experiment |
| GET | /experiments/{id}/comparison | Comparison |
| GET | /controllers | available ControllerSpec kinds and param schemas |
| POST | /optimization/studies | → OptimizationStudy (Job) |
| POST | /rl/policies | train → RLPolicy (Job) |
| POST | /copilot/sessions | → CopilotSession |
| POST | /copilot/sessions/{id}/messages | `{text}` → SSE stream of `{delta|tool_call|approval_required|final{answer, claims}}` |
| POST | /copilot/approvals/{tool_call_id} | `{decision: approve|reject, note}` |
| GET | /jobs/{id} | Job (progress) |
| GET | /reports/{experiment_id} | HTML report (rendered from records; no LLM HTML) |

## WebSocket `/ws/runs/{run_id}` (ADR-010)
| Server → client | Encoding | Content |
|---|---|---|
| `hello` | JSON | `{v:1, run_id, origin_lonlat, t, vtypes[], vid_table[], tls[{id, links, state}], speed}` |
| `frame` | binary | header `u8 v, u8 kind=1, u32 seq, f64 t, u32 n` + SoA `u32 idx[n], f32 dx[n], f32 dy[n], u16 ang[n], u16 spd[n], u8 type[n]` |
| `vid_add` | JSON | `{idx, id, type}` (new vehicles) |
| `tls` | JSON | `{t, changes[{id, state}]}` on change |
| `stats` | JSON, 1 Hz | `{t, running, waiting_backlog, arrived, teleports, collisions, mean_speed, halting}` |
| `event` | JSON | `{t, kind (teleport/collision/override/patch/incident), ...}` |
| `status` | JSON | `{state: running|paused|finished|failed, reason?}` |

| Client → server | Content |
|---|---|
| `control` | `{action: pause|resume|set_speed, value?}` |

There is no client-side state mutation over the WS. Patches go through REST and create a new version.

## Copilot tool schema (shape)
```json
{"name":"patch.close_edge","risk":"propose","input":{"scenario_version_id":"…","edge_ids":["…"]},
 "output":{"status":"pass|review_required|blocked","draft_patch_id":"…","evidence":{…}}}
```
