# TrafficTwin audit (commit 53a0d4ea, Apache-2.0)
Verified from source (grep/wc/ls), not README. Suitability as primary foundation: **4/10** (high-value donor of modules; poor as a base to fork whole).

## 1. Architecture
| Item | Finding |
|---|---|
| Top dirs (LOC) | sim/ 22.9k py; tests/ 6.4k py; scripts/ 4.6k py; api/ 3.6k py; strategist/ 3.4k py; web/ 4.9k ts/tsx; docs/ 841-line STATUS.md + ~40 md |
| Backend | FastAPI (api/main.py), file-backed, read-only except POST /api/jobs and decision log |
| Frontend | React 19 + Vite 7 + deck.gl 9.4 + maplibre-gl 5; no state lib (plain hooks; App.tsx 497 lines, engine.ts 32 KB); cinema/ = headless deck.gl for films |
| SUMO driving | Main runs: `sumo` CLI subprocess (sim/common.py:83, sim/runner.py, api/jobs.py:129). TraCI (`import traci`) only in sim/scenarios/simulate.py, sim/events/evacuation.py, strategist/evaluate.py, snapshot.py. **No libsumo.** No live TraCI streaming to the viewer. |
| Process isolation | One subprocess per job; api/jobs.py keeps a job json + log in logs/api-jobs; TT_MAX_JOBS (default cap) 409 if exceeded. No queue/worker. |
| Storage | Files only: runs/<id>/{meta.json, metrics.json, edgedata.parquet, fcd.parquet, tripinfo.parquet, *_report.json, recommendations.json, decisions.jsonl}; contract docs/contracts/run-outputs.md v1.1. duckdb is a dependency but unused in code (grep: 0 hits). No sqlite. |
| Run artifact | Parquet 5-min edge bins (Tier A), FCD parquet (Tier B only), JSON reports; edges.bin geometry per network hash. |

## 2. Implemented features
| Feature | Where | Notes |
|---|---|---|
| OSM ingest | sim/network/build_city.py (Geofabrik download, osmium clip by data/osm/jeddah.poly, netconvert via sim/network/config/city-v2.yaml, fix list data/osm/fixes) | Pipeline general in shape; inputs Jeddah-specific. Needs `osmium` binary. |
| Network overrides | sim/network/lane_defaults.py (Jeddah lane/speed medians), lane_audit.py (imagery audit) | Jeddah-specific evidence |
| Districts/buildings | sim/network/geo.py (admin_level from poly; Voronoi fallback) | Generalizable |
| Synthetic population | sim/population/{zones,synthesize,activities,modes,sampling}.py + config/*.yaml | Activity/trip-chain based on zones, GASTAT 3,712,917 control total (zones.yaml), OSM building/street/landuse residential weights, prayer-time activity anchors. Weights are judgement ("assumption:"). |
| Tier A meso | sim/config/runner.yaml (`--mesosim --meso-junction-control`, tls penalty 0.5) | whole city, 24h |
| Tier B micro | sim/bridge/window.py (30 KB), sim/network/build_window.py, windows/*.yaml | focus windows, FCD output, sublane |
| Day types | sim/daytypes/{weekday,friday,saturday,ramadan_weekday,umrah_season}.yaml, prayer.py | Gulf-specific |
| Events | sim/events/{accident,flood,motorcade,weather,emergency,evacuation(66 KB)}.py | accident/rain/flood/motorcade/evac; Tahlia/Obhur scenarios in sim/scenarios/*.yaml |
| Policies / comparison | sim/policies/{transforms,run,report,sweep}.py + yamls (remote work, staggered schools, cordon, bus line, ridehail, Loop tunnel, bridges) | policy vs baseline "difference mode" report; sim/loop/ mode choice |
| Strategist | strategist/{candidates,rank,evaluate,approve,explain}.py, strategist.yaml, weights.yaml | Rule-based candidate generation + forked-TraCI evaluation + weighted ranking + human approval log. **No LLM** (grep: none). Not an RL/signal optimizer. |
| Calibration (M8) | sim/calibrate.py, sim/adapters/{counts,traveltimes,synthetic}.py | routeSampler.py fit to counts + GEH<5; **dormant**: no Jeddah counts, proven only on synthetic counts |
| Metrics | sim/metrics.py, sim/runner.py:113-143 | Counts teleports (total/jam/yield/wrongLane), loaded, inserted, `vehicles_waiting_at_end` (runner.py:138), depart_delay per trip; teleport_share gate <0.5% (runner.yaml:44). Insertion backlog = loaded-inserted/waiting (no dedicated "unfinished trips" KPI or time-series). CO2/NOx, hourly+district parquet, top corridors. |
| Viewer | web/src/App.tsx, engine.ts, components/{JobsPanel,Timeline,StrategistPanel,ReportsPanel,SummaryTable,Legend,Hud}.tsx, cinema/ | run panel, timeline scrubber over edge bins, district choropleth, strategist approve UI, policy diff view |
| API (28 endpoints) | api/routers/runs.py: GET /api/runs, /{id}, /metrics, /bins, /bins/{i}, /district-effects, /trajectories, /policy-report, /scenario-report, /recommendations, /decisions; POST /{id}/recommendations/{opt}/decision. networks.py: GET /api/networks/{hash}/edges.{bin,json}. geo.py: GET /districts, /buildings. jobs.py: POST /api/jobs, GET /{id}, /{id}/events (log tail). GET /health | Missing vs FluxCity: no OSM-import-by-city endpoint, no demand-gen endpoint, no live WS stream, no patches API, no copilot, no signal edit, no reports export. Jobs only run `--smoke` random trips (api/jobs.py:31 `kind: Literal["smoke"]`). |

## 3. Generalizing to an arbitrary city
No city-config abstraction. City is baked into file names (`data/jeddah/*`, 44 references in py), config YAML, and function constants.

| Hardcode | file:line |
|---|---|
| Prayer coords + TZ Asia/Riyadh + Umm al-Qura | sim/daytypes/prayer.py:15-16 (coords param exists) |
| UTM zone 37N (EPSG:32637) | sim/network/geo.py:18; sim/population/zones.py:41; sim/policies/edges.py:114; sim/loop/site.py:56 |
| Map plot bbox 39.02-39.26 / 21.50-21.84 | sim/bridge/desire.py:361-363; sim/loop/site.py:407 |
| Viewer map centre [39.18, 21.55] | web/src/engine.ts:190 |
| Network paths, poly | sim/config/runner.yaml (smoke.tier_A.net), data/osm/jeddah.poly, sim/network/config/city*.yaml, api/settings.py:42-47 (districts/buildings default paths, env-overridable) |
| Census control total + exclusions (airport, seaport, naval base) | sim/population/config/zones.yaml |
| Lane/speed medians | sim/network/lane_defaults.py + sim/network/types/jeddah-lanes.json |
| Day types Friday/Ramadan/Umrah, weekend Fri-Sat | sim/daytypes/*.yaml; population activities.py (15 city refs); config/population.yaml (50 refs) |
| Named edge ids/scenarios (Tahlia, Obhur, Corniche, obh_*) | sim/scenarios/*.yaml, sim/policies/*.yaml, sim/bridge/run.py:106, data/jeddah_flood_sites.yaml, strategist/scenarios/ |
| Arabic narration, films | tests/test_narration_ar.py, docs/movies-arabic.md |
Effort: network build + zones + prayer are parameterizable (~1-2 wks); population/activity config and policies are heavy rewrites. The package layout (`sim/*`) is shared by all cities, so a city switch means a new `data/<city>/` plus editing ~10 YAMLs and ~6 constants; no registry.

## 4. Tests and CI
- 32 test files, ~313 test functions (tests/), 6.4k LOC. Cover API, producers, bridge, builder, calibrate, evacuation, events, lane audit, links, loop, movies, narration, network v2, policies, population, runner, strategist. Run offline on committed demo window (data/demo/demo.net.xml, 2 MB).
- CI (.github/workflows): ci.yml (ruff check+format, pytest on demo window, web typecheck+build; actions SHA-pinned), demo-smoke.yml, pages.yml. City-scale runs never in CI. No frontend unit tests (only typecheck/build; web/scripts/{screenshot,perf}.mjs).

## 5. Quality / security
| Item | Finding |
|---|---|
| shell=True / os.system | none found |
| Subprocess | list-form args everywhere; job params typed by pydantic (tier A/B, seed>=0, end>0) |
| Path traversal | api/runs.py:RUN_ID_RE + `_check_id` + `is_relative_to(runs_dir)` (good); jobs id regex api/routers/jobs.py/api/jobs.py:78 |
| Auth | **none**; POST /api/jobs and decision POST unauthenticated; CORS limited to localhost:5173 by default (env TT_CORS_ORIGINS), methods GET/POST. Local-tool posture only. |
| Concurrency | in-process job registry, JSON file state; no queue, no multi-user, no DB |
| Debt | docs heavy (assumptions registry ~84 KB), huge single files (evacuation.py 66 KB, link.py 51 KB, window.py 30 KB, normalize.py 26 KB) exceeding the 800-line ceiling; "Track A..J" provenance baked into names; symlinked data/jeddah to another checkout (sim/link.py:58) |
| Python | 3.12 only, uv, ruff clean in CI; SUMO via `eclipse-sumo` wheel (>=1.24; README 1.28) |

## 6. Reusable modules for FluxCity
| Module | Method | Why |
|---|---|---|
| api/runs.py + normalize + contract docs/contracts/run-outputs.md | extract / reference | traversal-safe file-backed run registry, nested baseline/scenario runs, defensive reads |
| web/src/engine.ts + binCache.ts + Timeline + color/legend | extract | deck.gl edge-bin timeline viewer, edges.bin binary geometry, difference mode |
| sim/metrics.py, sim/runner.py stats parsing (teleports, waiting, inserted) | extract | statistic-output + tripinfo to parquet, CO2/NOx, GEH-style gates |
| sim/calibrate.py + sim/adapters/counts.py | extract | routeSampler+GEH pipeline, city-agnostic once counts exist |
| sim/policies/transforms.py, report.py, sweep.py | reference | scenario-patch + diff-report pattern (YAML patches on net/routes) |
| strategist/{candidates,evaluate,fork,rank,approve} | reference/extract | fork-TraCI-state, evaluate candidates, rank, human-approval log (fits safety supervisor idea) |
| sim/network/build_city.py + geo.py (districts) | extract + parametrize | OSM->netconvert->fixes pipeline; replace jeddah.poly with arbitrary bbox/polygon |
| sim/population/zones.py, synthesize.py, sampling.py | reference | zone-weighted synthetic demand idea; needs a general rewrite (census input, no prayer anchors) |
| sim/events/{accident,weather,flood}.py | reference | event injection via TraCI |
| tests/ patterns (demo-window fixtures) | reference | offline reproducible test data |
Fork-and-keep whole repo: not recommended; too much Jeddah/Track history.

## 7. Weaknesses
- Teleport: `--time-to-teleport 300` (runner.yaml:7, assumption A-sim-002; range 120-600) with `--ignore-route-errors` (runner.yaml:8) masks unroutable demand; gate is <0.5% of loaded vehicles, only post-hoc; no waiting-for-insertion cap (`max-depart-delay` unset) so insertion backlog silently accumulates, reported only as `waiting_at_end`.
- Demand is synthetic, uncalibrated (label on every JSON); control total from census, activity weights judgement; no real counts; M8 calibration dormant.
- Tier A meso with `meso-tls-penalty 0.5` assumed, no signal timing data; fidelity test docs/fidelity.md vs micro exists but only on demo window.
- No real-time/live TraCI streaming, no signal-controller authoring/RL, no LLM copilot, no multi-city.
- Single-user local design, no auth, no DB.
