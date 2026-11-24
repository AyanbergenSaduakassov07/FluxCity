# Domain Model

All IDs are ULIDs. Artifacts are referenced by `sha256`. Versioned entities are immutable once created. Pydantic models live in `backend/fluxcity/core/models.py`, which the integrator owns.

## Entities
| Entity | Key fields | Notes |
|---|---|---|
| `Region` | id, name, country, origin_lonlat, crs (auto-UTM) | A city or demo area, e.g. "Astana-LeftBank" |
| `NetworkSource` | id, region_id, kind (overpass/pbf/file/netgenerate), query or bbox/polygon, fetched_at, osm_timestamp, sha256 | Raw input provenance |
| `RoadNetworkVersion` | id, source_id, parent_id?, net_sha256, plain_xml_sha256, netconvert_args, sumo_version, quality_report, provenance | Immutable |
| `DemandVersion` | id, network_version_id, method (random/od/route_sampler/ga), params, seed, routes_sha256, period, provenance, calibration_status | |
| `SignalConfig` | id, network_version_id, programs_sha256 (additional tlLogic), source (netconvert/webster/greenwave/manual/optimized) | |
| `ControllerSpec` | kind (native_static/actuated/delay_based/max_pressure/queue/rl), params, policy_sha256?, tls_ids | One per TLS group |
| `SafetyConstraints` | per-TLS min/max green, yellow, all-red, conflict matrix hash | Derived from the net plus overrides |
| `SimConfig` | begin, end, warmup, step_length, time_to_teleport, drain, extra args (allow-listed) | |
| `Patch` | id, op (enum), params (typed per op), target ids, created_by (user/copilot), approved_by | |
| `ScenarioVersion` | id, scenario_id, parent_id?, network_v, demand_v, signal_config, controllers[], sim_config, patches[], content_hash | Content hash = hash of all refs |
| `Scenario` | id, region_id, name, description, head_version_id | Mutable pointer |
| `Run` | id, scenario_version_id, seed, mode (live/headless), status, job_id, started/ended, manifest_sha256 | |
| `RunManifest` | inputs{hashes}, sumo_version, fluxcity_sha, dirty, args, seeds, platform, wall_s | JSON artifact |
| `RunResult` | run_id, kpis{…}, validity{gates, passed}, artifacts{tripinfo.parquet, summary.parquet, edgedata.parquet, events.parquet, frames.parquet?} | |
| `Experiment` | id, arms[scenario_version_id], seeds[], sim_config override, status | |
| `Comparison` | id, experiment_id, baseline_arm, kpi_deltas[{kpi, mean, ci_lo, ci_hi, n, valid}] | Derived, recomputable |
| `OptimizationStudy` | id, scenario_version_id, search_space, objectives, seeds, n_trials, best_trial → ScenarioVersion | |
| `RLPolicy` | id, env_spec (obs, reward, action, tls_ids), algo, train_seeds, steps, checkpoint_sha256, eval_comparison_id | |
| `CopilotSession` | id, messages, tool_calls[], approvals[], claims[] | |
| `ToolCall` | id, tool, risk, input, output_ref, status (done/pending_approval/rejected/error) | |
| `Claim` | text_span, value, unit, source (tool_call_id + json path), verified | |
| `Job` | id, kind, payload, status, attempts, worker_pid, heartbeat, error | SQLite queue |

## Enums
- `Provenance`: `synthetic | osm_inferred | calibrated | observed`.
- `CalibrationStatus`: `none | partial(GEH%) | calibrated(GEH%, date)`.
- `PatchOp`: `close_edge | reduce_lanes | set_speed | add_bus_lane | set_tls_program | set_tls_offsets | scale_demand | add_incident | vehicle_mix | manual_edit`.
- `RunStatus`: `queued | running | completed | failed | cancelled | invalid`. `invalid` means the run completed but failed a validity gate.

## Invariants
1. A version's `content_hash` is equal to the hash of its referenced artifact hashes plus its params. Equal hash means the same experiment.
2. A run references exactly one `ScenarioVersion` and one seed.
3. A comparison only pairs runs that share a seed and a sim config.
4. Copilot `act` tool calls must have a non-null `approved_by` before execution.
