# Prompt Suite

Phases 1–2 have full prompts. Phases 3–8 are work packages (`TASK_BACKLOG.md`) and get expanded into full prompts at each phase gate, after the previous phase's real interfaces exist.

## Shared preamble (prepend to every prompt)
> You are working on FluxCity in worktree `../FluxCity-<task>` on branch `agent/<task>`.
> - Read `AGENTS.md` first (Codex) or `CLAUDE.md` (Claude). Then read only the doc sections named under Context.
> - Edit only the **Owned files** plus their tests. Do not change `backend/fluxcity/core/` unless you are the integrator. Request contract changes in the handoff instead.
> - Rules:
>   - Python 3.12 with uv. Type hints everywhere.
>   - `logging`, never print. No bare except. No mutable defaults. Parameterized SQL only.
>   - Subprocesses are argv lists with timeouts and no shell. Functions stay under 50 lines.
>   - New logic is test-first (pytest).
> - Do not copy GPL, EUPL or unlicensed code. Extracted MIT/Apache code keeps its header and gets a row in `UPSTREAM.md`.
> - Finish by running the listed tests, committing with `<type>: <desc>`, and appending the handoff block (`docs/orchestration/HANDOFF_PROTOCOL.md`).

---
### P1.1 Repo scaffold — Claude
- **Objective:** Create an empty, buildable monorepo with CI.
- **Context:** `SYSTEM_ARCHITECTURE.md §2`, `ADR-003`, `ADR-014`.
- **Reuse:** `discovery/poc-results/pyproject.toml` (SUMO pins).
- **Owned:** `pyproject.toml`, `backend/fluxcity/__init__.py`, `backend/tests/test_smoke.py`, `web/` (Vite React TS template), `.github/workflows/ci.yml`, `.gitignore`, `LICENSE` (Apache-2.0), `README.md`.
- **Sequence:**
  1. Run `git init`.
  2. Create the uv project with deps eclipse-sumo==1.28.0, libsumo==1.28.0, fastapi, pydantic, pyarrow, duckdb, plus dev deps pytest, hypothesis, ruff, mypy.
  3. Run `pnpm create vite web --template react-ts` and add deck.gl and maplibre-gl.
  4. Add CI jobs: python (ruff, mypy, pytest) and web (tsc, vitest).
- **Tests:** a smoke test imports `libsumo` and runs `sumo --version`.
- **Acceptance:** `uv run pytest` and `pnpm -C web build` pass locally, and CI YAML is valid.
- **Commit:** `chore: scaffold monorepo with CI`.

### P1.2 Domain models + store — Claude (integrator)
- **Objective:** Implement the contracts that every other module imports.
- **Context:** `DOMAIN_MODEL.md` (all), `ADR-004`, `SYSTEM_ARCHITECTURE.md §4 Reproducibility`.
- **Owned:** `backend/fluxcity/core/{models,ids,hashing,manifest,provenance,errors}.py`, `backend/fluxcity/store/{db,repos,artifacts}.py`, `backend/fluxcity/store/schema.sql`, plus tests.
- **Interfaces:**
  - `ArtifactStore.put(path|bytes) -> sha256`
  - `ArtifactStore.path(sha) -> Path`
  - `Repo[T].create/get/list(cursor, limit)`
  - `content_hash(model) -> str`
- **Sequence:**
  1. Write the pydantic models (frozen) and the enums.
  2. Write the canonical JSON hashing.
  3. Write the SQLite schema (WAL) and the repositories, with parameterized SQL.
  4. Write the content-addressed artifact store under `data/artifacts/`.
- **Tests:**
  - Hash stability across field order.
  - Immutability.
  - Repo round-trip.
  - Path traversal is rejected in the artifact store.
- **Acceptance:** mypy strict passes on `core/` and tests pass.
- **Commit:** `feat: core domain models and sqlite/artifact store`.

### P1.3 Headless runner + metrics — Codex
- **Objective:** Run a ScenarioVersion headless with libsumo and produce KPIs, validity and parquet outputs.
- **Context:** `METHODOLOGY.md §2–3`, `ADR-002`, `ADR-013`, `DOMAIN_MODEL.md` (`SimConfig`, `RunResult`).
- **Reuse:** TrafficTwin `sim/metrics.py` and the `sim/runner.py` stats parsing (Apache-2.0; extract with header). Also `discovery/poc-results/bench_step.py`.
- **Owned:** `backend/fluxcity/sim/{sumocfg,runner,collectors}.py`, `backend/fluxcity/metrics/{parsers,kpis,validity}.py`, `data/fixtures/` (netgenerate grid3x3 + gridlock fixture), plus tests.
- **Interfaces:**
  - `run_headless(sv: ScenarioVersion, seed: int, out_dir: Path) -> RunResult`
  - `compute_kpis(tripinfo, stats, window) -> Kpis`
  - `check_validity(kpis, gates) -> Validity`
- **Sequence:**
  1. Build the fixtures with netgenerate and randomTrips at a fixed seed.
  2. Write the sumocfg builder, which only accepts allow-listed args.
  3. Write the libsumo loop with warm-up and drain.
  4. Write the parsers: tripinfo, statistics and summary, to parquet.
  5. Compute the KPIs, including penalized travel time.
  6. Apply the validity gates.
- **Tests:**
  - KPI values on the grid fixture are within tolerance of `sumo --duration-log.statistics`.
  - The gridlock fixture shows unfinished trips > 0, penalized travel time > completed-trip mean, and an invalid flag.
- **Acceptance:** the tests pass, and the grid run takes under 2 s.
- **Commit:** `feat: headless libsumo runner with honest KPIs`.

### P1.4 Job queue + worker pool — Codex
- **Objective:** Run jobs in parallel in isolated processes.
- **Context:** `ADR-002`, `DOMAIN_MODEL.md` (`Job`, `Run`).
- **Owned:** `backend/fluxcity/jobs/{queue,pool,worker}.py`, plus tests.
- **Interfaces:**
  - `enqueue(kind, payload) -> Job`
  - `Pool(n).start()`
  - `cancel(job_id)`
  - Job handlers are registered by kind.
- **Sequence:**
  1. Build the SQLite job table, with claim-by-update and a heartbeat.
  2. Use `multiprocessing` with spawn, one process per job.
  3. Cancel sends SIGTERM, then SIGKILL after 5 s.
  4. A crash marks the job failed and records the stderr tail.
- **Tests:**
  - 8 parallel fixture runs all complete.
  - Cancelling a long run takes under 6 s.
  - A deliberately crashing handler is marked failed and the pool survives.
- **Commit:** `feat: sqlite job queue and process pool`.

### P1.5 License gate + fixtures CI — Codex
- **Objective:** Make ADR-014 enforceable in CI.
- **Context:** `ADR-014`, `REUSE_MATRIX.md §3`.
- **Owned:** `scripts/check_licenses.py`, `scripts/license_allowlist.toml`, a CI step, plus tests.
- **Behavior:** the script fails on:
  - A dependency license not on the allow-list (via `importlib.metadata`).
  - Any path matching `nets/RESCO`.
  - A file with an `Extracted from` header but no `UPSTREAM.md` row.
- **Tests:** a temp tree with a violation fails, and a clean tree passes.
- **Commit:** `ci: license gate`.

### P1.6 CLI + determinism — Claude
- **Objective:** Provide `fluxcity run <scenario.yaml|fixture>` and `fluxcity rerun <manifest>`.
- **Context:** `METHODOLOGY.md §3.6`.
- **Owned:** `backend/fluxcity/cli.py`, `backend/tests/test_determinism.py`.
- **Acceptance:**
  - The same manifest gives an identical KPI hash.
  - A different seed gives a different hash.
  - The manifest includes the SUMO version and git SHA.
- **Commit:** `feat: cli run/rerun with determinism test`.

### P2.1 OSM fetch — Codex
- **Objective:** Fetch an Overpass bbox or polygon reliably, with a cache.
- **Context:** `ADR-012`.
- **Reuse:** UrbanFlow `sumo_scenario.py:323-376` and `osm/client.py` (Apache-2.0, extract).
- **Owned:** `backend/fluxcity/network/osm_fetch.py`, plus tests.
- **Interfaces:** `fetch_osm(area: BBox|Polygon, cache: ArtifactStore) -> NetworkSource`.
- **Rules:**
  - Area cap of 25 km² for Overpass. Larger areas raise `AreaTooLarge` with a Geofabrik hint.
  - Generic User-Agent.
  - Timeout of 120 s, with a mirror list.
- **Tests:** mocked HTTP for mirror fallback, a cache hit, the area cap, and a malformed response.
- **Commit:** `feat: overpass fetch with mirrors and cache`.

### P2.2 Import pipeline + quality report — Codex
- **Objective:** Turn an OSM file into a `RoadNetworkVersion` with a quality report.
- **Context:** `ADR-012`, `PHASE0_REPORT.md §2` (Astana numbers).
- **Reuse:** UrbanFlow `sumo_scenario.py:379-618` (flags, TLS retry ladder, `repair_unknown_tls_references`) and TrafficTwin `sim/network/build_city.py` (Apache-2.0).
- **Owned:** `backend/fluxcity/network/{import_pipeline,quality_report,plainxml}.py`, `data/fixtures/astana_lb.osm.xml.gz` (the PoC extract, ODbL), plus tests.
- **Tests:**
  - Importing the Astana fixture gives 604 ±5% edges and 30 ±3 TLS.
  - The quality report fields are populated, with `turn_lanes_coverage == 0`.
  - The plain-XML round trip is stable.
- **Commit:** `feat: osm import pipeline and network quality report`.

### P2.3 API skeleton — Claude
- **Objective:** Provide the FastAPI app with routers for regions, networks, jobs and runs, plus TS type generation.
- **Context:** `API_CONTRACTS.md §REST`, `SYSTEM_ARCHITECTURE.md §4`.
- **Owned:** `backend/fluxcity/api/**`, `backend/fluxcity/services/{network,runs}.py`, `scripts/gen_types.py`, `web/src/api/types.ts`.
- **Rules:**
  - Bind to 127.0.0.1.
  - problem+json errors.
  - Routes call services, never the store directly.
  - IDs are validated by regex.
- **Tests:** httpx route tests and an OpenAPI snapshot.
- **Commit:** `feat: api v1 skeleton`.

### P2.4 Live telemetry — Claude
- **Objective:** A live run streams over the WS per `ADR-010`.
- **Context:** `ADR-010`, `API_CONTRACTS.md §WebSocket`.
- **Owned:** `backend/fluxcity/sim/telemetry.py`, `backend/fluxcity/api/ws.py`, plus tests.
- **Tests:**
  - Encoder/decoder round trip.
  - Reconnect gets a `hello` with the current state.
  - Under a slow consumer, frames are dropped but stats and events are not.
  - Pause and resume work.
- **Acceptance:** encoding 2k vehicles takes under 2 ms per frame.
- **Commit:** `feat: live telemetry websocket`.

### P2.5 Web shell + network layer — Codex
- **Objective:** Build the map-first shell from `SYSTEM_ARCHITECTURE.md §5`.
- **Context:** that section and `API_CONTRACTS.md` (`/networks/{id}/geometry`).
- **Reuse:** TrafficTwin `web/src/engine.ts` and `binCache.ts` (Apache-2.0).
- **Owned:** `web/src/{app,map,layers/network,workspaces,theme,state}/**`, plus tests.
- **Tests:** vitest for the geometry decode, and a Playwright smoke test that the map renders with the badge and attribution.
- **Commit:** `feat: web shell and network layer`.

### P2.6 Vehicles, signals, controls — Codex
- **Objective:** Render live vehicles and TLS states, with a playout buffer.
- **Context:** `ADR-010` (buffer rules), `API_CONTRACTS.md §WebSocket`.
- **Owned:** `web/src/{live,layers/vehicles,layers/signals,components/Timeline,components/KpiStrip}/**`, plus tests.
- **Tests:**
  - Buffer unit tests: interpolation, the teleport guard, and reset on time regress.
  - Frame-time profiling at 2k vehicles reaches at least 30 fps.
- **Commit:** `feat: live vehicle and signal layers`.

---
## Phases 3–8: work packages
These are expanded into full prompts at their phase gate, using the backlog rows P3.1–P8.2. Each expanded prompt must name its Context sections, Reuse paths (from `REUSE_MATRIX.md`), Owned files, Interfaces, Tests and Acceptance (from `MASTER_PLAN.md`), and Commit.
