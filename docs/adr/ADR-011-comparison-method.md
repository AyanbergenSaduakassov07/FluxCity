# ADR-011: Comparison methodology
Status: Accepted (2026-11-24)

**Decision.**
- Arms are compared on **paired seeds**: the same demand seed and the same SUMO `--seed` per pair.
- Default replications: N = 10 for reports and N = 3 for quick looks. Quick-look results are labelled "indicative".
- Warm-up: KPIs use trips that depart in the measurement window. The warm-up defaults to 900 s, or one cycle multiple for a single intersection.
- Estimate: the mean of per-seed differences, with a 95% CI (t-interval; bootstrap when N ≥ 20). Show the absolute value, the % change and the CI.
- "No significant difference" is shown as such. We never claim an improvement when the CI crosses 0.
- An arm that fails a validity gate (ADR-013) is never ranked. The comparison shows **INVALID** with the reason.
- Definitions are in `docs/methodology/METHODOLOGY.md`.
