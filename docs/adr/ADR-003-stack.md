# ADR-003: Technology stack
Status: Accepted (2026-11-24)

| Layer | Choice | Rejected (why) |
|---|---|---|
| Backend | Python 3.12, uv, FastAPI, pydantic v2, sumolib | Django (heavy), Node (SUMO tooling is Python) |
| Jobs | Process pool + SQLite job table | Celery/Redis (extra services on a laptop) |
| Metadata | SQLite (WAL) via SQLModel-free plain `sqlite3` + repository layer | Postgres/PostGIS (no spatial queries needed in MVP; netconvert projects geometry) |
| Artifacts | Content-addressed files under `data/artifacts/`; Parquet for tables | MLflow (manifest + SQLite enough) |
| Analytics | DuckDB over Parquet | pandas-only (memory on 16 GB) |
| Frontend | React 19 + TS + Vite, deck.gl 9 + MapLibre 5, TanStack Query, Zustand | Leaflet (no GPU layers), Cesium/3D (out of MVP) |
| Basemap | OpenFreeMap / MapLibre demo tiles; offline style fallback | Mapbox (license/keys) |
| Charts | Observable Plot or Recharts (decide at Phase 3) | — |
| Tests | pytest, hypothesis, vitest, Playwright (smoke only) | — |

Raw SQL is always parameterized. The service layer sits between routes and storage (user rule).
