"""Generic repository over the JSON tables. SQL is parameterized; table names are a fixed map."""

import sqlite3
from typing import Any

from fluxcity.core import models as m
from fluxcity.core.errors import Conflict, InvalidInput, NotFound
from fluxcity.core.hashing import canonical_json, sha256_bytes

TABLES: dict[type[m.Entity], str] = {
    m.Region: "regions",
    m.NetworkSource: "network_sources",
    m.RoadNetworkVersion: "network_versions",
    m.DemandVersion: "demand_versions",
    m.SignalConfig: "signal_configs",
    m.Patch: "patches",
    m.Scenario: "scenarios",
    m.ScenarioVersion: "scenario_versions",
    m.Run: "runs",
}
MAX_LIMIT = 500
# Fields replace() may change; everything else in a row is history (DOMAIN_MODEL invariant 2).
MUTABLE: dict[type[m.Entity], frozenset[str]] = {
    m.Run: frozenset({"status", "job_id", "started_at", "ended_at", "manifest_sha256"}),
    m.Scenario: frozenset({"name", "description", "head_version_id"}),
}


def _dump(obj: m.Entity) -> str:
    # computed fields (e.g. content_hash) are derived on load; storing them breaks extra=forbid
    return obj.model_dump_json(exclude=set(type(obj).model_computed_fields))


class Repo[T: m.Entity]:
    def __init__(self, conn: sqlite3.Connection, model: type[T]) -> None:
        self.conn = conn
        self.model = model
        self.table = TABLES[model]

    def create(self, obj: T) -> T:
        cols, vals = ["id", "created_at", "data"], [obj.id, obj.created_at.isoformat()]
        vals.append(_dump(obj))
        if isinstance(obj, m.ScenarioVersion):
            cols.append("content_hash")
            vals.append(experiment_hash(self.conn, obj))
        sql = f"INSERT INTO {self.table} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})"
        try:
            with self.conn:
                self.conn.execute(sql, vals)
        except sqlite3.IntegrityError as e:
            raise Conflict("duplicate_id", f"{self.table} {obj.id} exists") from e
        return obj

    def get(self, id_: str) -> T:
        row = self.conn.execute(f"SELECT data FROM {self.table} WHERE id = ?", (id_,)).fetchone()
        if row is None:
            raise NotFound("not_found", f"{self.table} {id_} not found")
        return self.model.model_validate_json(row[0])

    def list(self, cursor: str | None = None, limit: int = 50) -> tuple[list[T], str | None]:
        """Keyset pagination by id (ULIDs sort by creation time). Returns (items, next_cursor)."""
        if not 1 <= limit <= MAX_LIMIT:
            raise InvalidInput("bad_limit", f"limit must be 1..{MAX_LIMIT}")
        rows = self.conn.execute(
            f"SELECT data FROM {self.table} WHERE id > ? ORDER BY id LIMIT ?",
            (cursor or "", limit + 1),
        ).fetchall()
        items = [self.model.model_validate_json(r[0]) for r in rows[:limit]]
        return items, (items[-1].id if len(rows) > limit else None)

    def replace(self, obj: T) -> T:
        """Only for mutable pointers (run status, scenario head). Versions stay immutable."""
        allowed = MUTABLE.get(self.model)
        if allowed is None:
            raise InvalidInput("immutable", f"{self.table} rows are immutable")
        old = self.get(obj.id).model_dump()
        changed = {k for k, v in obj.model_dump().items() if old[k] != v}
        if changed - allowed:
            raise InvalidInput("immutable_field", f"cannot change {sorted(changed - allowed)}")
        with self.conn:
            self.conn.execute(
                f"UPDATE {self.table} SET data = ? WHERE id = ?", (_dump(obj), obj.id)
            )
        return obj

    def content_hash(self, id_: str) -> str:
        """Experiment hash of a stored ScenarioVersion."""
        row = self.conn.execute(
            "SELECT content_hash FROM scenario_versions WHERE id = ?", (id_,)
        ).fetchone()
        if row is None:
            raise NotFound("not_found", f"scenario_versions {id_} not found")
        return str(row[0])


def experiment_hash(conn: sqlite3.Connection, sv: m.ScenarioVersion) -> str:
    """Hash of what the simulation actually consumes: artifact sha256s + params, never row ids.

    Two versions that reference identical artifacts, demand params, patches and config hash equal.
    """
    net = Repo(conn, m.RoadNetworkVersion).get(sv.network_version_id)
    dem = Repo(conn, m.DemandVersion).get(sv.demand_version_id)
    sig = Repo(conn, m.SignalConfig).get(sv.signal_config_id) if sv.signal_config_id else None
    patches = [Repo(conn, m.Patch).get(pid) for pid in sv.patch_ids]
    payload: dict[str, Any] = {
        "net": net.net_sha256,
        "demand": dem.model_dump(
            mode="json", include={"method", "params", "seed", "routes_sha256", "period_s"}
        ),
        "signals": sig.model_dump(mode="json", include={"programs_sha256"}) if sig else None,
        "patches": [
            p.model_dump(mode="json", include={"op", "params", "target_ids"}) for p in patches
        ],
        "controllers": [c.model_dump(mode="json") for c in sv.controllers],
        "sim": sv.sim_config.model_dump(mode="json"),
    }
    return sha256_bytes(canonical_json(payload))
