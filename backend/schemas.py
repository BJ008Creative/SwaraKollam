from typing import Literal

from pydantic import BaseModel, Field, field_validator

Symmetry = Literal["none", "mirror", "four_fold"]


class Confidence(BaseModel):
    tempo: float = Field(ge=0, le=1)
    pitch: float = Field(ge=0, le=1)
    cycle: float = Field(default=0.0, ge=0, le=1)


class FeatureVector(BaseModel):
    tempo_bpm: float = Field(ge=0)
    cycle_beats: int | None = Field(default=None, ge=1, le=32)
    pitch_range_cents: float = Field(ge=0)
    distinct_pitch_count: int = Field(ge=0, le=12)
    gamaka_intensity: float = Field(ge=0, le=1)
    symmetry_score: float = Field(ge=0, le=1)
    confidence: Confidence
    duration_seconds: float = Field(ge=0)
    # Quantised, tonic-relative pitch-class histogram; feeds the generator seed.
    contour_signature: str | None = None
    notes: list[str] = Field(default_factory=list)


class KolamParams(BaseModel):
    grid_size: int = Field(ge=5, le=13)
    symmetry: Symmetry = "mirror"
    turn_density: float = Field(ge=0, le=1)
    crossing_density: float = Field(default=0.5, ge=0, le=1)
    seed: int = Field(ge=0, le=4294967295)

    @field_validator("grid_size")
    @classmethod
    def grid_size_must_be_odd(cls, value: int) -> int:
        # README: "Grid size n (odd, bounded)".
        if value % 2 == 0:
            raise ValueError("grid_size must be odd")
        return value


class KolamResult(BaseModel):
    grid_size: int
    # Ordered lattice coordinates in pulli units: pullis are at integer
    # (x, y) in 0..grid_size-1, y pointing up.  Crossings and bounces are at
    # half-integers; the first point is repeated at the end to close the curve.
    path: list[list[float]]
    closed: bool
    validated: bool
    svg: str
    curve_path: str  # smoothed SVG path data in the 600x600 canvas
    validation: dict[str, bool]
    symmetry_requested: Symmetry
    symmetry_applied: Symmetry
    attempts: int
    repairs: int
    message: str


class GenerateResponse(BaseModel):
    features: FeatureVector
    params: KolamParams
    kolam: KolamResult
