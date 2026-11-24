# ADR-013: Teleports, unfinished trips, validity gates
Status: Accepted (2026-11-24)

**Decision.**
- Every run records:
  - Teleports by cause (jam, yield, wrong lane).
  - Collisions and emergency braking.
  - `loaded`, `inserted`, `arrived`.
  - Insertion backlog at the end (`waiting`).
  - Total depart delay.
  - Unfinished trips (`loaded − arrived`).
- `--time-to-teleport` defaults to 300 s and is stored in the manifest. Teleports are never disabled silently, and `--ignore-route-errors` is not used by default.
- The **penalized travel time** KPI counts each unfinished trip at (end − depart) plus its depart delay, so gridlock cannot look like an improvement.
- Validity gates. The defaults are configurable per study.

  | Gate | Default | Effect |
  |---|---|---|
  | Teleports | ≤ 0.5% of inserted | warn above 0.1% |
  | Unfinished trips | ≤ 1% after a 30 min drain | — |
  | End backlog | ≤ 1% of loaded | — |
  | Collisions | 0, outside incident scenarios | — |
- These numbers are shown next to every KPI in the UI, reports and copilot answers.
