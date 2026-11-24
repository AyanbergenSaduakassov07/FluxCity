-- One table per entity; the frozen pydantic model is stored as canonical JSON.
-- Rows are never updated except runs.status/timestamps and scenarios.head_version_id.
CREATE TABLE IF NOT EXISTS regions            (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS network_sources    (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS network_versions   (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS demand_versions    (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS signal_configs     (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS patches            (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS scenarios          (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS scenario_versions  (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, data TEXT NOT NULL,
                                               content_hash TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_sv_hash ON scenario_versions(content_hash);
CREATE TABLE IF NOT EXISTS runs               (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, data TEXT NOT NULL);
