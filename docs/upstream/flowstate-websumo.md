# Audit: flow_state and websumo (FluxCity references)

Scope note: audited the cloned `main` only (single local branch). flow_state README says SafeSignal, RL env, forecaster and Gemini code live on branches `task/rl-signal-control`, `task/ml-intelligence`. They are NOT in the clone (grep for safesignal/gemini/gymnasium/stable_baselines: zero code hits). Those parts are README claims only, unverified. Fetching the branches needs network; not done.

## 1. flow_state (VedantSheel08, c57700d1)

### License
No LICENSE/COPYING file anywhere (find, excluding node_modules); no `license` field in frontend/package.json; no pyproject.toml; README only mentions Toronto Open Data licence for data. Default copyright applies: architectural reference only, no code copying. Toronto/OSM data are separate and licensed on their own terms.

### Architecture (about 20.8k LOC py+ts, excluding data)
- Backend: Python, FastAPI (`api/app.py` 230, `api/service.py` 401), SUMO via traci in engine (`sim/engine.py` 686, "one SUMO process driven through TraCI"; README also says libsumo for performance path `performance/`). Scenario library `scenarios/components.py` 1306 LOC (11 scenarios built from reusable seeded components). Signals `sim/signals.py` 799.
- Frontend: React 19, Vite, Zustand, Tailwind 4, Radix, Recharts, vitest. NO MapLibre/deck.gl: a custom Canvas 2D renderer (`map/renderer.ts` 981, `map/vehicles.ts` 839 sprite atlas, `camera.ts`, `scene.ts`, `Minimap.tsx`) over a SUMO-local-metre network (not geographic tiles). Cached Path2D geometry under a camera transform, sprite atlases per vehicle type.
- Deploy: Render (Docker) + Vercel; run.sh.

### Telemetry
- WebSocket, JSON text, one `frame` message per sim step, rate-limited to <=20 Hz; separate 1 Hz `stats`, `event`, `status`, `run`, `results`, `job` messages; `hello` on connect carries run + events + results (reconnect resync). Client reconnect with exponential backoff (500 ms to 8 s), 15 s ping.
- Frame: `{type,run,t,v:[[id,typeCode,x,y,angle,speed,signalBits]...],p:[[id,x,y,angle,speed]...],tls:{tlsId:stateString}}`. Values rounded (x,y 2 dp). Verbose JSON per frame (no binary, no delta); fine at small scale, a bandwidth risk for large networks.
- Interpolation (`lib/frames.ts`): playout buffer of last 40 frames; renders about 1.25 frame intervals behind newest; cubic Hermite using SUMO heading+speed as tangents so vehicles pass exactly through SUMO positions and follow curves; never extrapolates; render clock gently pulled to target to absorb jitter; reuses view objects to avoid GC; TELEPORT_M=40 m threshold avoids interpolating across jumps; time going backward resets buffer (restart).
- Warm-up: SUMO runs 90 s before scenario clock t=0 (negative t during warm-up).

### Reproducibility
Seed draws a concrete scenario instance; driver profiles seeded. Test `tests/test_engine.py::test_same_seed_reproduces_the_simulation`: run seed 11 twice and seed 12 once to t=60, compare sorted (id, x, y) of the frame plus completed count; assert a==b and a!=c. Also `test_scenarios.py` (same seed reproduces inputs, different seeds differ, invalid params rejected, every scenario instantiates for many seeds). Replay recorder pairs arms by seed.

### Metrics (honest definitions)
- Teleports: `getStartingTeleportNumber()` counted per step, event emitted ("SUMO started teleporting..."); SUMO args `--time-to-teleport 240`, highways 0. Teleporting vehicles are filtered from frames (INVALID_DOUBLE sentinel check).
- Collisions: `--collision.action warn --collision.check-junctions true --collision-output`. `sim/safety.py` explicitly separates raw collision record observations, "episodes" (pair+type reappearing after an unreported step) and unique pairs, with an in-payload definition string stating it is not a count of physical crashes. Good pattern.
- Waiting/travel time, throughput, queues taken from SUMO, never estimated (README). Paired comparison stats with CIs in `replay/record.py` (`paired`, bootstrap-style rng_seed).

### Controller / signals
- On main there is no controller interface in the RL sense. `sim/signals.py` is a signal-plan designer: ITE kinematic yellow, all-red from crossed width and speed, pedestrian clearance, role inference of netconvert phases (`phase_roles`), cycle/split by intersection type, corridor offsets, actuated programs that never shorten clearance intervals (`write_actuated_programs`). Tests (396 LOC) assert legal sequences, clearance floors, pedestrian walk+clearance, offsets reduce waiting, SUMO executes the plan, no gridlock.
- `replay/heuristic.py`, `priority.py`: two hand-written rules acting only on green durations (amber/all-red/ped clearance untouched) used for fixed vs adaptive replay.
- SafeSignal (per README, branch only, not verified): min green 14 s incl. ped clearance, max green 60 s forced change, always full yellow + all-red; controller requests, wrapper decides. PPO (SB3 + Gymnasium) trained but README admits it does not beat the adaptive heuristic. Forecaster: gradient boosting, 30/60 s queue, MAE 2.23 vs 4.38 persistence (claim only).
- Gemini grounding (per README, branch only): explanations "checked against the measured simulation numbers", offline fallback. Implementation not available to audit.

### Comparison / playback UI
- `views/SideBySide.tsx` (625) and `LiveComparison.tsx`: two canvases, shared camera (`SharedView`, modes junction/follow/network/free), replay of recorded half-second frames at 1.5x (`replay/record.py` runs both arms headless 5 min per seed, records frames for display seed; every number shown comes from `artifacts/replay/district-eval.json`, including worse-run counts, so no cherry-picking). Live controlled comparison: two headless runs, same seed, differing in one setting (`service.start_compare`, thread per job, progress over WS `job` message).
- Honesty: README reports small gains (adaptive vs fixed -5.8% wait on 2x2 grid), states PPO not better. Replicate the tone.

### Tests
tests/: engine, signals, scenarios, scenarios_sumo, placement, network, performance, replay, api; frontend vitest (intensity, nav). Strong domain-level assertions rather than snapshot tests.

## 2. websumo (Open-TLC, EUPL-1.2)

License: EUPL-1.2 (LICENSE.md). Copyleft; EUPL-1.2 compatibility list includes GPLv2/3, AGPL, MPL, EPL; combining into a non-listed-compatible/proprietary product triggers obligations. Treat as reference unless FluxCity is itself copyleft-compatible.

- Size: about 3.5k LOC (backend 5 py files: main.py FastAPI 351, sumo_adapter.py 698, simbridge.py 383, network.py 341, fcd_fusion.py 138; frontend 6 tsx: MapView 608, App 359).
- Stack: FastAPI + libsumo (in-process, README says about 8x faster than TraCI socket) + NATS broker; browser gets WebSocket relay of NATS. Frontend: React, MapLibre GL JS basemap + deck.gl 9 overlay layers (`PolygonLayer` for vehicles as oriented rectangles from length/width, `ScatterplotLayer` persons/generators, `LineLayer` detectors/stop lines/crossings); network as GeoJSON source in MapLibre.
- How it gets SUMO state: simengine (own `sumo_adapter.py` or external Open Controller via `simbridge.py`, about 15 lines in an external step loop) publishes `sim.{scenario}.state` JSON each step (~10 Hz). Viewer is a pure NATS subscriber, file-free: network/detectors/routes served by request-reply as gzipped XML.
- State message v1: `{v,t,vehicles:[[id,lon,lat,angle,length,width,vclass]],persons:[...],tls:{junction:"GGrr"},detectors:{id:bool},maxRate}`. Lon/lat already projected server-side, so deck.gl needs no client projection. Detector occupancy unioned per displayed frame (explicitly documented bug-avoidance at 20x speed).
- Events: separate `log` subject from libsumo structured APIs (`getCollisions`, `getStartingTeleportIDList`, `getEmergencyStoppingVehiclesIDList`), verified 1:1 against SUMO stderr.
- Control: pause/resume/stop/speed/scale/spawn/select via `cmd.*` subjects, buffered and applied before next step; `select` attaches an inspect block (vehicle ~24 fields, TLS program table). Known limitation: selection is one global slot (not multi-user).
- Playback: live stream only, speed slider with `maxRate` ceiling feedback. No client-side interpolation found (grep), no recorded-timeline scrub. Weaker than flow_state here.
- Docs worth skimming for ideas (not code): `docs/SIM_PROTOCOL.md`, `BASEMAP_TILES_STRATEGY.md`, `NATS_TRACI_REPLACEMENT_RESEARCH.md`.
- Tests: none found in tree.

## 3. Patterns FluxCity should replicate (abstract)

1. Render-behind playout buffer + Hermite interpolation from SUMO heading/speed, no extrapolation, teleport-distance guard, reset on time regress. Best-in-class here; implement in FluxCity on a GPU layer.
2. Server is authoritative: vehicle positions, signals, and every metric straight from SUMO, never estimated.
3. Separate channels: high-rate frames vs 1 Hz stats vs discrete events vs status; `hello` snapshot on connect for reconnect resync.
4. Versioned wire protocol (websumo `v:1`) and per-frame occupancy union at high speed.
5. Safety metrics with explicit definitions in the payload (collision records vs episodes vs pairs; teleports separately).
6. Seed to reproducible demand; paired controller arms on the same seed; same-seed determinism test (a==b, a!=c) plus invariants like "clearance never shortened".
7. Side-by-side as two views of recorded or headless paired runs sharing one camera; results page numbers all derived from one eval artifact, including losing runs.
8. Signal supervisor as a thin filter between controller and SUMO: controller requests, supervisor enforces yellow/all-red/ped clearance/min-max green. Write FluxCity's own constraint set from ITE-style formulas, with property tests that fuzz controllers against it.
9. Honest reporting: publish negative RL results.
10. Warm-up period so the map starts populated.

## 4. Where they beat or lose to TrafficTwin/UrbanFlow (note: those audits are separate; comparison from the architecture facts above only)

- Better than a typical canvas/leaflet demo: flow_state's interpolation, paired-seed evaluation with CIs, collision semantics, signal legality test suite. websumo's deck.gl + MapLibre on real geography, and a NATS decoupling of sim and viewer.
- Weak points to improve on: flow_state uses Canvas 2D with local metres (no real basemap, will struggle past a few thousand vehicles) and verbose JSON frames (use binary/typed arrays or delta + gzip); websumo has no interpolation, no playback timeline, no tests, global single-selection state; flow_state main lacks a controller interface, SafeSignal/Gemini code unavailable to audit.
- FluxCity opportunity: combine websumo's MapLibre+deck.gl geography with flow_state's playout buffer, recorded-run timeline scrubbing, and a real controller/supervisor interface with tested constraints, plus a Gemini-style claim checker that is machine-verified (extract numbers from LLM text, compare to measured metrics with tolerance, reject or flag). flow_state only describes this; FluxCity should specify and test it.

## Not verified
SafeSignal, RL env, Gemini check (branches absent); websumo frontend interpolation inferred from grep only; throughput limits untested (nothing run).
