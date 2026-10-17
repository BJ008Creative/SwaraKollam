"""FeatureVector -> KolamParams.

A pure, deterministic function: identical features in, identical params out.
All tunable numbers live in ``config.json`` (README section 6), so alternative
mappings can be compared without touching code.  Features whose confidence is
below the configured minimum are replaced by defaults, so unreliable analysis
degrades gracefully instead of steering the kolam with noise.
"""

import hashlib
import json
from functools import lru_cache
from pathlib import Path

from schemas import KolamParams

CONFIG_PATH = Path(__file__).with_name("config.json")


def clamp(value, low, high):
    return max(low, min(high, float(value)))


@lru_cache(maxsize=1)
def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as file:
        return json.load(file)


def _confidence(features: dict, key: str) -> float:
    """Confidence in [0, 1]; a missing value means 'trusted' (direct input)."""
    conf = features.get("confidence")
    if conf is None:
        return 1.0
    value = conf.get(key) if isinstance(conf, dict) else getattr(conf, key, None)
    return 1.0 if value is None else clamp(value, 0, 1)


def _seed(features: dict, used: dict) -> int:
    """Stable seed from the quantised pitch contour (never Python's hash())."""
    signature = features.get("contour_signature")
    if signature:
        payload = {"sig": signature}
    else:
        payload = {
            "pitch_range": round(used["pitch_range"] / 100),
            "distinct": used["distinct"],
        }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).digest()
    return int.from_bytes(digest[:4], "big")


def map_features_to_params(features: dict) -> KolamParams:
    config = load_config()
    defaults = config["defaults"]
    minimum = config["confidence_min"]
    ranges = config["ranges"]

    pitch_ok = _confidence(features, "pitch") >= minimum["pitch"]
    tempo_ok = _confidence(features, "tempo") >= minimum["tempo"]
    cycle_ok = (
        _confidence(features, "cycle") >= minimum["cycle"]
        and features.get("cycle_beats") is not None
    )

    def pick(name: str, reliable: bool):
        value = features.get(name)
        return value if (reliable and value is not None) else defaults[name]

    pitch_range = pick("pitch_range_cents", pitch_ok)
    distinct = pick("distinct_pitch_count", pitch_ok)
    gamaka = clamp(pick("gamaka_intensity", pitch_ok), 0, 1)
    symmetry_score = clamp(pick("symmetry_score", pitch_ok), 0, 1)
    tempo = clamp(pick("tempo_bpm", tempo_ok), 30, 300)
    cycle = features["cycle_beats"] if cycle_ok else defaults["cycle_beats"]

    # Pitch range and distinct-pitch count -> grid size (monotonic, quantised).
    grid_sizes = config["grid_sizes"]
    weights = config["grid_weights"]
    pitch_signal = clamp(pitch_range / ranges["pitch_range_max_cents"], 0, 1)
    d_lo, d_hi = ranges["distinct_min"], ranges["distinct_max"]
    distinct_signal = clamp((distinct - d_lo) / (d_hi - d_lo), 0, 1)
    complexity = (
        weights["pitch_range"] * pitch_signal
        + weights["distinct_pitches"] * distinct_signal
    )
    grid_size = grid_sizes[round(complexity * (len(grid_sizes) - 1))]

    # Phrase symmetry -> symmetry mode (threshold bands).
    thresholds = config["symmetry_thresholds"]
    if symmetry_score >= thresholds["four_fold"]:
        symmetry = "four_fold"
    elif symmetry_score >= thresholds["mirror"]:
        symmetry = "mirror"
    else:
        symmetry = "none"

    # Gamaka (+ tempo) -> turn density; tempo + cycle -> crossing density.
    t_lo, t_hi = ranges["tempo_min"], ranges["tempo_max"]
    tempo_signal = clamp((tempo - t_lo) / (t_hi - t_lo), 0, 1)
    cycle_signal = clamp(cycle / ranges["cycle_max_beats"], 0, 1)

    turn = config["turn_density"]
    turn_density = clamp(
        turn["base"] + turn["gamaka"] * gamaka + turn["tempo"] * tempo_signal, 0, 1
    )
    cross = config["crossing_density"]
    crossing_density = clamp(
        cross["base"] + cross["tempo"] * tempo_signal + cross["cycle"] * cycle_signal,
        0,
        1,
    )

    return KolamParams(
        grid_size=grid_size,
        symmetry=symmetry,
        turn_density=round(turn_density, 4),
        crossing_density=round(crossing_density, 4),
        seed=_seed(features, {"pitch_range": pitch_range, "distinct": distinct}),
    )
