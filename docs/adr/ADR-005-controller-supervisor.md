# ADR-005: Controller protocol and Signal Safety Supervisor
Status: Accepted (2026-11-24)

**Decision.**
```python
class Controller(Protocol):
    id: str
    def reset(self, tls: TlsStatic, seed: int) -> None: ...
    def decide(self, obs: TlsObservation) -> PhaseRequest  # target green phase index | HOLD
```
- The `SafetySupervisor` sits between controller and libsumo. It is the **only** code that calls `trafficlight.setRedYellowGreenState` or `setPhase` for externally controlled TLS.
- It enforces:
  - Per-phase min green and max green.
  - Yellow and all-red intergreen, built from the G→y→r link transitions.
  - Conflict matrix: no two foe links green. Foes come from the net's junction `<request foes>` data.
  - Transition sequencing.
  - Fallback to the native fixed-time program on controller exception, timeout or NaN.
- Every override is logged as an event, and the counts become a metric.
- Native SUMO programs (static, actuated, delay_based) bypass the supervisor, because SUMO already enforces their phases. A one-time **static validator** checks those programs against the same constraints.
- Constraint values: defaults are ITE-style (yellow = t + v/(2a+2Gg), all-red from clearance width). Per-TLS overrides are allowed, and every value is stored in the manifest.
- Constraints are reimplemented from public formulas and from open_controller *concepts*. open_controller code is EUPL, so none is copied.
- **Scope.** Simulation only. There are no NTCIP, UTMC, OCIT or hardware interfaces, and none will be added (directive restriction).

**Verification.** Hypothesis property tests: random controllers × random nets must give 0 conflicting greens and 0 intergreen or min-green violations.
