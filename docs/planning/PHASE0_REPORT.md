# FluxCity — Phase 0 Report (2026-11-24)

Status: **approved 2026-11-24** (ADR-001…014 accepted). No product code written yet.

## 1. Bottom line

1. **There is no single foundation worth forking.** TrafficTwin scored 4/10 and UrbanFlow AI 3/10 on code inspection. FlowState is the best fit by design but has **no license**. WebSUMO is EUPL-1.2 and is only a viewer.
2. **Recommendation: a new thin repo that harvests modules** from permissively licensed sources: TrafficTwin (Apache-2.0), agentsumo-mcp (MIT), sumo-rl (MIT), video-to-sumo-rl (MIT), demandify (MIT), plus SUMO's own tools (EPL-2.0, used as-is). The original engineering is the core that no upstream has: scenario versioning, the controller protocol with a safety supervisor, matched-demand comparison, live telemetry, and a grounded copilot.
3. **The SUMO stack is verified on the M5.** SUMO 1.28 installs from PyPI wheels (`eclipse-sumo`, `libsumo`), with no Homebrew and no `SUMO_HOME` setup. libsumo is **37× faster** than TraCI for per-step telemetry reads. An Astana network builds in 1.6 s.
4. **Every Astana result will be synthetic and uncalibrated.** No traffic counts exist, and the OSM extract has **0 `turn:lanes` tags**. Lane-to-turn assignment is therefore inferred. The UI and reports must label this everywhere.

## 2. Measured proof of concept (`discovery/poc-results/`)

| Test | Result |
|---|---|
| Install | `uv add eclipse-sumo==1.28.0 libsumo==1.28.0 sumo-rl`: arm64 wheel, works with no system SUMO |
| 3×3 grid, 2,400 veh/h, 3,600 s, headless `sumo` | 0.37 s wall, 57 MB RSS, all trips completed |
| Per-step loop reading every vehicle pos/angle/speed plus TLS states (3,776 steps, peak 75 veh) | TraCI 3.67 ms/step · **libsumo 0.098 ms/step** |
| sumo-rl single-intersection, libsumo, 200 steps | OK: obs dim 11, Discrete(2), info includes system waiting/stopped |
| Astana left bank, bbox 71.405–71.445 E, 51.115–51.135 N (Overpass, 2.1 MB) | netconvert 1.6 s, 68 MB. **604 edges, 316 junctions, 30 TLS, 82 km.** OSM: 284 `lanes`, 199 `maxspeed`, 389 signal nodes, 568 restriction refs (15 ignored), **0 `turn:lanes`** |
| Astana random demand 0.8 s period, 1 h, 5,400 s horizon | 4,500 inserted, 0 waiting, **7 teleports (yield)**, 1 emergency brake, mean timeLoss 86 s. 1.84 s wall, 80 MB |
| SUMO `osmGet.py` | **Hung >5 min.** A direct Overpass POST with timeout and mirror fallback took seconds → ADR-012 |

Implications:
- District scale (hundreds of junctions) is cheap on 16 GB.
- RL on 1–20 intersections is CPU-bound and runs locally.
- Live telemetry cost is dominated by serialization, not SUMO.

## 3. Critical assessment of the specification

### 3.1 Contradictions
| # | Conflict | Resolution |
|---|---|---|
| C1 | "Reuse a complete application first" vs "do not merge apps / avoid incompatible frameworks / preserve upstream functionality" | No candidate passes inspection (§4), so we harvest modules (ADR-001) |
| C2 | Webster is listed as a *controller* | Webster is an offline timing method. It produces a fixed-time plan via SUMO `tlsCycleAdaptation.py` (ADR-006) |
| C3 | The safety supervisor must gate *all* controllers | SUMO-native static/actuated/delay-based programs are already constraint-valid. The supervisor gates only externally commanded actions (max-pressure, RL, copilot edits) |
| C4 | RL actions "extend phase / adjust timing" vs the sumo-rl foundation | sumo-rl uses discrete next-green selection. MVP uses select-green-or-hold through the supervisor. Duration actions come later |
| C5 | Netedit for advanced edits vs immutable versioning | Netedit runs as an external round-trip: export plain XML, edit, re-import → new `RoadNetworkVersion` |
| C6 | Both `reuse-matrix.md` and `REUSE_MATRIX.md` (also license-inventory) | Single source: `docs/dependencies/REUSE_MATRIX.md` |
| C7 | "Generate all 22 prompts" vs "prompts only after audit" plus approval gate | Phase 1–2 prompts are full. Later prompts are specified as work packages and expanded just-in-time at each phase gate (`docs/orchestration/PROMPTS.md`) |

### 3.2 Missing requirements (now decided or flagged)
- **User model.** Single local user, no auth, for MVP. Bind to localhost. Auth is required before any hosted deploy (R7).
- **Astana data.** No counts, signal timings or travel times. The only calibrated path is a city with open counts. Calibration is tested on synthetic "truth" plus one open-data city (R2).
- **Copilot success metric.** A grounding eval set: ≥30 questions with known answers from fixed runs, 100% numeric claim traceability, 0 invented run IDs.
- **CRS.** Not needed: netconvert projects to auto-UTM (Astana 42N). Store lon/lat in API payloads.
- **Time and people budget.** Not stated. The plan assumes one person plus two agents, part-time. MVP is about 10–12 weeks of agent-assisted work.
- **Teleport policy.** Not stated → ADR-013.

### 3.3 Excessive for MVP (deferred, not deleted)
- MARL.
- Pareto / pymoo.
- OR-Tools, which has no real need: signal timing is box-constrained black-box optimization, and Optuna covers it.
- MLflow, since a run manifest plus SQLite is enough.
- Video calibration.
- Economic and weather models.
- Pedestrians and full PT. Buses are kept for bus-lane / priority scenarios.
- 3D, PMTiles, kepler.gl, Valhalla, OSRM, osmnx (netconvert covers routing and graph import).
- PostGIS, Docker as a dev requirement, LiteLLM (PydanticAI is already provider-independent).

That leaves 11 workspaces. MVP ships 6 views: Network, Simulation, Scenarios/Compare, Signals, Copilot, Reports. Demand, Optimization and RL start as panels.

## 4. Primary foundation comparison (source-verified; details in `docs/upstream/*.md`)

| | TrafficTwin | UrbanFlow AI | FlowState | WebSUMO |
|---|---|---|---|---|
| License | Apache-2.0 | Apache-2.0 | **none** | EUPL-1.2 |
| Size | 37k py + 4.9k ts | ~? (one 2.7k-line god class) | 20.8k | small |
| SUMO driving | CLI subprocess; TraCI only for events | TraCI, global single session (`clear()` on create) | libsumo | libsumo + NATS |
| Live streaming | none (post-run edge bins) | HTTP polling full state | WS JSON ≤20 Hz + Hermite interpolation | WS JSON ~10 Hz |
| Map | MapLibre + deck.gl | Leaflet (bbox only) + Three.js | Canvas2D, local metres | MapLibre + deck.gl |
| Global city support | **none**: Jeddah in 44 paths, UTM 37N in 4 files, prayer times | yes (bbox → OSM) | no | n/a |
| Controllers / RL | none; rule-based strategist | "AI" = **fixed-weight max-pressure heuristic, no training** | fixed / adaptive / PPO (branches not public) | none |
| Metrics honesty | teleports counted; ttt 300; no unfinished-trip KPI | teleports/unfinished not counted; ttt 45; empty trips file | teleports + collisions separate | events stream |
| Tests / CI | 313 tests, CI | 13 tests, no CI | some, seed test | none |
| Score | **4/10** | **3/10** | ref only | ref only |

Verdict: forking TrafficTwin would carry about 23k LOC of Jeddah synthetic-population, Gulf day-type and film code. Live sim, controllers, RL, copilot and patches would all still be new. Harvesting its generic modules is cheaper and cleaner. Details in ADR-001.

## 5. Apple Silicon and compute

| Component | Status on M5 / 16 GB |
|---|---|
| SUMO 1.28, libsumo, sumolib, tools | ✅ verified (PyPI wheel) |
| sumo-rl + Gymnasium | ✅ verified. SB3/PyTorch MPS not yet run; CPU is fine for MLP policies |
| netedit / sumo-gui | not in the wheel; needs a GUI build (Homebrew tap/app). Optional |
| osmium-tool | Homebrew; needed only for Geofabrik clipping (large regions) |
| Docker | installed, daemon not running; not needed for dev |
| Codex CLI 0.172 | ✅ logged in |

Budget guidance:
- Interactive sim ≤ 1 at a time.
- Batch workers = `cpu_count − 2`, each a separate process with its own libsumo instance.
- Each Astana-district run is about 80 MB.
- RL: single-intersection DQN at 1e5 steps is expected to take minutes on CPU. Measure in Phase 6.

## 6. Risk register

| ID | Risk | L | I | Mitigation |
|---|---|---|---|---|
| R1 | Synthetic demand presented as real Astana traffic | H | H | Provenance enum on every artifact; mandatory "SYNTHETIC — UNCALIBRATED" badge in UI and reports; copilot must state it |
| R2 | No calibration data for Astana | H | M | Calibration pipeline proven on synthetic truth + one open-count city; `CalibrationStatus` field |
| R3 | OSM lane/turn data inferred (0 `turn:lanes`) → wrong capacity | H | M | Network quality score + inspector shows inferred vs imported; manual correction patches |
| R4 | RL underperforms max-pressure | M | L | Accepted; negative results reported; held-out seeds |
| R5 | Copilot invents numbers | M | H | Claim verifier: every number in an answer must match a tool result value; eval set gate |
| R6 | License contamination (GPL/EUPL/unlicensed, RESCO nets in sumo-rl) | M | H | Reuse matrix is the gate; CI check forbids `nets/RESCO` and unlisted vendored dirs |
| R7 | Unauthenticated local API exposed | L | H | Bind 127.0.0.1; auth ADR before any deploy |
| R8 | Agents overwrite each other | M | M | Worktrees + ownership map + contracts owned by integrator |
| R9 | libsumo is one instance per process | H | M | One sim per worker process, never shared across requests (ADR-002) |
| R10 | Scope creep (spec lists ~60 features) | H | H | MVP cut in §3.3; phase gates |
| R11 | Overpass rate limits / outages | M | L | Raw-extract cache keyed by bbox hash; Geofabrik fallback |
| R12 | Teleports/gridlock distort comparisons | M | H | ADR-013 validity gates |

## 7. Astana demonstration strategy
1. **Synthetic 1×1 and 3×3 grids** (netgenerate, committed). These are the controller and metric verification fixtures.
2. **One real Astana intersection.** Chosen by network-quality score from the left-bank extract. Lanes and turns are manually corrected via patches.
3. **Corridor of 5–20 TLS.** The candidate is Mangilik El / Turan Ave on the left bank, since the PoC bbox already contains 30 TLS. The final pick comes from the Phase 2 quality report.
4. **District.** The PoC bbox (82 km), for closures, incidents and route alternatives.

Every demo is labelled synthetic. Citywide scale is out of MVP.
