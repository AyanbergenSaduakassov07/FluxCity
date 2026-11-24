# Agent Ownership

| Area | Owner | Others may |
|---|---|---|
| `backend/fluxcity/core/` (models, manifest, hashing), `docs/architecture/*`, `web/src/api/types.ts` (generated) | **Integrator (Claude main session)** | propose changes through a contract-change request in the handoff |
| `control/supervisor.py`, `control/static_validator.py` | Claude | read |
| `copilot/` | Claude | Codex: UI only |
| `metrics/compare.py`, methodology | Claude | read |
| `sim/`, `metrics/` parsers, `jobs/`, `network/`, `demand/`, `scenario/patches/`, `control/controllers/`, `optimize/`, `rl/` | Codex (per task prompt) | Claude reviews |
| `web/src/**` except generated types | Codex | Claude reviews |
| `docs/planning/PROJECT_STATUS.md`, `UPSTREAM.md`, `THIRD_PARTY_NOTICES.md`, `REUSE_MATRIX.md` | Integrator | agents append rows in their branch |

Rules:
- Each task prompt lists **owned files**. An agent edits only those, plus tests under the matching `tests/` path.
- Codex never reviews or merges its own output.
- Safety-critical modules (supervisor, claim verifier, executor path and argv handling) are written by Claude and reviewed by Opus plus the security-reviewer.
