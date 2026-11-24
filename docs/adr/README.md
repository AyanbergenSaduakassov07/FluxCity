# Architecture Decision Records

Status key: **Proposed** means it is awaiting approval. **Accepted** means it is approved.

| ADR | Decision | Status |
|---|---|---|
| [001](ADR-001-foundation.md) | New repo; harvest permissive modules; no app fork | Accepted |
| [002](ADR-002-sim-runtime.md) | libsumo in one worker process per run; TraCI only for sumo-gui | Accepted |
| [003](ADR-003-stack.md) | FastAPI + pydantic v2 / React + TS + deck.gl + MapLibre / SQLite + Parquet + DuckDB | Accepted |
| [004](ADR-004-scenario-versioning.md) | Immutable content-hashed versions; typed patches applied to SUMO plain XML | Accepted |
| [005](ADR-005-controller-supervisor.md) | Controller protocol + deterministic Signal Safety Supervisor | Accepted |
| [006](ADR-006-baseline-controllers.md) | SUMO-native and SUMO-tool baselines; our own max-pressure and queue controllers | Accepted |
| [007](ADR-007-rl.md) | sumo-rl + SB3, with actions routed through the supervisor | Accepted |
| [008](ADR-008-optimization.md) | Optuna only (TPE, NSGA-II); no pymoo or OR-Tools in MVP | Accepted |
| [009](ADR-009-copilot.md) | Typed tool registry, approvals, claim verifier, no shell; free Gemini/OpenRouter via OpenAI-compatible client | Accepted |
| [010](ADR-010-telemetry.md) | WebSocket binary frames at 10 Hz plus a render-behind interpolation buffer | Accepted |
| [011](ADR-011-comparison-method.md) | Paired-seed replications, CI on differences, warm-up exclusion | Accepted |
| [012](ADR-012-osm-import.md) | Direct Overpass with mirror fallback + cache; Geofabrik/osmium for large areas | Accepted |
| [013](ADR-013-validity-gates.md) | Teleports, unfinished trips and backlog are first-class; validity gates | Accepted |
| [014](ADR-014-licensing.md) | Licensing policy and FluxCity license (Apache-2.0) | Accepted |

Every custom build that replaces a possible upstream needs an ADR. Add new ones as `ADR-NNN-slug.md`.
