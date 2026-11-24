# Simulation and Evaluation Methodology

## 1. What FluxCity results mean
FluxCity outputs are **microsimulation estimates under stated assumptions**. For Astana, demand is synthetic and lane/turn data is partly inferred: OSM has 0 `turn:lanes` in the PoC extract. Results are valid for comparing scenarios against each other under the same assumptions. They are not forecasts of real Astana traffic. Every report states the provenance and calibration status.

## 2. KPIs (definitions)
| KPI | Definition | Source |
|---|---|---|
| Mean travel time (completed) | mean tripinfo `duration` over trips departing in the measurement window | tripinfo |
| Penalized travel time | completed trips' duration, plus (end − depart + departDelay) for each unfinished trip | tripinfo + vehroutes/loaded |
| Mean time loss / delay | mean `timeLoss` | tripinfo |
| Mean waiting time | mean `waitingTime` (speed < 0.1 m/s) | tripinfo |
| Stops | mean `waitingCount` | tripinfo |
| Throughput | arrived per hour in the window | statistics/summary |
| Max / mean queue length | per lane, from `queue-output` or lane halting count | queue/summary |
| Insertion backlog | `waiting` at end + total depart delay | statistics |
| Unfinished trips | loaded − arrived at end | statistics |
| Teleports | count by cause | statistics |
| Collisions, emergency stops | count | statistics |
| CO2 / NOx / fuel | sum from emission output, HBEFA4 class defaults | emissions (optional) |
| Corridor travel time | mean traverse time across a defined edge sequence | edgeData / tripinfo filter |
| Supervisor overrides | count by type | FluxCity events |

## 3. Experimental protocol
1. **Warm-up.** Default 900 s. KPIs count only trips that depart after warm-up and before `end`.
2. **Drain.** The simulation continues up to 1800 s after the last departure, and unfinished trips are counted.
3. **Replications.** N paired seeds. Each seed fixes randomTrips/duarouter and the SUMO `--seed`. Defaults: N = 10 for reports, N = 3 for exploration (labelled indicative).
4. **Estimate.** For each KPI, take the mean of per-seed differences (candidate − baseline). Use a 95% t-interval, or a bootstrap with 10k resamples when N ≥ 20. Report absolute, % and CI.
5. **Validity gates** (ADR-013). An invalid arm is not ranked.
6. **Determinism test.** The same manifest gives an identical KPI hash; a different seed gives a different hash. CI runs this on the fixture net.

## 4. Controllers and RL
- Baselines on every controller comparison: fixed-time (netconvert default and Webster), actuated, max-pressure.
- RL: train seeds and eval seeds are disjoint. Report learning curves, eval on N = 10 held-out seeds, and supervisor override counts. A policy that relies on overrides is flagged.
- No result is called "optimal". Optimization results are "best found in K trials under objective X".

## 5. Calibration
- Calibration is count-based: SUMO `routeSampler` against edge or turn counts. Optionally, demandify GA against speeds.
- Fit metrics: GEH < 5 for at least 85% of counts (the standard target), plus MAE, RMSE and bias per interval.
- Validation on synthetic truth: generate "truth" demand, extract counts, recalibrate from a perturbed start, and check that the target GEH is recovered. This proves the pipeline without real data.
- Astana stays `calibration_status = none` until real counts exist.

## 6. Evaluation of FluxCity itself
| Area | Check | Target |
|---|---|---|
| Reproducibility | rerun from manifest | identical KPI hash |
| Supervisor | hypothesis fuzz | 0 conflicting greens, 0 intergreen/min-green violations in 10k sequences |
| Telemetry | 2k vehicles, 10 Hz | ≥ 30 fps on M5, < 150 ms end-to-end latency |
| Import | Astana PoC bbox | < 30 s cold, < 3 s cached |
| Copilot | grounded eval set (≥ 30) + injection set (≥ 10) | 100% claim traceability, 0 unapproved acts, 0 injection successes |
| Comparison | known-effect test: closure of an arterial on grid | delay increase detected, CI excludes 0 |
