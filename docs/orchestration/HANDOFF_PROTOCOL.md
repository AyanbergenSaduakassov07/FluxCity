# Handoff Protocol

File: `.claude/handoff.md`. It holds the current state only, and finished items move to `PROJECT_STATUS.md`. Each task appends one block:

```
## <task id> — <agent> — <branch> — <status: done|blocked|needs-review>
Changed: <files>
Tests: <command> → <result>
Contract changes requested: <none | description>
Upstream extracted: <none | rows added to UPSTREAM.md>
Next: <one line>
```
- Name the exact doc section a follow-up needs, e.g. `API_CONTRACTS.md §WebSocket`. Never write "read X.md".
- A blocked task states the blocker and the smallest decision needed.
