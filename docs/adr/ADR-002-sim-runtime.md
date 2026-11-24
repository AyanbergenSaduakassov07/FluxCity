# ADR-002: Simulation runtime
Status: Accepted (2026-11-24)

**Context.** The PoC on the M5 measured TraCI at 3.67 ms/step and libsumo at 0.098 ms/step for a full vehicle and TLS read, so libsumo is 37× faster. libsumo holds one global simulation per process.

**Decision.**
- Each run executes in a dedicated **worker process** (`multiprocessing` spawn) that imports libsumo. A simulation is never shared across requests.
- Headless batch runs (experiments, optimization, RL evaluation) use the same worker, with telemetry disabled.
- A pool of `cpu_count-2` workers sits on top of a SQLite-backed job table. There is no Celery or Redis.
- The `sumo-gui` debug mode uses TraCI. Its only purpose is visual debugging.
- SUMO comes from the pinned PyPI wheels `eclipse-sumo==1.28.0` and `libsumo==1.28.0`. Upgrades need a manifest-diff test.

**Consequences.**
- Crash isolation is built in.
- Cancel works by killing the process.
- Reproducibility depends on a pinned SUMO version, which is recorded in every manifest.
