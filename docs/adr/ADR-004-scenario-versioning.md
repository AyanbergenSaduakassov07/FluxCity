# ADR-004: Scenario versioning and patches
Status: Accepted (2026-11-24)

**Decision.**
- Every input is an immutable artifact identified by SHA-256: network, demand, signal programs, additional files and sim config.
- A `ScenarioVersion` is a tuple (network version, demand version, signal config, controller assignment, sim config) plus its parent. It is never edited in place.
- Network patches are **typed operations**: `close_edge`, `reduce_lanes`, `set_speed`, `add_bus_lane`, `set_tls_program`, `scale_demand`, `add_incident`, `vehicle_mix`.
- Patches are applied to netconvert **plain XML** (`--plain-output-prefix`), then rebuilt with `netconvert`. TLS-only and demand-only patches skip the rebuild.
- Netedit edits are an external round-trip: export plain XML, edit in Netedit, re-import. The result is a new version whose patch is `manual_edit` with the diff hash.
- Patch logic comes from agentsumo edge_edit, reduce_lanes and speed (MIT), re-typed with pydantic. Edge IDs are validated, and fuzzy names are never accepted.

**Alternatives.**
- TraCI runtime edits only (UrbanFlow style). Rejected: they are not persistent or reproducible, and they cannot change geometry.
- A database diff model. Rejected as over-engineered.

**Consequences.**
- Any run can be reproduced from its manifest.
- Side-by-side comparison is version against version, with an explicit diff.
