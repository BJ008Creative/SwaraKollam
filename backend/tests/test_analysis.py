"""Feature maths on synthetic signals with known answers (numpy only)."""

import numpy as np

from audio import analysis as A

FPS = 22050 / 512
SA = 1200 * np.log2(200 / 55)  # a 200 Hz tonic on the cents scale


def contour(seed=0, seconds=30):
    rng = np.random.default_rng(seed)
    n = int(seconds * FPS)
    return rng, n, np.arange(n) / FPS


def test_tonic_is_recovered_and_stats_are_transposition_invariant():
    rng, n, _ = contour()
    notes = np.repeat(rng.choice([0, 200, 400, 700, 900, 1200], size=n // 30 + 1), 30)[:n]
    notes[:200] = 0
    notes[400:700] = 0
    cents = SA + notes + rng.normal(0, 2, n)
    assert abs(A.estimate_tonic(cents) - (SA % 1200)) < 15
    stats = A.pitch_statistics(cents)
    shifted = A.pitch_statistics(cents + 700)
    assert 1100 < stats["pitch_range_cents"] < 1300
    assert stats["distinct_pitch_count"] == 5
    for key in ("pitch_range_cents", "distinct_pitch_count", "contour_signature"):
        assert stats[key] == shifted[key]


def test_gamaka_separates_steady_from_ornamented_and_ignores_gaps():
    rng, n, t = contour()
    steady = SA + np.repeat([0, 200, 400, 200], n // 4 + 1)[:n] + rng.normal(0, 2, n)
    vibrato = steady + 45 * np.sin(2 * np.pi * 6 * t)
    gappy = steady.copy()
    gappy[::40] = np.nan
    for i in range(0, n - 30, 200):
        gappy[i : i + 25] = np.nan
    assert A.gamaka_intensity(steady, FPS) < 0.15
    assert A.gamaka_intensity(vibrato, FPS) > 0.6
    # Gaps in the contour must not be mistaken for ornamentation.
    assert A.gamaka_intensity(gappy, FPS) < 0.15


def test_symmetry_separates_structured_from_unstructured_contours():
    structured, unstructured = [], []
    for seed in range(6):
        rng, n, _ = contour(seed)
        phrase = np.cumsum(rng.normal(0, 60, int(4 * FPS)))
        half = np.cumsum(rng.normal(0, 60, int(15 * FPS)))
        structured.append(A.symmetry_score(np.tile(phrase, 8)[:n] + SA, FPS))
        structured.append(
            A.symmetry_score(np.concatenate([half, half[::-1]])[:n] + SA, FPS)
        )
        held = np.repeat(rng.normal(0, 300, n // 20 + 1), 20)[:n]
        unstructured.append(A.symmetry_score(held + SA, FPS))
    assert min(structured) > 0.75
    assert np.mean(unstructured) < 0.4
    assert A.symmetry_score(np.zeros(50), FPS) == 0.0  # too short


def test_cycle_and_tempo_confidence_on_an_accented_pulse():
    rng, n, _ = contour()
    beat = FPS * 60 / 120
    for period, expected in ((8, 8), (4, 4)):
        env = np.zeros(n)
        for k in range(int(n / beat)):
            env[int(round(k * beat))] = 1.0 if k % period == 0 else 0.3
        env = np.convolve(env, np.hanning(5), "same") + rng.normal(0, 0.01, n)
        cycle, confidence = A.estimate_cycle(env, FPS, 120)
        assert cycle == expected and confidence > 0.3
        assert A.tempo_confidence(env, FPS, 120) > 0.3
        assert A.tempo_confidence(env, FPS, 97) < 0.15  # wrong tempo


def test_no_cycle_is_reported_for_noise():
    rng, n, _ = contour()
    cycle, _ = A.estimate_cycle(rng.normal(0, 1, n), FPS, 120)
    assert cycle is None
