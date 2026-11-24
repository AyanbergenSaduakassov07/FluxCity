# FluxCity: agent rules (Codex and Claude)

FluxCity is a SUMO-based platform for traffic simulation, scenarios and optimization. It runs locally on an M5 with 16 GB. Simulation only, with no real-world signal control.

## Before you start
1. Read `.claude/handoff.md` if it exists.
2. Read only the doc sections your task prompt names. Prompts are in `docs/orchestration/PROMPTS.md`.
3. Work in your own worktree: `git worktree add ../FluxCity-<task> -b agent/<task>`. Check `git worktree list` first.

## Hard rules
- SUMO is the only traffic engine. No custom vehicle physics.
- Edit only the owned files in your prompt. Contracts in `backend/fluxcity/core/` and `web/src/api/types.ts` belong to the integrator.
- Licensing (ADR-014):
  - Never copy GPL, AGPL, EUPL or unlicensed code.
  - Extracted MIT/Apache code keeps its header and gets a row in `UPSTREAM.md`.
  - Never add `nets/RESCO`.
- Never expose a shell, arbitrary file paths, raw SQL or web access through API or copilot tools.
- Code:
  - Python: `logging` only, no print, no bare except, no mutable defaults. Parameterized SQL only. Subprocesses are argv lists with timeouts. Functions stay under 50 lines.
  - Never set signal states outside `control/supervisor.py` for externally controlled TLS.
- Metrics always include teleports, unfinished trips and backlog (ADR-013).
- Label Astana outputs synthetic. Never describe them as validated.

## Commands
`uv run pytest -q` · `uv run ruff check` · `uv run mypy backend/fluxcity/core` · `pnpm -C web test` · `uv run python scripts/check_licenses.py`

## Finish
Run tests, commit `<type>: <desc>` (your files only), and append a handoff block per `docs/orchestration/HANDOFF_PROTOCOL.md`.
