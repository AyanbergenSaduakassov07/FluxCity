import sqlite3
from pathlib import Path

import pytest
from pydantic import ValidationError

from fluxcity.core import models as m
from fluxcity.core.errors import Conflict, InvalidInput, NotFound
from fluxcity.core.hashing import canonical_json
from fluxcity.core.ids import is_id, new_id
from fluxcity.store.artifacts import ArtifactStore
from fluxcity.store.db import connect
from fluxcity.store.repos import Repo

SHA = "a" * 64


@pytest.fixture
def conn() -> sqlite3.Connection:
    return connect(":memory:")


def _version(**kw: object) -> m.ScenarioVersion:
    base: dict[str, object] = dict(
        scenario_id=new_id(), network_version_id=new_id(), demand_version_id=new_id()
    )
    return m.ScenarioVersion.model_validate(base | kw)


def test_ids_are_ulids_and_sortable() -> None:
    a, b = new_id(), new_id()
    assert is_id(a) and is_id(b) and len(a) == 26


def test_canonical_json_ignores_key_order() -> None:
    assert canonical_json({"b": 1, "a": [1, {"y": 2, "x": 3}]}) == canonical_json(
        {"a": [1, {"x": 3, "y": 2}], "b": 1}
    )


def test_content_hash_ignores_identity_but_tracks_inputs() -> None:
    v1 = _version(network_version_id=(net := new_id()), demand_version_id=(dem := new_id()))
    v2 = _version(network_version_id=net, demand_version_id=dem)  # other id/scenario/time
    assert v1.content_hash == v2.content_hash
    v3 = v1.model_copy(update={"sim_config": m.SimConfig(end_s=7200)})
    assert v3.content_hash != v1.content_hash


def test_models_are_frozen_and_strict() -> None:
    region = m.Region(name="Astana", country="KZ", origin_lon=71.4, origin_lat=51.1)
    with pytest.raises(ValidationError):
        region.name = "x"
    with pytest.raises(ValidationError):
        m.Region(name="A", country="KZ", origin_lon=0, origin_lat=0, extra=1)  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        m.BBox(west=2, south=0, east=1, north=1)
    with pytest.raises(ValidationError):
        m.ControllerSpec(kind=m.ControllerKind.RL, tls_ids=("j1",))


def test_validity_passed_only_when_all_gates_pass() -> None:
    ok = m.GateResult(name="teleport_pct", value=0.1, limit=1, passed=True)
    bad = m.GateResult(name="backlog", value=9, limit=1, passed=False)
    assert m.Validity(gates=(ok,)).passed and not m.Validity(gates=(ok, bad)).passed


def test_repo_round_trip_and_pagination(conn: sqlite3.Connection) -> None:
    repo = Repo(conn, m.Region)
    made = [
        repo.create(m.Region(name=f"r{i}", country="KZ", origin_lon=0, origin_lat=0))
        for i in range(5)
    ]
    assert repo.get(made[0].id) == made[0]
    page1, cur = repo.list(limit=3)
    page2, end = repo.list(cursor=cur, limit=3)
    assert [r.id for r in page1 + page2] == sorted(r.id for r in made) and end is None
    with pytest.raises(Conflict):
        repo.create(made[0])
    with pytest.raises(NotFound):
        repo.get(new_id())


def test_versions_are_immutable_in_repo(conn: sqlite3.Connection) -> None:
    repo = Repo(conn, m.ScenarioVersion)
    v = repo.create(_version())
    assert repo.get(v.id).content_hash == v.content_hash
    with pytest.raises(InvalidInput):
        repo.replace(v)


def test_run_status_can_advance(conn: sqlite3.Connection) -> None:
    repo = Repo(conn, m.Run)
    run = repo.create(m.Run(scenario_version_id=new_id(), seed=1))
    repo.replace(run.model_copy(update={"status": m.RunStatus.COMPLETED}))
    assert repo.get(run.id).status is m.RunStatus.COMPLETED


def test_artifact_store_dedupes_and_round_trips(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path / "a")
    src = tmp_path / "net.xml"
    src.write_bytes(b"<net/>")
    sha = store.put(src)
    assert store.put(b"<net/>") == sha
    assert store.path(sha).read_bytes() == b"<net/>"
    assert not list((tmp_path / "a").glob(".tmp-*"))


@pytest.mark.parametrize("bad", ["../../etc/passwd", "/etc/passwd", "A" * 64, SHA[:-1]])
def test_artifact_store_rejects_traversal(tmp_path: Path, bad: str) -> None:
    with pytest.raises(InvalidInput):
        ArtifactStore(tmp_path).path(bad)


def test_missing_artifact(tmp_path: Path) -> None:
    with pytest.raises(NotFound):
        ArtifactStore(tmp_path).path(SHA)
