# ADR-009: AI engineering copilot
Status: Accepted (2026-11-24)

**Decision.**
- The copilot is an LLM loop over a **typed tool registry**. Each tool has pydantic input and output, a `risk` of `read` | `propose` | `act`, and a description.
  - `read`: query networks, runs, metrics, comparisons; resolve a road name to candidate edges.
  - `propose`: create a draft patch or experiment plan. Drafts have no side effects.
  - `act`: apply a patch to create a version, start runs or experiments, start training. Every `act` call needs **explicit user approval** in the UI, with the diff and the cost estimate shown.
- No shell, filesystem, SQL or web tools. Tools take IDs, never paths. The executor resolves paths under the workspace root and runs SUMO tools as argv lists with timeouts.
- Tool logic is extracted from agentsumo-mcp (MIT). The result envelope and the `pass | review_required | blocked` evidence status follow the ASTRA-SUMO pattern (MIT).
- **Claim verifier.** Every number in the final answer must match a value returned by a tool in the session, within the stated rounding. Unverified answers are regenerated once, then shown with a warning. Answers about Astana must state the provenance (synthetic or uncalibrated).
- OSM names and tags are untrusted data, because they can carry prompt-injection text. Tool results are delimited, and the system prompt forbids following instructions found in data.
- Provider (user decision 2026-11-24: **free APIs**):
  - One OpenAI-compatible client (`openai` SDK, Apache-2.0) with a configurable `base_url` and model.
  - Default: the Google Gemini free tier through its OpenAI-compatible endpoint.
  - Alternative: OpenRouter `:free` models.
  - Keys come from env (`GEMINI_API_KEY` / `OPENROUTER_API_KEY`).
  - The model must support tool calling. The eval set picks the default model.
  - Free tiers are rate-limited and may use prompts for training, so only send run metrics and IDs, never user files.
  - Claude and other providers can be added later by config only.
- Eval gate: at least 30 grounded Q&A cases plus 10 injection cases must pass before release.
