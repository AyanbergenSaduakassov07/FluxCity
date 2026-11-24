# Integration Plan (worktrees)

- Integrator: the Claude main session on `main` in `~/Desktop/Projects/FluxCity`.
- Each task runs in its own worktree: `git worktree add ../FluxCity-<task> -b agent/<task>`.
- Before creating one, check `git worktree list` and `git branch --list 'agent/*'`.
- One agent per worktree. Parallel tasks must have disjoint owned files (see the backlog dependency column).
- Merge order: contracts first (`core/`, API types), then services, then UI. Merge one branch at a time with `git merge --no-ff`, rerun CI on `main`, update `PROJECT_STATUS.md`, then remove the worktree.
- Contract changes: the agent writes a request into its handoff, and the integrator applies it on `main` first. Dependent branches then rebase.
- Commits use the format `<type>: <description>`. Stage only your own files and never sweep in other WIP.

Parallel lanes for Phase 1–2:
| Lane | Tasks |
|---|---|
| A (Claude) | P1.1 → P1.2 → P1.6 → P2.3 → P2.4 |
| B (Codex) | P1.5 ‖ P1.3 → P1.4 → P2.1 → P2.2 |
| C (Codex) | P2.5 → P2.6 (after P2.3 types exist) |
