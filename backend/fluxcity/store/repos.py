"""Generic repository over the JSON tables. SQL is parameterized; table names are a fixed map."""

import sqlite3

from fluxcity.core import models as m
from fluxcity.core.errors import Conflict, InvalidInput, NotFound

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
            vals.append(obj.content_hash)
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
        if self.model not in (m.Run, m.Scenario):
            raise InvalidInput("immutable", f"{self.table} rows are immutable")
        with self.conn:
            cur = self.conn.execute(
                f"UPDATE {self.table} SET data = ? WHERE id = ?", (_dump(obj), obj.id)
            )
        if cur.rowcount == 0:
            raise NotFound("not_found", f"{self.table} {obj.id} not found")
        return obj
