# FluxCity: Claude Code

Follow `AGENTS.md` (shared rules). Claude-specific additions:

- **Role.** The Claude main session is the integrator: it owns `core/` contracts, `docs/architecture/*`, the merges and `PROJECT_STATUS.md`. It writes the safety-critical modules (supervisor, copilot executor, claim verifier).
- **Plan state.** `docs/planning/PROJECT_STATUS.md` holds the current phase. Task rows are in `docs/planning/TASK_BACKLOG.md`, and prompts are in `docs/orchestration/PROMPTS.md` (grep `### P<id>`).
- **Decisions.** `docs/adr/README.md` is the index. Read a single ADR only when the task touches it.
- **Large docs.** For `docs/upstream/*.md` audits and `REUSE_MATRIX.md`, `grep -n` for the repo or feature first, then read only that section.
- **Review.** One Opus code-reviewer pass per finished module (`REVIEW_PROTOCOL.md`). Codex output is always reviewed by Claude.
- **Delegation.** Bounded implementation tasks marked X in the backlog go to Codex (`/codex:rescue`) in their own worktree.
- `discovery/` is Phase 0 scratch and is not product code.
