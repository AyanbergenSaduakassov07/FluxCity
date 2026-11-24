# FluxCity

**FluxCity is an open-source platform for traffic simulation, infrastructure scenarios and signal optimization, built on [Eclipse SUMO](https://eclipse.dev/sumo/).**

The goal is to model a city's road network, change it (close a road, cut a lane, retime signals, add a bus lane), and compare the result against the baseline with honest statistics.

- The demo city is Astana. The platform works for any city with OpenStreetMap coverage.
- Simulation only. FluxCity does not control real traffic signals.
- Astana results use synthetic demand and OSM-inferred lanes. They are **not calibrated** and are labelled that way everywhere.

> **Status:** Phase 1 (foundation) has started. Planning is done; see [`docs/planning/PHASE0_REPORT.md`](docs/planning/PHASE0_REPORT.md).

## What it will do
| Area | Summary |
|---|---|
| Network import | Import a bbox from OpenStreetMap, convert it with netconvert, and get a network quality report |
| Live simulation | libsumo workers stream vehicles and signals to a deck.gl + MapLibre map |
| Scenario Lab | Versioned, typed patches; side-by-side comparison on paired seeds with confidence intervals (flagship) |
| Signals | Fixed-time, actuated, Webster, green wave, max-pressure and RL controllers. External commands go through a deterministic safety supervisor |
| Honest metrics | Teleports, unfinished trips and insertion backlog are reported next to every KPI. Runs that fail validity gates are marked INVALID |
| Optimization / RL | Optuna studies; sumo-rl + Stable-Baselines3 |
| AI copilot | Typed tools with approval gates and number-checked answers. No shell access |

## Stack
Python 3.12 (uv), FastAPI, pydantic, SUMO 1.28 (PyPI wheels), SQLite + Parquet + DuckDB. React 19, TypeScript, Vite, deck.gl and MapLibre.

## Quick start
```bash
uv sync                      # Python deps, including the SUMO binaries
uv run pytest -q             # backend tests
cd web && pnpm install && pnpm dev
```

## Documentation
- [Architecture](docs/architecture/SYSTEM_ARCHITECTURE.md) · [Domain model](docs/architecture/DOMAIN_MODEL.md) · [API contracts](docs/architecture/API_CONTRACTS.md)
- [Decisions (ADRs)](docs/adr/README.md) · [Methodology](docs/methodology/METHODOLOGY.md)
- [Master plan](docs/planning/MASTER_PLAN.md) · [Backlog](docs/planning/TASK_BACKLOG.md) · [Status](docs/planning/PROJECT_STATUS.md)
- [Reuse matrix and licenses](docs/dependencies/REUSE_MATRIX.md) · [Upstream sources](UPSTREAM.md)
- Contributors and agents: [AGENTS.md](AGENTS.md)

## License
Apache-2.0 (see [LICENSE](LICENSE)). Third-party notices are in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Map data © OpenStreetMap contributors (ODbL).
