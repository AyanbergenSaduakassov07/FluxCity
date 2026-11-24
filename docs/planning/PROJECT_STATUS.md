# Project Status

| Date | Phase | State | Note |
|---|---|---|---|
| 2026-11-24 | 0 | **Approved** | ADR-001…014 accepted. Harvest-into-new-repo; libsumo workers + supervisor + validity gates; copilot on free Gemini/OpenRouter; Apache-2.0. |
| 2026-11-24 | 1 | In progress | P1.1 scaffold done: uv + SUMO 1.28 pins, web (Vite/React/deck.gl/MapLibre), CI, Apache-2.0. Next P1.2 ‖ P1.5 |

## Open decisions
None blocking Phase 1.

## Not yet done in Phase 0
- TrafficTwin `make demo` and UrbanFlow were not run. Their audits come from code reading only.
- SB3 training was not benchmarked. Netedit/sumo-gui were not installed.
- The provenance of the non-RESCO sumo-rl nets was not confirmed. Fixtures will be regenerated with netgenerate instead.

## Compute policy (user decision 2026-11-24)
The Mac does only light work: edit code, run unit tests, run small fixture sims. Heavy work runs on GitHub Actions or a cloud runner, never locally: experiments with many seeds, Optuna studies, RL training, district-scale runs.
