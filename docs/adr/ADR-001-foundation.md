# ADR-001: New repository, module harvesting, no application fork
Status: Accepted (2026-11-24)

**Context.** The directive asks us to first reuse a complete application. Source inspection (`docs/upstream/`) found:
- TrafficTwin (Apache-2.0, 4/10): Jeddah is hardwired in 44 paths. It has no live simulation, no controllers and no LLM. About 23k LOC is city-specific.
- UrbanFlow AI (Apache-2.0, 3/10): its "AI" is a fixed-weight heuristic. It runs one global TraCI session from a 2.7k-line god class and does not count teleports.
- FlowState: best architecture, but unlicensed.
- websumo: EUPL-1.2, and only a viewer.

**Decision.** Start a new `FluxCity` monorepo and extract permissively licensed modules file by file (see `docs/dependencies/REUSE_MATRIX.md`). Each extracted file keeps its upstream header and gets an entry in `UPSTREAM.md`.

**Alternatives.**
- Fork TrafficTwin: rejected. We would delete more than we keep, and live sim, controllers, RL, copilot and patches would still be new code.
- Fork UrbanFlow: rejected, because the core engine has to be rewritten anyway.
- Compose separate apps: rejected for incompatible frameworks and run models.

**Consequences.**
- Greenfield structure, with CI and tests from day 1.
- About 3–5k LOC is harvested (viewer engine, run registry, metrics parsing, calibration, netconvert flags, agentsumo tool logic).
- Reuse is less than "one app", but the license stays clean.
