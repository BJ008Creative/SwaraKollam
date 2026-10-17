import hashlib
import json
from pathlib import Path

from schemas import KolamParams


CONFIG_PATH = Path(__file__).with_name("config.json")


def clamp(value, low, high):
    return max(low, min(high, float(value)))


def map_features_to_params(features: dict) -> KolamParams:
    with open(CONFIG_PATH, encoding="utf-8") as file:
        config = json.load(file)

    defaults = config["defaults"]
    grid_sizes = config["grid_sizes"]

    pitch_range = features.get(
        "pitch_range_cents", defaults["pitch_range_cents"]
    )
    distinct = features.get(
        "distinct_pitch_count", defaults["distinct_pitch_count"]
    )
    gamaka = clamp(
        features.get("gamaka_intensity", defaults["gamaka_intensity"]),
        0, 1
    )
    symmetry_score = clamp(
        features.get("symmetry_score", defaults["symmetry_score"]),
        0, 1
    )
    tempo = clamp(
        features.get("tempo_bpm", defaults["tempo_bpm"]),
        30, 300
    )

    # More pitch variation and distinct pitches -> larger grid.
    pitch_signal = clamp(pitch_range / 3600, 0, 1)
    distinct_signal = clamp((distinct - 3) / 15, 0, 1)

    complexity = (
        0.55 * pitch_signal
        + 0.45 * distinct_signal
    )

    index = round(complexity * (len(grid_sizes) - 1))
    grid_size = grid_sizes[index]

    thresholds = config["symmetry_thresholds"]

    if symmetry_score >= thresholds["four_fold"]:
        symmetry = "four_fold"
    elif symmetry_score >= thresholds["mirror"]:
        symmetry = "mirror"
    else:
        symmetry = "none"

    # Tempo and estimated gamaka variation control turn density.
    tempo_signal = clamp((tempo - 50) / 200, 0, 1)

    turn_density = clamp(
        0.15 + 0.55 * gamaka + 0.30 * tempo_signal,
        0, 1
    )

    # Stable seed: do not use Python's built-in hash().
    seed_data = {
        "pitch_range": round(pitch_range / 100),
        "distinct": distinct,
        "tempo": round(tempo / 5),
        "gamaka": round(gamaka * 10),
        "symmetry": round(symmetry_score * 10)
    }

    digest = hashlib.sha256(
        json.dumps(seed_data, sort_keys=True).encode()
    ).digest()

    seed = int.from_bytes(digest[:4], "big")

    return KolamParams(
        grid_size=grid_size,
        symmetry=symmetry,
        turn_density=round(turn_density, 4),
        seed=seed
    )