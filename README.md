# FluxCity

[![ci](https://github.com/AyanbergenSaduakassov07/FluxCity/actions/workflows/ci.yml/badge.svg)](https://github.com/AyanbergenSaduakassov07/FluxCity/actions/workflows/ci.yml)
[![license: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)
[![Eclipse SUMO 1.28](https://img.shields.io/badge/Eclipse%20SUMO-1.28-green)](https://eclipse.dev/sumo/)
[![data: synthetic, uncalibrated](https://img.shields.io/badge/data-synthetic%2C%20uncalibrated-orange)](#data-honesty)

**A city traffic digital twin built on [Eclipse SUMO](https://eclipse.dev/sumo/).** FluxCity
simulates a city's real OpenStreetMap road network, lets you change it (close roads, inject
crashes, rain or floods, test policies such as remote work or staggered school hours) and
compares every scenario against a matched baseline. A FastAPI backend serves the runs to a
React + deck.gl + MapLibre viewer. Everything runs locally from public data.

Demo city: **Astana** (in progress; the pipeline is being generalized to any OSM city).

## Data honesty
All results use **synthetic demand, uncalibrated**. No real traffic counts are used yet, so read
results as comparisons between scenarios, not forecasts. FluxCity is a simulation tool only: it
never controls real traffic signals or infrastructure.

## Features
| Area | What it does |
|---|---|
| Network | OSM extract → SUMO network via netconvert, lane defaults, network QA |
| Demand | Synthetic population and activity-based trips by day type |
| Simulation | City-wide mesoscopic runs plus microscopic focus windows |
| Events | Crash, rain, flood, motorcade and evacuation injected into runs |
| Policy lab | Scenario vs matched baseline: delay, vehicle-hours, CO2 |
| Strategist | Ranks emergency response options for human approval |
| Viewer | React + deck.gl map of edge speeds, trajectories and reports |

## Roadmap
1. Any-city support, Astana as the reference (OSM bbox import, auto-UTM, configurable day types)
2. New UI
3. Live simulation streaming (libsumo + WebSocket)
4. Signal control: fixed-time, actuated, max-pressure, RL (simulation only)
5. Grounded AI copilot with typed, approval-gated tools

## Quickstart
Needs macOS or Linux, [uv](https://docs.astral.sh/uv/), Node 22+ and `make`.
```bash
git clone https://github.com/AyanbergenSaduakassov07/FluxCity.git && cd FluxCity
make demo CITY=0     # demo window: setup + demo runs, viewer on http://localhost:5173
make test            # ruff + pytest
```

## Stack
Python 3.12 (uv), SUMO 1.28 (PyPI wheels), FastAPI, pydantic, pandas, DuckDB, GeoPandas.
React 19, TypeScript, Vite, deck.gl 9, MapLibre 5.

## License
Apache-2.0, see [LICENSE](LICENSE) and [NOTICE](NOTICE). FluxCity builds on
[TrafficTwin](https://github.com/alturkestani/TrafficTwin) (Apache-2.0). Map data
© OpenStreetMap contributors (ODbL).
