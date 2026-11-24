# Master Plan

Each phase ends at a gate: acceptance criteria pass, Opus code review, status update, user sign-off. Durations assume part-time work by one person with two agents.

| Phase | Goal | Duration | Owner (lead) |
|---|---|---|---|
| 0 | Discovery, audit, ADRs, plan | done → **approval pending** | Claude |
| 1 | Foundation: repo, CI, domain, store, headless run + metrics + manifest | 1–1.5 wk | Claude (contracts) / Codex |
| 2 | Network import + live viewer | 1.5–2 wk | Codex (impl) / Claude (WS, API) |
| 3 | Scenario Lab + Compare (**flagship**) | 2 wk | Claude (method) / Codex (patches, UI) |
| 4 | Signals: protocol, supervisor, baselines | 1.5 wk | Claude (supervisor) / Codex (controllers) |
| 5 | Demand + calibration | 1 wk | Codex |
| 6 | Optimization + RL | 1.5 wk | Codex (impl) / Claude (eval) |
| 7 | Copilot | 1.5 wk | Claude |
| 8 | Reports, Astana demo, hardening | 1 wk | both |

## Acceptance criteria
**P1 Foundation**
- `uv run fluxcity run data/fixtures/grid3x3` writes a manifest, tripinfo/summary/stats parquet, KPIs and validity.
- Same manifest → identical KPI hash. A different seed → a different hash (CI test).
- Teleports, unfinished trips, backlog and penalized travel time are present and unit-tested on a crafted gridlock fixture.
- Job pool runs 8 headless runs in parallel; cancel kills the process; a crash marks the job failed.
- CI green: ruff, mypy (strict on core/), pytest, license gate (ADR-014).

**P2 Import + viewer**
- Astana PoC bbox imports in under 30 s cold and under 3 s cached. The quality report matches the PoC counts (604 edges / 316 junctions / 30 TLS, ±5% across OSM updates).
- Map shows the network, live vehicles and TLS states. Play, pause and speed work. Reconnect resyncs through `hello`.
- At least 30 fps with 2k vehicles on the M5. The synthetic badge and OSM attribution are always visible.

**P3 Scenario Lab + Compare**
- Patches `close_edge`, `reduce_lanes`, `set_speed`, `scale_demand`, `set_tls_program` each produce a new version with a diff, and have unit tests on fixtures.
- Experiment: baseline vs closure, 10 seeds, in parallel. The comparison gives a CI table. The known-effect test passes.
- Compare UI: synced dual map, delta heatmap, KPI table with validity badges. An invalid arm shows INVALID.
- Rerun from any manifest is bit-identical in KPIs.

**P4 Signals**
- Supervisor property tests: 10k fuzzed sequences give 0 violations. The static validator passes on all fixture nets.
- Controllers: native static, actuated and delay_based; Webster via tlsCycleAdaptation; green wave via tlsCoordinator; max-pressure; queue.
- On a grid fixture at high demand, the report ranks all controllers with CIs, whatever the outcome.

**P5 Demand + calibration**
- OD/zone and random demand. routeSampler from counts. GEH report.
- Synthetic-truth test: GEH < 5 on at least 85% of counts.

**P6 Optimization + RL**
- An Optuna study over cycle/split/offset on the corridor is reproducible from a seed, and its best trial becomes a ScenarioVersion.
- DQN on a single intersection and PPO on the corridor, trained through the supervisor, evaluated on 10 held-out seeds against max-pressure and actuated. Report includes negative results.

**P7 Copilot**
- Registry of at least 15 typed tools. Approval UI. Claim verifier.
- Eval: at least 30 grounded and 10 injection cases at 100% traceability, 0 unapproved acts, 0 injection successes.

**P8 Demo**
- `scripts/demo_astana.sh` runs end to end in under 10 minutes: import, baseline, closure scenario, compare, signal comparison on the corridor, copilot Q&A, report.
- Every artifact carries the synthetic label.
