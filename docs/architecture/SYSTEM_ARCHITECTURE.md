# System Architecture

Shape: a modular monolith, with one FastAPI process and a pool of SUMO worker processes. It runs locally on an M5 with 16 GB. Decisions: ADR-001…014.

## 1. Components
```
 web (React/TS, deck.gl+MapLibre)
   │ REST /api/v1 (JSON)        │ WS /ws/runs/{id} (binary frames + JSON)
 ┌─▼────────────────────────────▼───────────────────────────────┐
 │ api (FastAPI routers)  → services (no DB in routes)           │
 │  network · demand · scenario · runs · compare · control ·     │
 │  optimize · rl · copilot · reports                            │
 │ store: SQLite (metadata, jobs, events)   artifacts: CAS files │
 └──────┬───────────────────────────────────────▲───────────────┘
        │ job table (SQLite) + multiprocessing   │ results (parquet, manifest)
 ┌──────▼───────────────────────────────────────┴───────────────┐
 │ worker process × (cpu_count−2)  — one libsumo sim each        │
 │  sim.session → control.supervisor → controllers               │
 │  telemetry encoder (live runs) · metrics collectors           │
 └───────────────────────────────────────────────────────────────┘
 External, as argv subprocesses with timeouts: netconvert, duarouter, randomTrips,
 routeSampler, tlsCycleAdaptation, tlsCoordinator. Overpass is reached over HTTPS and cached.
```

## 2. Repository layout (target)
```
backend/fluxcity/
  core/        domain models (pydantic), ids, hashing, manifest, provenance   ← integrator-owned contracts
  store/       sqlite repositories, artifact store (content-addressed)
  network/     osm_fetch, import_pipeline, quality_report, plainxml
  demand/      random, od_matrix, route_sampler, calibration, geh
  scenario/    patches/ (one module per op), apply, versioning
  sim/         worker, session (libsumo), sumocfg builder, telemetry, collectors
  control/     protocol, supervisor, static_validator, controllers/
  metrics/     parsers (tripinfo, stats, summary, edgedata), kpis, validity, compare
  optimize/    optuna studies
  rl/          sumo-rl adapter (supervised TrafficSignal), train, evaluate
  copilot/     registry, tools/, executor, llm_client, claim_verifier, prompts
  api/         routers, ws, deps, errors
  jobs/        queue, pool
backend/tests/ unit, property (hypothesis), integration (real SUMO, small nets)
web/src/       app shell, map/, layers/, workspaces/, api/ (generated types), state/
data/fixtures/ committed small nets (netgenerate) + Astana extract snapshot
data/cache/, data/artifacts/, data/db/   (gitignored)
scripts/       check_licenses.py, gen_types.py, demo_*.sh
extracted/     not used. Extracted code lives in its target module with a header plus an UPSTREAM.md row.
```

## 3. Key flows
1. **Import.** bbox → Overpass (cached) → netconvert → `RoadNetworkVersion` + quality report. Then run randomTrips/duarouter, or import OD, to get a `DemandVersion`.
2. **Scenario.** Base `ScenarioVersion` → typed patch → apply (plain XML → netconvert) → child version. The diff is stored.
3. **Live run.** POST run → job → worker starts libsumo → supervisor and controller each step → telemetry over the WS → collectors → at the end: parquet, KPIs, validity, manifest.
4. **Experiment.** (versions × seeds) → N headless jobs in parallel → `Comparison` with paired stats (ADR-011).
5. **Copilot.** Message → LLM → tool calls → `read` runs immediately; `propose` creates a draft; `act` waits in the approval queue. The answer goes through the claim verifier before display.

## 4. Cross-cutting
- **Reproducibility.** Every run writes `manifest.json`: input hashes, SUMO version, FluxCity git SHA plus dirty flag, sumocfg args, seeds, controller spec and policy hash, platform, and wall time. `fluxcity rerun <manifest>` must reproduce the KPI hash.
- **Provenance.** Every network, demand and run carries `provenance ∈ {synthetic, osm_inferred, calibrated, observed}` and `calibration_status`. The UI badge comes from these fields.
- **Security.** Bind to 127.0.0.1. Validate IDs at the boundary. Resolve paths under `data/`. All subprocesses are argv lists with no shell. Parameterized SQL. No secrets in the repo; LLM keys (Gemini/OpenRouter) come from env.
- **Errors.** Typed `FluxError(code, message, detail)` maps to RFC 9457 problem+json.
- **Logging.** `logging` with structured run_id/job_id fields, never print.

## 5. UI/UX (map-first)
```
┌────┬──────────────────────────────────────────────┬──────────────┐
│rail│  Map canvas (deck.gl over MapLibre)           │ Inspector    │
│ N  │   layers: network, vehicles, signals, heat,   │ (selected    │
│ S  │   closures/patches, deltas                    │  edge/TLS/   │
│ C  │  [SYNTHETIC — UNCALIBRATED] badge, OSM attr.  │  run/patch)  │
│ Sg │                                               │              │
│ AI ├──────────────────────────────────────────────┤ Copilot      │
│ R  │ Timeline · play/pause/speed · KPI strip (with │ drawer +     │
│    │ teleports/unfinished/backlog always visible)  │ approvals    │
└────┴──────────────────────────────────────────────┴──────────────┘
```
- **Workspaces (MVP).** N = Network, S = Simulation, C = Scenarios and Compare, Sg = Signals, AI = Copilot, R = Reports. Demand, Optimization and RL start as panels inside S, C and Sg.
- **Compare (flagship).** Two synchronized maps, or one map with a swipe, sharing one camera and clock. An edge delta heatmap. A KPI table with mean Δ, CI and validity badges. A patch diff list.
- **Visual system.** Dark default plus light theme, with tokens defined once. Colorblind-safe sequential and diverging ramps. Metric colours carry units in the legend. Keyboard-accessible controls.
- Built with the `anthropic-skills:ui-ux-pro-max` skill at Phase 2.
