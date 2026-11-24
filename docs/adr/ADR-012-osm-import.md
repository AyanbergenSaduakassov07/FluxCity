# ADR-012: OSM import
Status: Accepted (2026-11-24)

**Context.** SUMO `osmGet.py` hung for more than 5 minutes on the PoC bbox. A direct Overpass POST took seconds.

**Decision.**
- Fetch with a direct Overpass POST: a 120 s timeout, a mirror list (overpass-api.de, kumi, mail.ru) and a generic User-Agent. This is extracted from the UrbanFlow multi-mirror fetch (Apache-2.0).
- Cache by `sha256(query)`. The cache records the OSM timestamp and source in the `NetworkSource` provenance.
- Areas above about 25 km², or polygon extracts, use a Geofabrik PBF plus `osmium extract`. This is optional and needs Homebrew osmium.
- The netconvert flag set is SUMO's `osmNetconvert.typ.xml` plus guess-ramps, join-junctions, guess-signals, discard-simple, join-TLS and keep passenger/bus/bicycle. It is merged with UrbanFlow's flags and TLS repair ladder.
- Every import produces a **network quality report**:
  - Share of edges with an imported vs inferred lane count and speed.
  - `turn:lanes` coverage. Astana: 0.
  - Ignored restrictions, the TLS count, disconnected components and netconvert warnings grouped by type.
