# ADR-014: Licensing policy
Status: Accepted (2026-11-24)

| Class | Licenses | Allowed use |
|---|---|---|
| Permissive | MIT, BSD, Apache-2.0, ISC, PSF | dependency, extract with header + `UPSTREAM.md` entry |
| Weak copyleft (file) | EPL-2.0 (SUMO), MPL-2.0 | dependency / subprocess unmodified; modifications to those files stay EPL |
| Copyleft | GPL-3, AGPL (ultralytics), EUPL-1.2 (websumo, open_controller) | **reference only**: read concepts, never copy; no linking. Separate-process optional tools only after a legal check |
| Unlicensed | flow_state, LibSignal, smart-traffic-rl | reference only |
| Non-commercial data | RESCO nets (CC BY-NC-*) | forbidden in repo |
| Data | OSM (ODbL) | attribution in UI + reports; derived nets are Produced Works |

**FluxCity license: Apache-2.0** (recommended). It is compatible with every extract (Apache and MIT) and grants a patent license.

**CI gate.**
- `scripts/check_licenses.py` fails when a dependency is not on the allow-list.
- It fails when an `extracted/` file has no `UPSTREAM.md` entry.
- It fails on any path matching `nets/RESCO`.
