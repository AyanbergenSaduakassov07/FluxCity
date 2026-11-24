# Agentic-SUMO audit for FluxCity AI Engineering Copilot

Verified from source, 2026-11-24. Nothing executed, nothing installed. SUMO tool behaviour (tlsCoordinator, tlsCycleAdaptation, netconvert) is from the wrapper call sites plus SUMO docs, not from SUMO source.

Root: `/Users/ayanbergen/Desktop/Projects/FluxCity/discovery/upstream/`

## 1. Summary verdict

| Repo | Role for us | Verdict |
|---|---|---|
| `agentsumo-mcp-sdist/agentsumo_mcp-0.1.3/agentsumo_mcp` | Best source of SUMO operations | EXTRACT algorithms, WRAP behind our typed registry. Do not expose as MCP to the LLM |
| `kra35-prismx-agentsumo` | Planner agent + web UI | REJECT as code (Claude-only, unsafe web). Take prompt/report ideas only |
| `ASTRA-SUMO` | Contract/evidence patterns + calibration metrics + dev skills | EXTRACT patterns (result envelope, claim tiers, GEH/MAE/RMSE, routeSampler wrapper). Do not depend on it |

Best tool source: agentsumo_mcp (SUMO-generic, MIT, 7.8k LOC, no LLM dependency). Best design source: ASTRA (pydantic Annotated schemas, safety annotations, evidence invariants).

## 2. agentsumo_mcp 0.1.3 (PyPI agentsumo-mcp)

- Path: `agentsumo-mcp-sdist/agentsumo_mcp-0.1.3/agentsumo_mcp/`. 7,796 LOC; `main.py` is 2,026 LOC holding all 26 tool definitions. MIT.
- kra35 copy differs from sdist only in `baseline/osm_http.py` (`diff -rq`). Treat as identical.
- LLM coupling: none. Plain FastMCP stdio (`mcp[cli]>=1.13.1,<2`, `FastMCP("SUMO Baseline")`). Works with any MCP client. Docstrings carry Anthropic-style workflow hints and emoji, Claude-flavoured prompting but not a dependency.
- Deps: sumolib, traci, geopy (Nominatim), geopandas<0.15, shapely, pandas, lxml, matplotlib, ddgs, httpx. Heavy (geopandas pin).
- Schemas: NONE as pydantic. Tool schemas are inferred by FastMCP from bare type hints (`list`, `str = None`); the contract is the docstring. `edge_ids: list`, `coordinates: list`, `additional_files: list` are untyped. Returns are ad hoc `dict` with `status: success|error`, no schema.
- State: tools are stateless functions over file paths; hand-off is by passing the returned path to the next tool. Module-level singletons only. Outputs are timestamped new files (inputs are not edited in place, except the flow/vehicle tools that append to a passed `route_file` by design).
- Path handling: `utils/path_utils.py::get_output_path` accepts any absolute path and `mkdir -p`s it. Input paths (`net_file`, `route_file`, `db_path`, `additional_files`) are never constrained. No traversal guard anywhere.
- Subprocess: all list-argv `subprocess.run/Popen`, no `shell=True`, no `os.system` (grep-verified). Binaries resolved from `SUMO_HOME` (`settings/settings.py`), which can be overridden by a `sumo_home.txt` file next to the package. Flag: macOS default path hardcoded.

### Tool table (26, all in `main.py`)

| # | Tool (main.py line) | Implementation file | Executes | Validation / side effects | Status | FluxCity recommendation |
|---|---|---|---|---|---|---|
| 1 | osm_extract (59) | baseline/osm_extractor.py, osm_http.py | Overpass HTTP (httpx, 4 mirrors) or Geofabrik PBF download, osmium subprocess; geocodes city name | Network egress, writes OSM files; bbox validated | Works, needs network | WRAP (we likely have our own scenario source). Egress must be allowlisted |
| 2 | net_convert (115) | baseline/net_converter.py | `netconvert` argv, options from `NetworkSettings.NETCONVERT_OPTIONS` (removes motorways, passenger only) | Opinionated defaults baked in | Works | WRAP; take option list as reference |
| 3 | trip_generate (146) | baseline/trip_generator.py (354) | `randomTrips.py` via sys.executable | Random OD, seeded (DEFAULT_SEED 42) | Works | EXTRACT only if we need random baseline demand |
| 4 | route_generate (220) | baseline/route_generator.py | `duarouter --ignore-errors` | `--ignore-errors` hides unroutable trips | Works | WRAP; drop `--ignore-errors` or report dropped count |
| 5 | sumo_runner (247) | baseline/simulation_runner.py (705) | `sumo` Popen + TraCI on free port; writes tripinfo, edgedata, emission, summary, replay JSON (position frames every step) | additional_files XML validated (structure + edge/lane IDs). 1-hour default. Writes `.sim_progress.json` | Works. Our engine is authoritative SUMO so we have our own runner | EXTRACT: `_validate_additional_files`, log-error surfacing (`_sumo_errors`), free-port launch. REJECT replay JSON (heavy) |
| 6 | edge_edit_tool (291) | customization/network_editor.py:28 | `netconvert --remove-edges.explicit` | edge_ids checked against net (missing reported). Returns `requires_reroute: True` | Works | EXTRACT as `close_road` patch op. Nice pattern: explicit reroute flag |
| 7 | reduce_lanes_tool (351) | network_editor.py:275 | `netconvert --plain-output-prefix` -> edit .edg.xml numLanes -> rebuild only touched junctions (connections + tlLogic of touched nodes dropped and regenerated) -> netconvert | Needs `reduce_by` XOR `remain_lanes`. Raises error if nothing changed. edge_ids NOT validated against the net. Removes the highest-index `<lane>` children = right-most lanes (may be bus/bike lanes; permissions ignored) | Works, best-engineered tool (touched-node-only rebuild keeps comparison clean) | EXTRACT algorithm; WRAP with pydantic `LaneReductionPatch`; add lane-permission awareness and edge validation |
| 8 | speed_limit_edit_tool (419) | network_editor.py:523 | Pure Python XML: sets `speed` on every `<lane>` of target edges in a copy of the net | km/h to m/s. Does not touch internal junction lanes or connections; no `from/to` speed on junction | Works but crude | EXTRACT; safer to patch via `netconvert --edge-files` plain XML |
| 9 | vehicle_generation_tool (469) | customization/vehicle_manager.py:97 | Geocode (Nominatim) -> nearest edges -> duarouter-like path -> appends `<vehicle>` to route file | Geocoding = network + non-determinism | Works | REJECT geocoding path; EXTRACT nearest-edge logic |
| 10 | flow_generation_tool (545) | vehicle_manager.py:274 | Same, appends `<flow>` (vehsPerHour XOR number; departLane free, departPos random_free). Accepts lat/lon directly | Chain via route_file output | Works | EXTRACT; this is the flow primitive for demand patches. Coordinate mode only |
| 11 | validate_od_coordinates_tool (621) | main.py inline + utils/sumo_utils.py | sumolib spatial lookup | Read-only; bbox + nearest edge | Works | ADOPT logic (read-only, good evidence tool) |
| 12 | vehicle_type_edit_tool (718) | vehicle_manager.py:519 | XML rewrite of vType by `electric_ratio` | ratio unchecked in docstring | Works | EXTRACT if we model EV share |
| 13 | tls_offset_tool (739) | customization/traffic_lights.py:optimize_offsets | `sys.executable $SUMO_HOME/tools/tlsCoordinator.py -n -r -o` | `check=True`; paths unvalidated; output `tls_offset_<ts>.add.xml` | Thin wrapper, works | WRAP (trivial). Keep as additional-file patch |
| 14 | tls_adaptation_tool (758) | traffic_lights.py:optimize_cycles | `tlsCycleAdaptation.py -n -r -o -b 0` (SUMO's Webster-based cycle adaptation, per SUMO docs) | Same; `-b 0` begin time hardcoded | Thin wrapper | WRAP; expose begin/end |
| 15 | xml_to_sqlite_tool (779) | analysis/xml_to_sqlite.py (682) | sqlite3, parameterised queries for ids; table names via f-string from fixed list | Creates DB, replaces simulation_id rows. Tables: simulations, trips, vehicle_info, edge_info, edge_metrics, network_state | Works | EXTRACT schema + importer (good evidence store). Parameterised, no injection seen |
| 16 | simulation_report_tool (925) | main.py:925-1325 (400 inline lines) | Builds HTML string, SVG network | `executive_summary` inserted raw at main.py:1260, no escaping => stored XSS if report is viewed | Works | REJECT as is; EXTRACT KPI queries, render via our React with escaped text |
| 17 | network_summary_tool (1328) | main.py | sumolib: edge/junction counts, length, bbox, road names | Read-only | Works | ADOPT logic |
| 18 | route_analysis_tool (1393) | main.py | duarouter 30 s timeout per query, tempdir, optional weight file (edgedata) | Geocode for place names | Works | EXTRACT (shortest/traveltime route diff before/after is good evidence) |
| 19 | visualize_net_tool (1631) | visualization/network_plotter.py -> sumo_plot.py | `$SUMO_HOME/tools/visualization/plot_net_dump.py` etc via sys.executable, `--blind`, MPLBACKEND=Agg | argv list | Works | REJECT (matplotlib PNG); we render in React/deck |
| 20 | visualize_edge_tool (1650) | edge_plotter.py | same | | Works | REJECT |
| 21 | visualize_policy_target_tool (1673) | edge_plotter.py | same | | Works | REJECT |
| 22 | analyze_road_details_tool (1734) | utils/sumo_utils.py:510,632 | sumolib + geocode | Read-only | Works | EXTRACT road-segment stats |
| 23 | visualize_edgedata_tool (1790) | data_plotter.py | SUMO plot scripts | | Works | REJECT |
| 24 | get_road_names_tool (1866) | utils/sumo_utils.py:465 | `edge.getName()` | Read-only; "Unnamed Road" fallback | Works | ADOPT logic |
| 25 | get_edge_ids_from_road_name_tool (1918) | sumo_utils.py:139 | exact-match on `edge.getName()`; raises ValueError if none | Case/diacritic-sensitive exact match only, no fuzzy | Works | EXTRACT, add normalisation + ambiguity result (return candidates, not silently all) |
| 26 | web_search_tool (1968) | main.py | `ddgs.DDGS().text()`; returns title/url/snippet | Unfiltered third-party text into LLM context | Works | REJECT (prompt-injection surface, violates "evidence-grounded") |

Placeholder/broken: none are stubs. Weak points: (a) `_filter_edges_by_location` (network_editor.py:135-225) on geocode failure or any exception returns ALL edges of the road ("Fallback: return all"), so a failed geocode silently widens a lane reduction/closure from 300 m to the whole road. (b) reduce_lanes / speed edit do not validate edge_ids exist (edge_edit does). (c) `reference_location` parser splits on commas, so "Main St, Seoul" is treated as an intersection query. (d) `simulation_report_tool` is a 400-line inline HTML builder. (e) default SUMO_HOME is a hardcoded macOS 1.24.0 path.

Requested-item checklist:
- lane reduction: tool 7 (best), edge edit: tool 6, speed: tool 8
- tls offset: tool 13 (`tlsCoordinator.py`), tls adaptation: tool 14 (`tlsCycleAdaptation.py`), both pass-through of SUMO scripts
- flow/vehicle generation: tools 9, 10 (+12 types)
- xml_to_sqlite: tool 15, report: tool 16, network_summary: tool 17
- road-name to edge: tools 24, 25 (exact `getName()` match; no fuzzy, no disambiguation)

## 3. kra35-prismx-agentsumo (planner agent + web)

- Commit 22798bf (confirmed). MIT. ~15.4k LOC including tests; the MCP package inside is identical to sdist.
- Layout: `agentsumo/agent/agent_sumo.py` (1,166 LOC; agent loop), `agent/prompts/prompt_builder.py` (504), `client/mcp_client.py` (406), `client/filesystem_mcp_client.py`, `client/sqlite_mcp_client.py`, `core/config.py`, `web/app.py` (1,768; FastAPI + WebSocket `/ws/chat`), `chat.py`, `web.py`, `tests/` (16 files, require local SUMO).
- LLM coupling: Claude-only. `import anthropic`, `anthropic.Anthropic(...)`, default model `claude-sonnet-4-5-20250929`, uses `cache_control: ephemeral`, extended thinking, `max_tokens` 16000. API key from `ANTHROPIC_API_KEY` or legacy `claude_api.txt`. Requires Python 3.12 exactly.
- Agent loop: manual `tool_use` -> `_handle_tool_use` recursion with a depth guard. Tools = MCP tools of agentsumo_mcp + `@modelcontextprotocol/server-filesystem` (via `npx -y`, allowed dirs list) + Anthropic's archived `mcp-server-sqlite` (`read_query`). So the LLM gets raw SQL and filesystem read/write tools. No approval gate, no per-tool policy, no typed registry, no evidence/claim model.
- Web: no auth, no CORS config found, WebSocket chat open. `/api/report/{report_path:path}` (app.py:312) does `output_dir / report_path` and only checks `.suffix == ".html"` and `exists()`: `../` traversal reads any `.html` on disk. `/api/replay/{name}` uses `find_simulation_file`. Not usable as-is.
- Reuse: prompt structure (workflow ordering, "regenerate trips after edge deletion" rule), `PromptBuilder` ideas, dashboard concept (baseline vs policy KPI compare, replay frames). Code: REJECT.

## 4. ASTRA-SUMO

- Commit 946468b. MIT. Python >=3.11. `plugins/astra-sumo/src/astra_sumo`: 316 .py, ~195k LOC (292k with tests; 142 test files). Heavily Hamburg/Ingolstadt corridor-specific (hundreds of `hamburg_*` modules, 119 KB `connection_mode_audit.py`, 119 KB `corridor_edit_ledger.py`). Windows-first (pywin32 for NetEdit GUI session).
- LLM coupling: none in code; product is a Codex plugin (`.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`, `skills/*/agents/openai.yaml`). Model-agnostic MCP (FastMCP, `mcp[cli]<2`) plus an `astra` CLI.
- Schemas: pydantic v2 `Annotated[..., Field(description=...)]` per parameter in `mcp_contract_tools.py`; common `AstraToolResult` envelope; `ToolAnnotations(readOnlyHint, destructiveHint, idempotentHint, openWorldHint)` set per tool in `server.py::_register_tool`. This is exactly the typed-registry pattern we want.
- Profiles: `default` = 10 tools (`astra.preflight`, `config.inspect`, `run.compare`, `place.resolve`, `intersection.classify`, `signal.classify`, `network.audit`, `network.compare`, `demand.audit`, `review.create`), `netedit` = 4 tools (open/observe/act/close; act requires `expected_screenshot_sha256` of the latest observe, a nice stale-state guard), `legacy` = 73 tools. Long/batch work goes through `astra workflow <tool> request.json`, an allowlist.
- Execution: `core/command_runner.py::run_command`: argv list, `stdin=DEVNULL`, timeout, structured `CommandResult` (status pass/fail/timeout). No `shell=True` anywhere in src (grep). Path inputs only checked `is_file()/is_dir()` (digital_twin_tools.py:1206-1225), so no sandbox either; output dirs created anywhere.
- Evidence invariants (AGENTS.md): source artifacts immutable, candidates written separately, decisions `pass | review_required | blocked | not_applicable`, hashes of source/candidate bound to evidence, "SUMO load, route completion, or KPI improvement is not proof of correctness". `core/claim_tiers.py` evaluates gates into three tiers (strict_valid, reference_aligned, manual_quality_reviewed). Directly maps to our "evidence-grounded claims".
- Calibration (actual): `core/detector_demand.py` (1,016 LOC) + `cached_detector_demand.py` (1,308) + `core/route_sampler.py`. Algorithm: parse net, bind detectors to lanes/edges (validated positions), build detector-anchored candidate routes via shortest paths between boundary edges, write routeSampler-format multi-interval edge counts, run SUMO's `routeSampler.py` (found via SUMO_HOME / PATH / sumolib parent), then simulate with E1 detectors and compare. Not a GA/SPSA/gradient calibrator: it is count-constrained route sampling, with explicit statement that routeSampler yields "one detector-constrained plausible realization" (non-identifiability is reported). Metrics (`summarize_comparison`, line 981+): `geh_value = sqrt(2(m-e)^2/(m+e))`, MAE, RMSE, max_abs_error, signed_bias, `GEH_lt5_percent`. Compare is on edge `nVehEntered` vs expected totals. Small enough to extract (about 40 lines for metrics).
- Skills (4, `plugins/astra-sumo/skills/`): astra-build, astra-calibrate, astra-report, astra-simulate (each 37-45 lines SKILL.md + `agents/openai.yaml` + `references/`). astra-simulate references: `mcp-tool-routing.md` (21.8 KB), `plan-experiment.md`, `debug-sumo-traci.md`, `preflight-sumo-environment.md`, `develop-and-verify-code.md`, `audit-sumo-controllers.md`, `sumolights-controller-patterns.md`. Format is Codex plugin; SKILL.md frontmatter (name/description) is compatible with Claude Code skills, `openai.yaml` is Codex-only.
- Reusable for OUR dev workflow: AGENTS.md structure (product boundary, code placement: server.py registers only, tools/ thin, core/ logic; evidence invariants; "when adding an MCP tool: update server, catalog doc, skill routing, contract tests" with a test that checks catalog coverage, `tests/test_repository_navigation.py`), `debug-sumo-traci.md`, `preflight-sumo-environment.md`, `develop-and-verify-code.md`. Copy, rewrite for our stack; do not install the plugin.
- Not reusable: Hamburg/Ingolstadt modules, NetEdit pywin32 GUI automation (Windows only), OCIT/MAP signal formats, 73-tool legacy surface, OSM cleanup tied to their reference-matching.

## 5. Security findings

| ID | Sev | Where | Issue | Mitigation in FluxCity |
|---|---|---|---|---|
| S1 | High | agentsumo_mcp every tool | Arbitrary absolute paths for read (`net_file`, `route_file`, `db_path`, `tripinfo_xml`) and write (`output_dir`, `mkdir -p`) | Registry takes IDs (scenario_id, patch_id, run_id), never paths; resolve server-side under a workspace root, `resolve()` + `is_relative_to` |
| S2 | High | kra35 `web/app.py:312` | Path traversal via `{report_path:path}` (only `.html` suffix + exists) | Reject |
| S3 | High | kra35 agent | LLM gets `server-filesystem` (npx) + raw SQL (`read_query`) | Reject; never hand the model fs/shell/SQL |
| S4 | Med | `simulation_report_tool` main.py:1260 | LLM-authored `executive_summary` interpolated raw into HTML (stored XSS) | Escape/render as text |
| S5 | Med | `web_search_tool` | Third-party snippets in LLM context = indirect prompt injection; also contradicts evidence-grounding | Drop. If research needed, curated allowlisted sources, quoted as untrusted data |
| S6 | Med | geocoding in 6 tools (Nominatim) | Network egress inside edit tools, non-deterministic, and silent widening to whole road on failure (network_editor.py:191, 225) | Resolve places in a separate read-only tool that returns candidates for user confirmation; edits accept edge IDs only |
| S7 | Med | `osm_http.py`, geofabrik | Egress to 4 Overpass mirrors + Geofabrik, large downloads, no size cap noticed | Out of Copilot scope or egress allowlist |
| S8 | Low | tls tools, `sys.executable script` | argv lists, no shell; script path from SUMO_HOME (overridable by `sumo_home.txt`, env) | Pin SUMO_HOME in config, not from files in package dir |
| S9 | Low | subprocess calls | No timeouts except route_analysis (30 s) and plot; sumo_runner can run unbounded | Always set timeouts; ASTRA `run_command` does |
| S10 | Low | kra35 web | No auth, open WebSocket | N/A (reject) |
| S11 | Info | DB | xml_to_sqlite uses parameter binding; f-strings only on fixed table names | OK |
| S12 | Info | ASTRA | Same unrestricted-path property as S1 (only existence checks) | Same fix |

No `shell=True`, `os.system`, `eval`, `exec` in either agentsumo_mcp or ASTRA src (grep). Command injection via argv is not possible except option injection through values beginning with `-` (e.g. net_file="--something"), and netconvert `--remove-edges.explicit` receives a comma-joined string of LLM-supplied IDs (validated against the net in edge_edit only).

## 6. Per-tool decision for FluxCity registry

Legend: ADOPT = pip dependency, WRAP = call upstream function behind our pydantic schema, EXTRACT = copy/adapt code (MIT, keep notice), REJECT.

| FluxCity tool (proposed) | Source | Decision | Reason |
|---|---|---|---|
| patch.road_closure | agentsumo edge_edit (6) | EXTRACT | Keep netconvert `--remove-edges.explicit` and `requires_reroute`; take edge IDs only; emit as versioned patch |
| patch.lane_reduction | agentsumo reduce_lanes (7) | EXTRACT | Touched-node-only rebuild is the value; add permission-aware lane choice and edge validation. Not dependency: 600-line file coupled to geocoding and module singletons |
| patch.speed_limit | agentsumo speed (8) | EXTRACT | Small; do via plain-XML edge attribute to keep junction consistency |
| patch.tls_offset | agentsumo tls_offset (13) | WRAP | Thin call to SUMO's tlsCoordinator.py; ours is a 20-line wrapper with typed args and timeout |
| patch.tls_cycle_adaptation | agentsumo tls_adaptation (14) | WRAP | Same; expose begin/end |
| patch.demand_flow | agentsumo flow_generation (10) | EXTRACT | Lat/lon mode + free-depart safety attrs; drop geocoding |
| patch.vehicle_mix | agentsumo vehicle_type_edit (12) | EXTRACT | Small |
| run.simulate | agentsumo sumo_runner (5) | REJECT (use our engine); EXTRACT `_validate_additional_files` and SUMO-error extraction | We own authoritative run |
| run.route_generate | agentsumo route_generate (4) | WRAP | duarouter argv; remove `--ignore-errors` or count drops |
| evidence.results_to_db | agentsumo xml_to_sqlite (15) | EXTRACT | Schema and importer are good evidence base; add run_id/patch hash columns |
| evidence.network_summary | network_summary (17) | ADOPT-logic (copy) | Read-only sumolib |
| evidence.validate_od | validate_od_coordinates (11) | EXTRACT | Read-only |
| evidence.route_compare | route_analysis (18) | EXTRACT | Before/after path diff |
| resolve.road_name_to_edges | (24,25) | EXTRACT + improve | Exact match only; return ambiguity and per-edge geometry for confirmation |
| resolve.place | geocode (Nominatim) | REJECT | Non-deterministic egress; use our own gazetteer/scenario data |
| report.generate | simulation_report (16) | REJECT | Inline HTML, XSS; render in React from run records |
| viz.* (19,20,21,23) | visualize_* | REJECT | Matplotlib PNG pipelines |
| research.web_search | (26) | REJECT | Prompt-injection, not evidence |
| osm_extract / net_convert / trip_generate | (1,2,3) | WRAP only if we need scenario creation | Out of Copilot MVP |
| metrics.calibration_fit | ASTRA detector_demand `geh_value`, `summarize_comparison` | EXTRACT (about 40 lines) | GEH<5 %, MAE, RMSE, bias |
| calibrate.route_sampling | ASTRA route_sampler.py / detector_demand | EXTRACT later | routeSampler wrapper with count-format validation; heavy, defer |
| contract: result envelope + tool annotations | ASTRA mcp_contract_tools.py, server.py | EXTRACT pattern | Annotated Field schemas, ToolAnnotations, `pass/review_required/blocked/not_applicable` |
| claims: tiered gates | ASTRA claim_tiers.py | EXTRACT pattern | Maps to "evidence-grounded claims" |
| agent loop / web / prompts | kra35 | REJECT | Claude-only, no approval gate, unsafe web |

## 7. Recommended architecture consequence

1. Do not run agentsumo-mcp as the model-facing server. Build our typed registry (pydantic in/out, `risk: read|patch|run`, approval required for anything creating a patch or run) and implement the extracted functions as internal services.
2. Every tool takes IDs, resolves paths under a workspace root, runs argv-list subprocess with timeouts (copy ASTRA `run_command` shape).
3. Patches are versioned artifacts (source net hash + patch spec + output hash) so `requires_reroute` and untouched-junction guarantees become recorded evidence.
4. Claims returned by the Copilot must cite run_id + metric rows (xml_to_sqlite-style tables), with ASTRA-style `pass/review_required/blocked` status; never from web search.
5. Fuzzy/place inputs resolve in a read-only step that returns candidates; edit tools accept only confirmed edge IDs (fixes the silent "all edges" fallback).

## 8. Not verified

- Behaviour of SUMO's own tlsCoordinator.py / tlsCycleAdaptation.py / routeSampler.py (not in repo; relied on call sites and SUMO docs).
- No tests run; agentsumo tests need local SUMO.
- ASTRA: read the contract layer, command runner, detector_demand metrics, skill listing; did not read the ~300 domain modules or the 73 legacy tools individually.
- kra35 agent: structure and Claude coupling verified; prompt text and `web/app.py` routes beyond the report/replay endpoints not audited line by line.
