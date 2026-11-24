# UrbanFlow-AI audit (commit 98e8edb1, Apache-2.0)

Verdict: foundation suitability 3/10. Good OSM->SUMO plumbing and a 3D viz; the "AI" is a hand-tuned heuristic, single-session, polling-only, 1 smoke-level test suite.

## 1. Architecture
| Dir | LOC (py/ts/tsx/js/css) | Notes |
|---|---|---|
| server/app | ~8.2k py | FastAPI + pydantic-settings; sumo_engine.py 2690, sumo_scenario.py 994, osm/normalizer.py 1485, training_jobs.py 564 |
| web/src | ~6.2k ts/tsx/css | React 19 + Vite 7 + react-three-fiber/drei + three 0.170; leaflet/react-leaflet only in MapSelector.tsx (bbox pick). City view = Three.js (scene/CityScene.tsx 1989) |
| ai/urbanflow_ai | ~1.5k py (+1.5k notebook generator) | env/, models/, training/, integration/ |
| tests | 259 | 11 pytest funcs (tests/server), 1 vitest file with 2 util tests |
- SUMO driving: TraCI (not libsumo): `traci.start(...)`, `traci.getConnection(label)` sumo_engine.py:402-425; step-length 1, `--ignore-route-errors`. traci is NOT in pyproject; found by appending `$SUMO_HOME/tools` to sys.path (sumo_scenario.py:39-66).
- Sessions: `SimulationSessionStore` (session_store.py) in-memory dict, but `create()` calls `self.clear()` -> effectively ONE session at a time; RLock; every request blocks on engine lock.
- Storage: flat files under data/{osm,sessions,runs,models}; no DB. Training job/model registry = in-memory dicts + JSON files.
- Streaming: none. Frontend POSTs `/simulation/{id}/step {steps}` and receives full SimulationStateDto each time (App.tsx:284); training polled by setInterval GET. No WebSocket/SSE (grep: zero hits).

## 2. The "UrbanFlow AI controller" (CRITICAL)
Hand-written pressure heuristic with fixed weights. NOT a neural net, NOT tabular Q, NO learning.
- ai/urbanflow_ai/env/actions.py:157-165 `phase_pressure` = weighted sum (halted*3.0 + vehicles*1.0 + wait*0.04 + occupancy*1.6 + low_speed*0.65 + emergency*7.0); `best_green_phase` = argmax (l.141-154); switch if candidate >= current + switch_margin(4.0) or max_green timeout (l.71-97). Applied via `trafficlight.setPhase` + `setPhaseDuration` (l.121-130).
- Weights are `@dataclass(frozen=True)` constants, config.py:27-35. `policy.update_score()` (models/policy.py:32-39) only counts steps and tracks best_reward. Nothing ever mutates PolicyWeights.
- "Training" = training/train_tls.py:31-64: runs the same controller over a vehicle-count curriculum and calls `save_checkpoint` whenever instantaneous reward is a new max. The saved JSON is the same default weights + metadata. No gradient, no perturbation, no search, no eval/holdout. The CLI itself says "needs a live TraCI connection" (l.82-85).
- Dependencies: pyproject lists no torch/numpy/gym/sklearn. grep for backward/optimizer/epsilon/learning_rate: zero hits.
- "Model registry" = JSON files in data/models + in-memory `_models` dict in training_jobs.py (l.305-338, 418-429); "onnx"/"torchscript" formats declared in schemas/training.py:8 but only checkpoint/pickle accepted (training_jobs.py:358). Pickle export writes (pickle.dumps) only; load path uses JSON. Committed run history carries the author's abs paths (/Users/andrey/...).
- Reward (config.py:16-24, env/rewards.py) is a hand-weighted sum, evaluated on the controller's own steps.
=> Claim "AI" = false for any ML sense; it is a max-pressure-like adaptive controller. Reusable as a baseline controller only.

## 3. Features
| Feature | Status | Evidence |
|---|---|---|
| Worldwide bbox | Yes, lat/lon validated only; no max-area cap | schemas/osm.py:3-16; MapSelector.tsx (Leaflet rect) |
| OSM fetch | Overpass, 4 mirror failover, 180s | sumo_scenario.py:323-376; osm/client.py |
| OSM normalization | Big hand parser -> CityMapDto (roads, lanes, buildings, crossings, signals, PT) | osm/normalizer.py (1485 L) |
| netconvert | geometry.remove, roundabouts/ramps.guess, junctions.join, tls.guess(+signals), tls.discard-simple=false, default-type actuated, crossings/sidewalks.guess, ptstop/ptline output, osm typemap | sumo_scenario.py:429-482; `--tls.set` retry ladder 800/500/300/180/100 (l.396-403) |
| TLS repair | Strips tl refs to unknown tlLogic, demotes orphan traffic_light junctions | sumo_scenario.py:581-618 |
| Vehicle demand | trips file is EMPTY (l.620-621); cars spawned at runtime by Python on weighted edges (`_ensure_visible_vehicles`, `_vehicle_edge_weights`, sumo_engine.py:1596-1672) = visual fill, not OD demand model |
| Pedestrians | randomTrips.py --pedestrians --persontrips, 900s window (sumo_scenario.py:624-653) |
| PT | OSM routes -> ptline output; bus/tram/light_rail/train vTypes; runtime spawn every 300s (sumo_scenario.py:18-21, sumo_engine.py:1304) |
| Routing | duarouter --ignore-errors --repair (l.656+) |
| Road events | Runtime TraCI: lane.setDisallowed (close, l.2427/2457), lane.setMaxSpeed (roadwork, l.1986), rerouteTraveltime; random events events.py. Editor patches (close/open/remove/add road, crossing, signal) via /editor/apply (kinds in schemas/editor.py:6-14) |
| TLS override | all red/yellow/green/sumo-auto, setRedYellowGreenState (sumo_engine.py:236-245) |
| Live metrics | avg speed, avg wait, stopped(<0.5 m/s), congestion=stopped/active, throughput (metrics.py:82-114). Teleports and unfinished/loaded-vs-arrived NOT counted; time-to-teleport=45 hides gridlock (sumo_scenario.py ~829). No tripinfo/ summary.xml |
| Streaming | request/response polling, full state DTO |
| Notebooks | ai/notebooks/create_analysis_notebooks.py generates 4 ipynb (0.4-1.6 MB each, committed) |
| Safety supervisor / scenario compare / RL lab / LLM copilot / reports | absent |

## 4. Hardcoded assumptions / install
- No Astana/Kazakhstan constants in server/web src (grep clean). Defaults: 1000 m area text (App.tsx:73), CORS only localhost:5173.
- macOS-centric SUMO discovery: /opt/homebrew/opt/sumo, /Applications/SUMO.app, EclipseSUMO.framework 1.27.0, proj.db at /opt/homebrew/Cellar/proj/9.6.2 (sumo_scenario.py:56-82,156). Works on Apple Silicon if brew SUMO present; no Linux/Docker path. README tells `cd /Users/andrey/...`. `rglob` scans of /opt/homebrew & /Applications as fallback = slow.
- SUMO not pip-installed (no eclipse-sumo/libsumo in deps).

## 5. Quality / security
- Tests: 11 pytest + 2 vitest, no coverage config, no CI (.github absent). Mostly smoke.
- Files >800 L: sumo_engine.py 2690, CityScene.tsx 1989, create_analysis_notebooks.py 1509, normalizer.py 1485, global.css 1226, App.tsx 1091, sumo_scenario.py 994. sumo_engine is a god class.
- Security: no shell=True/os.system/eval (grep clean); subprocess with arg lists (run_command, sumo_scenario.py:953). pickle.dumps on export (write-only). Endpoints all unauthenticated; model path from filesystem glob (ai_tls_controller.py:94) and `safe_file_name`; delete_model uses stored path from registry (not user path) -> low traversal risk. Large bbox -> unbounded Overpass/netconvert DoS. Errors echo repr() to client (409 detail).
- Blocking sync endpoints run SUMO under a global lock -> no concurrency.

## 6. Reusable for FluxCity
| Item | File | Method |
|---|---|---|
| netconvert flag set + TLS retry ladder + repair_unknown_tls_references | server/app/simulation/sumo_scenario.py:379-618 | Copy and refactor into import service; add `--tls.guess-signals`-based tests |
| Overpass multi-mirror query | sumo_scenario.py:323-376, osm/client.py | Copy; add bbox area cap + cache |
| Pedestrian/PT generation (randomTrips, ptline) | sumo_scenario.py:624-760 | Copy ideas |
| Max-pressure TLS heuristic | ai/urbanflow_ai/env/{observations,actions,rewards}.py | Wrap as baseline controller behind FluxCity safety supervisor; ~500 L, clean, frozen dataclasses |
| Road close/roadwork via lane.setDisallowed/setMaxSpeed | sumo_engine.py:1951-2460 | Reimplement as typed scenario patches |
| OSM normalizer | osm/normalizer.py | Optional, only if CityMapDto-style JSON needed for viz |
| Three.js city scene | web/src/scene/* | Not recommended (2k-line monolith; FluxCity wants map viz) |
Do not reuse: session store, sumo_engine god class, training "registry", metrics (no teleports), polling API.

## Risks
1. "AI" is a fixed-weight heuristic; any RL/ML positioning must be built from scratch.
2. Single-session, lock-serialised, polling architecture cannot support side-by-side comparison, RL lab or multi-user.
3. Metrics/demand not credible for optimisation: empty trips, runtime-spawned visual traffic, teleports hidden, no OD demand; plus 2.7k-line god class and almost no tests/CI.
