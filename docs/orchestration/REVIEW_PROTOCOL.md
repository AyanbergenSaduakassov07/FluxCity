# Review Protocol

1. The agent runs the task's tests plus `uv run ruff check`, `uv run mypy backend/fluxcity/core`, `uv run pytest -q`, and `pnpm -C web test` when web code changed.
2. Each finished task or module gets one **code-reviewer (Opus)** pass, with the task prompt as the brief. python-reviewer or typescript-reviewer (Sonnet) runs in parallel. Reviews never happen per edit.
3. Supervisor, copilot executor, subprocess handling and API input validation also get a **security-reviewer** pass.
4. Codex output is always reviewed by Claude, never by Codex.
5. Merge requires green CI, findings fixed or explicitly deferred with a `shortcut:` comment, and the handoff block written.
6. Escalate one model tier after two failed attempts at a task.
