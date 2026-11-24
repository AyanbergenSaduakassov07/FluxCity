# ADR-008: Optimization
Status: Accepted (2026-11-24)

**Decision.**
- Optuna (MIT) runs all signal and scenario parameter search:
  - TPE for single-objective problems.
  - NSGA-II sampler for 2–3 objectives, such as delay vs emissions vs max queue.
- Each trial is a set of `Run`s over K paired seeds. The objective is the mean of the validity-gated KPI, and invalid runs are pruned with a penalty.
- The study's storage is SQLite (Optuna RDB) in the project DB directory.
- pymoo, OR-Tools and SciPy are deferred until a problem needs them. Example: exact cycle-length optimization, which is SciPy `minimize_scalar` and about 10 lines when needed.

**Budget.** On the M5 with 8 workers, 200 trials × 5 seeds on a corridor is about 1000 runs × 2–5 s each, so roughly 5–10 min.
