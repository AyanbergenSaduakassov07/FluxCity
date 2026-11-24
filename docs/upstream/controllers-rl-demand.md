# FluxCity audit: signal control, RL, demand/calibration repos

Date: 2026-11-24. Source-verified from clones in `discovery/upstream/`. Nothing was run or installed (static read only), so "works on Apple Silicon" claims are inferred from deps, not tested.
Method labels: **dependency** = pip-install and call; **extract** = copy code (permissive only); **reference-only** = read, reimplement clean-room; **reject**.

## 1. Per-repo table

| Repo | License (verified) | What it really is | Quality / tests | SUMO coupling | Apple Silicon / deps | Verdict |
|---|---|---|---|---|---|---|
| sumo-rl | MIT (`LICENSE`). **Bundled `nets/RESCO/*` are NOT MIT** (see 2.1) | Gymnasium + PettingZoo (AEC and Parallel) env, ~1.2k LOC in `sumo_rl/environment/`. Q-learning agent, SB3 PPO and DQN example scripts in `experiments/` | Clean, small. Tests: only `tests/gym_test.py`, `tests/pz_test.py` (API conformance, 100 s sims). No logic tests | `sumolib>=1.14`, `traci>=1.14`; needs `SUMO_HOME` (raises ImportError otherwise); libsumo via `LIBSUMO_AS_TRACI` env var | Pure Python; gymnasium, pettingzoo, numpy, pandas. No torch dep (examples use SB3). libsumo availability on macOS arm64 depends on the eclipse-sumo wheel, unverified | **Dependency for env (optional), extract ideas.** Prefer own thin env |
| RESCO | Code GPL-3.0 (`LICENSE`). Scenarios per-folder (see 2.2) | Benchmark framework v2.0: `multi_signal.py` (606 LOC), `traffic_signal.py`, agents (FIXED, MAXPRESSURE, MAXWAVE, STOCHASTIC, IDQN, MPLight, IPPO, MA2C, FMA2C, CoSLight, SWOKS, COOM-SAC, RLCD) | Research code, config via YAML + `quik_config`. No test dir found | `eclipse-sumo>=1.17`, `numpy<2`, python `>=3.7` declared; README says libsumo "requires linux" | torch + pfrl (old); FMA2C needs `tensorflow==1.15.5`, py3.7. Poor on arm64 | **Reference-only (code). Scenarios: reject for commercial** |
| LibSignal | **No root LICENSE file** (only `data/raw_data/ingolstadt21/LICENSE`, GPL-3.0). README has no license | Cross-sim (SUMO, CityFlow, OpenEngine) lib: `agent/` has fixedtime, maxpressure, sotl, presslight, mplight, colight, frap, dqn, ppo, sac, maddpg, magd. `world/world_sumo.py` 38 KB | Research code, YAML configs per sim. No tests | SUMO via traci; `gym==0.21.0`, `numpy==1.21.5` pinned | Old pins (gym 0.21, numpy 1.21) break on modern Python; CityFlow has no arm64 story | **Reject** (all rights reserved by default). Do not even copy snippets |
| sumolights | GPL-3.0 | 3.1k LOC. Controllers in `src/trafficsignalcontrollers/`: `maxpressuretsc.py`, `websterstsc.py`, `sotltsc.py`, `uniformcycletsc.py`, `nextphaserltsc.py`, `nextdurationrltsc.py`; DQN, DDPG in `src/rlagents/` | Paper code. No tests | README: SUMO **v1.2**; `tensorflow==1.14.0` | TF1.14: dead on arm64/py3.11+ | **Reference-only** (Webster formula and phase-deque pattern). Reject code |
| smart-traffic-rl | **No LICENSE file**. README badge says "Academic" | 1.2k LOC. `src/realcity/baselines.py` (fixed + max-pressure on Cologne8 via sumo-rl), `ippo.py`, `colight.py` (both reported **failed to converge**) | Small scripts, no tests | sumo-rl, SB3 2.3.2, libsumo>=1.18 | torch via SB3 | **Reject** (unlicensed). Useful finding only: max-pressure beat their IPPO/CoLight; use it as a baseline sanity check |
| open_controller | EUPL-1.2 (`LICENSE.md`) | Docker/NATS microservice stack. `services/control_engine` is a **signal-group controller engine** (intergreen matrix, min times, conflict groups, `signal_group_controller.py` 456 LOC, `signal_group.py` 580 LOC). `services/safety_extender/` (experimental gap extension). `services/simengine` (SUMO via libsumo over NATS), `indicators` (sensor fusion), UI | Best engineering of the set: ruff strict config, `tests/unit` + `tests/integration` (e2e clockwork, timer, config). Needs py3.13 | `libsumo>=1.27.0`, `nats-py` | py3.13 only; Docker for normal use | **Run as separate service only, or reference-only** (see 2.4) |
| websumo | EUPL-1.2 | FastAPI + libsumo + NATS relay, deck.gl/MapLibre frontend; `backend/src/sumo_adapter.py` 31 KB; large `docs/` of research notes | Backend 1.9k LOC. One test elsewhere (`test_websumo_geo_fallback.py` lives in open_controller). Bundles a 15.8 MB `nats-server` binary | libsumo | arm64 untested; bundled nats-server binary arch unknown | **Separate tool only** if we want a viewer. Not a core component |
| demandify | MIT | OSM to SUMO net, TomTom speeds, GA demand calibration (DEAP), FastAPI UI + CLI, Demand Studio editor, HTML reports | Strongest test suite: 33 test files (objective, GA, worker seed, reproducibility, import mode, routing). CI: `release.yml`, `reproducibility.yml` | Developed on SUMO 1.26. Runs `sumo`, `netconvert`, `duarouter` as subprocesses (`utils/validation.py`) | Pure Python wheels (deap, shapely, rtree, pyproj, protobuf). No torch. py>=3.9 | **Dependency or extract** for GA + demand model. Objective must change (see 2.5) |
| video-to-sumo-rl | MIT (code). RESCO is described as CC BY-NC-SA 4.0 in its LICENSE (contradicts RESCO's own GPL-3.0 file, so treat RESCO as unclear) | Video (YOLO11x + ByteTrack) to turning counts to SUMO `routeSampler` demand, GEH validation, RESCO IDQN with pressure reward. `release_v2/code/tools/` holds the analysis, `resco_integration/` patches RESCO | Heavy research release, SHA manifest, preregistration. Not a library | SUMO tools `routeSampler.py` via subprocess, libsumo/traci | torch 2.12, ultralytics 8.4.75 | **Extract** `demandlib.py` and GEH logic; **reject** the video stage (ultralytics is AGPL-3.0, not verified in this repo, check before use) |
| sumo-traffic-network-builder | **No license, no LICENSE file** | `pipeline/main.py`, `main_v2.py`: OSM bbox to net (netconvert) + Mapillary enrichment + randomTrips demand; mentions "Real-Twin" calibration | Tiny scripts, no tests | netconvert, randomTrips | conda env | **Reject** (unlicensed). Idea only |

## 2. Detail answers

### 2.1 sumo-rl
- **min_green and yellow enforcement:** `sumo_rl/environment/traffic_signal.py`, `TrafficSignal.set_next_phase()` (lines 179-203). If `new_phase == green_phase` or `time_since_last_phase_change < yellow_time + min_green`, the request is ignored and the phase held. Otherwise a yellow state (built in `_build_phases()`, lines 128-161) is set and `is_yellow` flips; `update()` (168-177) restores green after `yellow_time`. `enforce_max_green` optionally forces advance (line 188); constructor docstring still says max_green "currently ignored" (stale). This is soft env logic, not a safety supervisor: no conflict matrix, no all-red, no intergreen, yellow derived by rule (G/g to r/s becomes y, line 149), phase list taken from the net's first program and any phase containing `y` dropped. Yellow transitions are made for every phase pair, so no clearance-time check by movement.
- **Observation** (`_observation_fn_default`, line 238): one-hot green phase + min_green flag + per-lane density + per-lane queue (incoming only, normalized by lane capacity). Pluggable via `ObservationFunction` subclass (`observations.py`). **Rewards** (`reward_fns`, line 347): `diff-waiting-time` (default), `average-speed`, `queue`, `pressure`, `co2`; custom via `register_reward_fn` or a list with weights (multi-objective).
- **Action semantics:** discrete index of the next green phase (not duration, not extend/switch). `delta_time` default 5 s between decisions; action applied only when `time_to_act`.
- **PettingZoo:** `sumo_rl.env()` (AEC) and `sumo_rl.parallel_env()`; `SumoEnvironment` itself is a gymnasium env, `single_agent=True` for one signal. `resco_envs.py` wraps RESCO nets (grid4x4, arterial4x4, cologne1/3/8, ingolstadt1/7/21).
- **libsumo:** `LIBSUMO = "LIBSUMO_AS_TRACI" in os.environ` (env.py line 37). Single connection only in libsumo mode.
- **Bundled nets:** `single-intersection`, `2way-single-intersection`, `2x2grid`, `3x3grid`, `4x4-Lucas`, `4x4loop`, `Nguyen`, `OW`, `double`, `simple`, and `RESCO/` (7 scenarios). **License trap:** the repo is MIT but `nets/RESCO/` carries third-party terms: arterial4x4, grid4x4 = CC BY-NC-ND 4.0 (PDF in folder); cologne1/3/8 = CC BY-NC-SA (CC legal code PDF); ingolstadt1/7/21 = GPL-3.0 `LICENSE`. Do not ship those. The other nets have no license file, so provenance is unconfirmed; generate our own nets.
- **Non-RL controller plug-in:** yes. Fixed: `fixed_ts=True` (ignores actions, follows net program). Anything else: call `env.step({ts: phase_idx})` with a rule-based policy; `smart-traffic-rl/src/realcity/baselines.py` proves max-pressure works this way (reads `env.traffic_signals[ts].sumo` and `green_phases`). Limitation: action space is phase index only, so Webster (durations) must be emulated by choosing when to switch.

### 2.2 RESCO
- **Controllers:** `agents/static/fixed.py` (FIXED, STOCHASTIC), `maxpressure.py` (thin: reuses `WaveAgent`, `observation[1:]`), `maxwave.py` (argmax over `cfg["phase_pairs"]` of summed direction values); RL: `action_value/` (pfrl_dqn IDQN, mplight, rlcd, multiheaded_dqn, advanced_xlight), `policy/` (pfrl_ppo, ma2c, fma2c, coom_sac, CoSLight, SWOKS). No Webster, no actuated, no queue-based as such (MAXPRESSURE here is a lane-count wave variant, not true max pressure).
- **Safety:** yellow built per phase pair in `traffic_signal.py::create_yellows` (line 16), `cfg.yellow_length`, all-red transition. Similar to sumo-rl, no supervisor.
- **Scenarios:** `resco_benchmark/environments/LICENSE` says each folder has its own license. Verified: cologne1 = CC BY-NC-SA 3.0; arterial4x4, grid4x4 = CC BY-NC-SA 4.0 (RESCO) vs BY-NC-ND 4.0 (sumo-rl's copy: disagreement, either is non-commercial); ingolstadt1 and saltlake2 = GPL-3.0. Data and code are licensed separately; none are permissive. Non-commercial and GPL data cannot go in the core.
- **Deps:** fma2c needs TF 1.15.5 / py3.7; numpy<2.

### 2.3 LibSignal
- Controllers present: `fixedtime.py`, `maxpressure.py` (generators + `t_min`), `sotl.py`, presslight, mplight, colight, frap, dqn, ppo, sac, maddpg, magd. SUMO world: `world/world_sumo.py` (has yellow dict, `yellow_phase_time`, virtual phase). Configs `configs/sim/sumo*.cfg`.
- No license anywhere at root; default copyright applies. **Cannot reuse or adapt even one function.** Reading for ideas is allowed but keep notes separate from our implementation.

### 2.4 open_controller and websumo (EUPL-1.2)
- open_controller models a real field controller: signal groups with per-state minimums, intergreen matrix, conflict groups (`signal_group_controller.py::_set_conflict_groups`, `_tick_minimum`), NATS messaging, SUMO via libsumo as "simengine". This is the closest thing in the set to a **deterministic signal safety supervisor** (conflict + intergreen + minimum enforcement). `safety_extender/` is a separate, labelled experimental gap-extension tool, not a general supervisor.
- EUPL-1.2 is weak-copyleft per file, with a compatibility list (includes GPL-2/3, MPL-2, EPL-2, AGPL; not MIT/Apache). Copying or modifying its files forces EUPL on those files and on a combined work distributed together. Running unmodified as a **separate process talking over NATS** is a mere aggregation/communication boundary and does not impose EUPL on our code (not legal advice; confirm with counsel before shipping a Docker bundle that includes it). Network-use clause: EUPL treats SaaS provision as distribution (Art. 5 "Communication to the public"), so hosting a modified copy requires publishing the changes.
- Recommendation: do not copy. Reimplement the supervisor from the public concepts (intergreen matrix, min green, conflict groups, all-red clearance), which are standard traffic-engineering ideas, not protectable code. Optionally use open_controller as an external reference controller in comparisons.
- websumo is a viewer only: FastAPI + NATS + deck.gl. Standalone mode spawns its own libsumo adapter. Not needed in the core.

### 2.5 demandify
- **Algorithm:** `calibration/optimizer.py::GeneticAlgorithm` on DEAP. Genome = `num_od_pairs * num_bins` vehicle counts (docstring line 61). Features: intervalwise MAE, MAE-elite Pareto selection with teleport/failure filtering, random immigrants, assortative mating, deterministic crowding, adaptive mutation boost, genotypic and phenotypic diversity tracking, seeded, parallel workers (`calibration/worker.py`).
- **Observed data:** **edge speeds, not counts.** `calibration/objective.py::EdgeSpeedObjective` compares simulated vs observed speed normalized by free-flow. Observed input is TomTom Traffic Flow (`providers/tomtom.py`, vector tiles, needs `TOMTOM_API_KEY`, free tier 2,500 req/day) or an offline bundle `observed_edges.csv` + `traffic_data_raw.csv` + `network.net.xml` (`offline_data.py`, 7 bundled cities in `offline_datasets/`).
- **Gap for FluxCity:** no vehicle-count objective, no GEH. Needs a new `CountObjective` (sim edge or detector counts per interval vs counts; GEH or RMSE). Genome and GA are generic and reusable; simulation reads edgeData, so counts are available via `<edgeData>` output (`sumo/simulation.py` line 60 mentions edgeData).
- **Outputs:** `exporter.py` writes SUMO net/routes/sumocfg + metadata; `custom_formats.py` (URB/RouteRL), HTML report (`export/report.py`), `cache/keys.py` content-addressed cache (5-min traffic buckets).
- **UI/API:** FastAPI app (`app.py`, `web/routes.py`, `dataset_routes.py`, `studio_routes.py`), Jinja templates, CLI (`cli.py`, `demandify doctor`). No stable library API; `pipeline.py` is a 2,000-line orchestrator.
- **Tests:** 33 files; objective, GA early stopping, worker seed, offline reproducibility, routing, OD bias. Good enough to refactor against.
- **SUMO:** README states tested on 1.26.0; shells out to `sumo`, `netconvert`, `duarouter` (so no Python binding coupling).
- **Risk:** v0.0.6, single author, 2026 repo. Pin a commit.

### 2.6 video-to-sumo-rl
- **GEH:** `release_v2/code/tools/twin_geh.py`. Formula `sqrt(2 (M - C)^2 / (M + C))`, M=C=0 gives 0, observed = 5-min turning counts as hourly equivalents (x12), simulated = vehicles crossing the stop line per movement per interval (via TraCI odometer extraction). Standard GEH is 5 lines; extract the definition and the per-interval cell bookkeeping, write own.
- **Count to demand:** `tools/demandlib.py`: `read_counts`/`write_counts` (SUMO `edgeRelation` interval XML), `largest_remainder` apportionment (rounding that preserves totals), deterministic wrapper around SUMO `tools/routeSampler.py` (timestamp stripped for reproducibility, SHA-256 signatures). This is the reusable piece. Equal-length intervals required by routeSampler (noted in `e14_demand.py`).
- **Count extraction:** `src/stage1_track.py` (YOLO11x + ByteTrack), `calib_fisheye.py`, `classify.py`; `tools/perception_*.py` are validation UIs. Depends on ultralytics (AGPL-3.0 upstream, flag for legal) and fisheye cameras specific to their site. Not reusable for FluxCity without rework.
- **RL:** `resco_integration/` patches RESCO (GPL per RESCO's own file) with `pressure_norm` reward. Reference only. Their conclusion: pressure reward is stable under saturation, waiting-time reward is not.

## 3. Matrix: feature, repo, file, method, license

### 3.1 Controllers and interface

| Feature | Repo | File | Method | License |
|---|---|---|---|---|
| Env interface (gym/PettingZoo), phase-index action | sumo-rl | `sumo_rl/environment/env.py`, `traffic_signal.py` | dependency (or reference for own interface) | MIT |
| Observation function plug-in (`ObservationFunction`) | sumo-rl | `environment/observations.py` | extract (pattern) | MIT |
| Reward registry (pressure, queue, diff-wait, speed, co2) | sumo-rl | `traffic_signal.py::reward_fns` | extract | MIT |
| Soft min_green/yellow logic | sumo-rl | `traffic_signal.py::set_next_phase`, `_build_phases` | reference-only (not a safety supervisor) | MIT |
| Deterministic safety supervisor: conflict matrix, intergreen, min times | open_controller | `services/control_engine/src/signal_group_controller.py`, `signal_group.py` | reference-only (reimplement) | EUPL-1.2 |
| Fixed-time | sumo-rl | `SumoEnvironment(fixed_ts=True)` | dependency; trivial to write own | MIT |
| Fixed-time (other) | RESCO `agents/static/fixed.py`; LibSignal `agent/fixedtime.py` | reference-only; reject | GPL-3.0; none |
| Actuated (gap-based) | none in set | n/a. SUMO native `type="actuated"` tlLogic; RESCO paper baselines only | write own / use SUMO built-in | EPL-2.0 (SUMO) |
| SOTL | sumolights `trafficsignalcontrollers/sotltsc.py`; LibSignal `agent/sotl.py` | reference-only; reject | GPL-3.0; none |
| Max-pressure | smart-traffic-rl `src/realcity/baselines.py` (nice, uses `getControlledLinks`); sumolights `maxpressuretsc.py`; RESCO `static/maxpressure.py`; LibSignal `agent/maxpressure.py` | reference-only for all; write own in ~60 LOC using `trafficlight.getControlledLinks` | none; GPL-3.0; GPL-3.0; none |
| Max-wave | RESCO `static/maxwave.py` | reference-only | GPL-3.0 |
| Webster | sumolights `websterstsc.py` (Webster 1958 formula, `C=(1.5L+5)/(1-Y)`) | reference-only; formula is public domain, reimplement from the textbook | GPL-3.0 |
| Queue-based (longest queue first) | none dedicated | write own (sumo-rl `get_lanes_queue`, `get_total_queued` pattern) | MIT pattern |
| Uniform cycle | sumolights `uniformcycletsc.py` | reject (trivial) | GPL-3.0 |
| DQN (single) | sumo-rl `experiments/dqn_2way-single-intersection.py`, `dqn_big-intersection.py` (SB3) | extract (examples) | MIT |
| PPO | sumo-rl `experiments/ppo_4x4grid.py`, `sb3_grid4x4.py` (SB3, PettingZoo wrapper) | extract (examples) | MIT |
| MARL (shared-param, parallel_env) | sumo-rl `ql_4x4grid_pz.py`, `sb3_grid4x4.py`; RESCO IDQN/MPLight/IPPO/MA2C | sumo-rl extract; RESCO reference-only | MIT; GPL-3.0 |
| MPLight / PressLight / CoLight / FRAP | RESCO `action_value/mplight.py`; LibSignal `agent/*` | RESCO reference-only; LibSignal reject | GPL-3.0; none |
| DDPG (continuous duration) | sumolights `rlagents/ddpgagent.py` (TF1) | reject | GPL-3.0 |
| Benchmark scenarios | RESCO envs (cologne, ingolstadt, saltlake), sumo-rl bundled RESCO nets | reject for core; may use locally for research only | CC BY-NC-SA / NC-ND / GPL-3.0 |
| Simple synthetic nets (single-intersection, 2x2) | sumo-rl `sumo_rl/nets/` | extract only after confirming provenance (no per-net license), else regenerate with netgenerate | MIT repo, nets unverified |
| Viewer | websumo | run as separate tool | EUPL-1.2 |

### 3.2 Demand and calibration

| Feature | Repo | File | Method | License |
|---|---|---|---|---|
| GA over OD x time-bin counts | demandify | `calibration/optimizer.py`, `worker.py` | dependency (pin commit) or extract | MIT |
| Objective (speed MAE) | demandify | `calibration/objective.py` | extract; add count/GEH objective | MIT |
| Count-based calibration | none native; SUMO `tools/routeSampler.py`, `flowrouter.py`, `tools/calibrator` | external tool | dependency (SUMO tool, call by subprocess) | EPL-2.0 |
| Count to routes wrapper, largest-remainder rounding, edgeRelation I/O | video-to-sumo-rl | `release_v2/code/tools/demandlib.py` | extract | MIT |
| GEH per movement per 5-min interval | video-to-sumo-rl | `tools/twin_geh.py` | extract (definition) or write own | MIT |
| OSM to SUMO net | demandify `sumo/network.py`, `providers/osm.py` | extract | MIT |
| Offline observed-data bundles, cache keys | demandify | `offline_data.py`, `cache/keys.py` | extract | MIT |
| Live speed observations | demandify | `providers/tomtom.py` | extract only if a TomTom key and terms fit (ToS limit commercial caching; check) | MIT code, TomTom API terms |
| Export routes/net/sumocfg, report | demandify | `export/exporter.py`, `report.py` | extract | MIT |
| Demand editor UI | demandify | `web/studio_routes.py`, `sumo/studio_service.py` | optional | MIT |
| Counts from video | video-to-sumo-rl | `src/stage1_track.py` | reject (ultralytics AGPL, site-specific) | MIT wrapper |
| Net + randomTrips pipeline | sumo-traffic-network-builder | `pipeline/main.py` | reject | none |

## 4. Recommendations (ranked)
1. Build our own `Controller` protocol (observation to proposed phase request), a `SafetySupervisor` between controller and TraCI, and a thin SUMO env. Write fixed, actuated (use SUMO native), max-pressure, queue-based, Webster from textbooks. Reason: every classical implementation in this set is GPL/EUPL/unlicensed, and each is under 100 LOC.
2. Use sumo-rl as the optional RL adapter and for DQN/PPO/MARL examples (MIT). Do not ship its `nets/RESCO/`.
3. Take demandify as the demand backbone; add a count/GEH objective; take `demandlib.py` and GEH from video-to-sumo-rl. Prefer SUMO `routeSampler.py` first, GA only when routeSampler cannot match counts.
4. Reference-read only: RESCO, sumolights, open_controller. Never read-then-copy; reimplement from the paper/public formula.
5. Reject: LibSignal, smart-traffic-rl, sumo-traffic-network-builder (no license).
6. Open items: legal read of EUPL separate-process use; ultralytics AGPL if video counts ever enter; confirm provenance of non-RESCO sumo-rl nets; test libsumo on macOS arm64 with the SUMO version we pin.
