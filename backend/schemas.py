from typing import Literal
from pydantic import BaseModel, Field


Symmetry = Literal["none", "mirror", "four_fold"]


class Confidence(BaseModel):
    tempo: float = Field(ge=0, le=1)
    pitch: float = Field(ge=0, le=1)


class FeatureVector(BaseModel):
    tempo_bpm: float = Field(ge=0)
    cycle_beats: int | None = Field(default=None, ge=1, le=32)
    pitch_range_cents: float = Field(ge=0)
    distinct_pitch_count: int = Field(ge=0)
    gamaka_intensity: float = Field(ge=0, le=1)
    symmetry_score: float = Field(ge=0, le=1)
    confidence: Confidence
    duration_seconds: float = Field(ge=0)
    notes: list[str] = Field(default_factory=list)


class KolamParams(BaseModel):
    grid_size: int = Field(ge=5, le=13)
    symmetry: Symmetry = "mirror"
    turn_density: float = Field(ge=0, le=1)
    seed: int = Field(ge=0, le=4294967295)


class KolamResult(BaseModel):
    grid_size: int
    path: list[list[float]]
    closed: bool
    validated: bool
    svg: str
    validation: dict[str, bool]
    message: str


class GenerateResponse(BaseModel):
    features: FeatureVector
    params: KolamParams
    kolam: KolamResult