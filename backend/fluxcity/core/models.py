"""Domain models (docs/architecture/DOMAIN_MODEL.md). Integrator-owned contract.

All models are frozen: "changing" one means creating a new object (model_copy) or a new version.
Copilot, RL and optimization entities are added in their phases.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, computed_field, model_validator

from fluxcity.core.hashing import SHA256_RE
from fluxcity.core.ids import is_id, new_id
from fluxcity.core.provenance import CalibrationStatus, Provenance


def _check_id(value: str) -> str:
    if not is_id(value):
        raise ValueError(f"not a ULID: {value!r}")
    return value


def _check_sha(value: str) -> str:
    if not SHA256_RE.match(value):
        raise ValueError(f"not a sha256 hex digest: {value!r}")
    return value


Id = Annotated[str, AfterValidator(_check_id)]
Sha256 = Annotated[str, AfterValidator(_check_sha)]


def _now() -> datetime:
    return datetime.now(UTC)


class Entity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: Id = Field(default_factory=new_id)
    created_at: datetime = Field(default_factory=_now)


class BBox(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    west: float = Field(ge=-180, le=180)
    south: float = Field(ge=-90, le=90)
    east: float = Field(ge=-180, le=180)
    north: float = Field(ge=-90, le=90)

    @model_validator(mode="after")
    def _ordered(self) -> "BBox":
        if self.west >= self.east or self.south >= self.north:
            raise ValueError("bbox must have west < east and south < north")
        return self


# --- enums -----------------------------------------------------------------


class SourceKind(StrEnum):
    OVERPASS = "overpass"
    PBF = "pbf"
    FILE = "file"
    NETGENERATE = "netgenerate"


class DemandMethod(StrEnum):
    RANDOM = "random"
    OD = "od"
    ROUTE_SAMPLER = "route_sampler"
    GA = "ga"


class SignalSource(StrEnum):
    NETCONVERT = "netconvert"
    WEBSTER = "webster"
    GREENWAVE = "greenwave"
    MANUAL = "manual"
    OPTIMIZED = "optimized"


class ControllerKind(StrEnum):
    NATIVE_STATIC = "native_static"
    ACTUATED = "actuated"
    DELAY_BASED = "delay_based"
    MAX_PRESSURE = "max_pressure"
    QUEUE = "queue"
    RL = "rl"


class PatchOp(StrEnum):
    CLOSE_EDGE = "close_edge"
    REDUCE_LANES = "reduce_lanes"
    SET_SPEED = "set_speed"
    ADD_BUS_LANE = "add_bus_lane"
    SET_TLS_PROGRAM = "set_tls_program"
    SET_TLS_OFFSETS = "set_tls_offsets"
    SCALE_DEMAND = "scale_demand"
    ADD_INCIDENT = "add_incident"
    VEHICLE_MIX = "vehicle_mix"
    MANUAL_EDIT = "manual_edit"


class RunMode(StrEnum):
    LIVE = "live"
    HEADLESS = "headless"


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INVALID = "invalid"  # completed but failed a validity gate (ADR-013)


# --- network, demand, signals -------------------------------------------------


class Region(Entity):
    name: str = Field(min_length=1, max_length=120)
    country: str = Field(min_length=2, max_length=2)  # ISO 3166-1 alpha-2
    origin_lon: float = Field(ge=-180, le=180)
    origin_lat: float = Field(ge=-90, le=90)


class NetworkSource(Entity):
    region_id: Id
    kind: SourceKind
    bbox: BBox | None = None
    query: str | None = None
    fetched_at: datetime | None = None
    osm_timestamp: str | None = None
    sha256: Sha256


class RoadNetworkVersion(Entity):
    source_id: Id
    parent_id: Id | None = None
    net_sha256: Sha256
    plain_xml_sha256: Sha256 | None = None
    netconvert_args: tuple[str, ...] = ()
    sumo_version: str
    quality_report: dict[str, Any] = Field(default_factory=dict)
    provenance: Provenance = Provenance.OSM_INFERRED


class DemandVersion(Entity):
    network_version_id: Id
    method: DemandMethod
    params: dict[str, Any] = Field(default_factory=dict)
    seed: int = Field(ge=0)
    routes_sha256: Sha256
    period_s: float = Field(gt=0)
    provenance: Provenance = Provenance.SYNTHETIC
    calibration: CalibrationStatus = Field(default_factory=CalibrationStatus)


class SignalConfig(Entity):
    network_version_id: Id
    programs_sha256: Sha256 | None = None  # None = programs embedded in the net
    source: SignalSource = SignalSource.NETCONVERT


class ControllerSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: ControllerKind
    tls_ids: tuple[str, ...]
    params: dict[str, Any] = Field(default_factory=dict)
    policy_sha256: Sha256 | None = None

    @model_validator(mode="after")
    def _rl_needs_policy(self) -> "ControllerSpec":
        if self.kind is ControllerKind.RL and self.policy_sha256 is None:
            raise ValueError("rl controller requires policy_sha256")
        return self


class SimConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    begin_s: float = Field(default=0, ge=0)
    end_s: float = Field(default=3600, gt=0)
    warmup_s: float = Field(default=900, ge=0)
    drain_s: float = Field(default=1800, ge=0)
    step_length_s: float = Field(default=1.0, gt=0, le=5)
    time_to_teleport_s: float = Field(default=300, ge=-1)  # -1 disables; recorded, never silent
    extra_args: tuple[str, ...] = ()  # checked against the sumocfg builder's allow-list (P1.3)

    @model_validator(mode="after")
    def _window(self) -> "SimConfig":
        if self.end_s <= self.begin_s + self.warmup_s:
            raise ValueError("end_s must exceed begin_s + warmup_s")
        return self


# --- scenarios -----------------------------------------------------------------


class Patch(Entity):
    op: PatchOp
    params: dict[str, Any] = Field(default_factory=dict)
    target_ids: tuple[str, ...] = ()
    created_by: str = "user"  # "user" | "copilot"
    approved_by: str | None = None


class Scenario(Entity):
    region_id: Id
    name: str = Field(min_length=1, max_length=120)
    description: str = ""
    head_version_id: Id | None = None


class ScenarioVersion(Entity):
    scenario_id: Id
    parent_id: Id | None = None
    network_version_id: Id
    demand_version_id: Id
    signal_config_id: Id | None = None
    controllers: tuple[ControllerSpec, ...] = ()
    sim_config: SimConfig = Field(default_factory=SimConfig)
    patch_ids: tuple[Id, ...] = ()
    # The experiment content hash needs the referenced artifacts' sha256s, so the store
    # computes it on insert (store.repos.experiment_hash), not the model.


# --- runs ----------------------------------------------------------------------


class Kpis(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    mean_travel_time_s: float | None
    penalized_travel_time_s: float | None
    mean_time_loss_s: float | None
    mean_waiting_time_s: float | None
    throughput_veh_h: float
    loaded: int = Field(ge=0)
    inserted: int = Field(ge=0)
    arrived: int = Field(ge=0)
    unfinished: int = Field(ge=0)
    backlog_end: int = Field(ge=0)
    total_depart_delay_s: float = Field(ge=0)
    teleports: dict[str, int] = Field(default_factory=dict)  # by cause
    collisions: int = Field(default=0, ge=0)
    emergency_stops: int = Field(default=0, ge=0)


class GateResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    value: float
    limit: float
    passed: bool


class Validity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    gates: tuple[GateResult, ...]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def passed(self) -> bool:
        return all(g.passed for g in self.gates)


class RunManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: Id
    scenario_version_hash: Sha256
    inputs: dict[str, Sha256]  # role -> artifact hash (net, routes, additional, ...)
    seed: int = Field(ge=0)
    sumo_version: str
    fluxcity_version: str
    git_sha: str | None
    git_dirty: bool | None
    sumo_args: tuple[str, ...]
    platform: str
    python: str
    wall_s: float | None = None


class Run(Entity):
    scenario_version_id: Id
    seed: int = Field(ge=0)
    mode: RunMode = RunMode.HEADLESS
    status: RunStatus = RunStatus.QUEUED
    job_id: Id | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    manifest_sha256: Sha256 | None = None


class RunResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: Id
    kpis: Kpis
    validity: Validity
    artifacts: dict[str, Sha256]  # e.g. "tripinfo.parquet" -> hash
