from mapping.mapper import map_features_to_params


def test_mapping_is_deterministic():
    features = {
        "tempo_bpm": 92,
        "cycle_beats": 8,
        "pitch_range_cents": 2400,
        "distinct_pitch_count": 10,
        "gamaka_intensity": 0.63,
        "symmetry_score": 0.71
    }

    first = map_features_to_params(features)
    second = map_features_to_params(features)

    assert first == second


def test_parameters_are_in_range():
    params = map_features_to_params({
        "tempo_bpm": 140,
        "pitch_range_cents": 2000,
        "distinct_pitch_count": 9,
        "gamaka_intensity": 0.4,
        "symmetry_score": 0.6
    })

    assert params.grid_size in [5, 7, 9, 11, 13]
    assert params.symmetry in ["none", "mirror", "four_fold"]
    assert 0 <= params.turn_density <= 1
    assert 0 <= params.seed <= 4294967295