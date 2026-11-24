# Task Backlog

ID format: `P<phase>.<n>`. **C** = Claude, **X** = Codex. Full prompts for P1–P2 are in `docs/orchestration/PROMPTS.md`.

| ID | Task | Agent | Depends | Size |
|---|---|---|---|---|
| P1.1 | Repo scaffold: uv workspace, web Vite app, CI, ruff/mypy/pytest/vitest, `.gitignore`, LICENSE | C | approval | S |
| P1.2 | `core/` domain models, hashing, manifest, provenance + `store/` SQLite repos + artifact CAS | C | P1.1 | M |
| P1.3 | `sim/` sumocfg builder + headless runner + `metrics/` parsers, KPIs, validity | X | P1.2 | M |
| P1.4 | `jobs/` SQLite queue + process pool + cancel + crash handling | X | P1.2 | M |
| P1.5 | `scripts/check_licenses.py` + CI gate + fixture nets via netgenerate | X | P1.1 | S |
| P1.6 | CLI `fluxcity run/rerun` + determinism test | C | P1.3, P1.4 | S |
| P2.1 | `network/osm_fetch` (mirrors, cache, provenance) | X | P1.2 | S |
| P2.2 | `network/import_pipeline` + quality report | X | P2.1 | M |
| P2.3 | FastAPI app, errors, regions/networks/jobs/runs routers + OpenAPI→TS types | C | P1.6 | M |
| P2.4 | Live worker telemetry encoder + WS endpoint + protocol tests | C | P2.3 | M |
| P2.5 | Web shell, theme tokens, map, network layer, workspace rail | X | P2.3 | M |
| P2.6 | Vehicle + TLS layers, playout buffer, controls, KPI strip | X | P2.4, P2.5 | M |
| P3.1 | Patch ops (close_edge, reduce_lanes, set_speed, scale_demand, set_tls_program) — extract agentsumo | X | P2.2 | L |
| P3.2 | Versioning, diff, apply pipeline | C | P3.1 | M |
| P3.3 | Experiments + paired comparison stats | C | P1.4 | M |
| P3.4 | Compare UI (sync maps, delta heat, KPI table) | X | P3.3, P2.6 | L |
| P4.1 | TLS static model + conflict matrix + static validator | C | P1.3 | M |
| P4.2 | SafetySupervisor + property tests | C | P4.1 | M |
| P4.3 | Controllers: max-pressure, queue; native wiring; Webster/green-wave wrappers | X | P4.2 | M |
| P4.4 | Signals workspace UI | X | P4.3 | M |
| P5.1 | Demand: OD/zones, random; routeSampler + GEH; synthetic-truth test | X | P3.2 | M |
| P6.1 | Optuna studies | X | P3.3, P4.3 | M |
| P6.2 | sumo-rl adapter (supervised TrafficSignal), train/eval jobs | X | P4.2 | M |
| P6.3 | RL/opt evaluation report | C | P6.1, P6.2 | S |
| P7.1 | Tool registry + executor + extracted agentsumo tools | C | P3.2 | L |
| P7.2 | LLM loop, approvals, claim verifier, SSE | C | P7.1 | M |
| P7.3 | Copilot UI + eval sets | X (UI) / C (eval) | P7.2 | M |
| P8.1 | Reports (HTML from records, print-to-PDF) | X | P3.3 | M |
| P8.2 | Astana demo script, perf pass, docs | C | all | M |
