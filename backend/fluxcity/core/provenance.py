"""Where data came from and how far it has been calibrated (drives the UI badge)."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Provenance(StrEnum):
    SYNTHETIC = "synthetic"
    OSM_INFERRED = "osm_inferred"
    CALIBRATED = "calibrated"
    OBSERVED = "observed"


class CalibrationLevel(StrEnum):
    NONE = "none"
    PARTIAL = "partial"
    CALIBRATED = "calibrated"


class CalibrationStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    level: CalibrationLevel = CalibrationLevel.NONE
    geh_pass_pct: float | None = Field(default=None, ge=0, le=100)
    calibrated_on: str | None = None  # ISO date
