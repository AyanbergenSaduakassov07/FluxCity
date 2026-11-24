# ADR-006: Baseline controllers
Status: Accepted (2026-11-24)

| Controller | Implementation | Through supervisor |
|---|---|---|
| Fixed-time | SUMO `static` tlLogic from netconvert / user plan | no (static validator) |
| Actuated (gap) | SUMO native `type="actuated"` | no |
| Delay-based | SUMO native `type="delay_based"` | no |
| Webster | SUMO `tools/tlsCycleAdaptation.py` → static plan (offline method, not a runtime controller) | no |
| Green wave | SUMO `tools/tlsCoordinator.py` offsets | no |
| Max-pressure | Own (~60 LOC) via `trafficlight.getControlledLinks` + lane vehicle counts | yes |
| Queue-based (longest queue first) | Own (~40 LOC) | yes |
| RL policy | ADR-007 | yes |

**Why our own code.** Every classical controller in the audited set is GPL-3, EUPL or unlicensed. Each is under 100 LOC from published formulas.
