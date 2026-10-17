from mapping.mapper import map_features_to_params

FEATURES = {
    "tempo_bpm": 92,
    "cycle_beats": 8,
    "pitch_range_cents": 2400,
    "distinct_pitch_count": 10,
    "gamaka_intensity": 0.63,
    "symmetry_score": 0.71,
}


def test_mapping_is_deterministic():
    assert map_features_to_params(FEATURES) == map_features_to_params(FEATURES)


def test_parameters_are_in_range():
    params = map_features_to_params(
        {
            "tempo_bpm": 140,
            "pitch_range_cents": 2000,
            "distinct_pitch_count": 9,
            "gamaka_intensity": 0.4,
            "symmetry_score": 0.6,
        }
    )
    assert params.grid_size in [5, 7, 9, 11, 13]
    assert params.symmetry in ["none", "mirror", "four_fold"]
    assert 0 <= params.turn_density <= 1
    assert 0 <= params.crossing_density <= 1
    assert 0 <= params.seed <= 4294967295


def test_grid_size_is_monotonic_in_pitch_range():
    sizes = []
    for cents in range(0, 4000, 200):
        features = dict(FEATURES, pitch_range_cents=cents, distinct_pitch_count=7)
        sizes.append(map_features_to_params(features).grid_size)
    assert sizes == sorted(sizes)
    assert sizes[0] < sizes[-1]


def test_turn_density_is_monotonic_in_gamaka():
    values = [
        map_features_to_params(dict(FEATURES, gamaka_intensity=g / 10)).turn_density
        for g in range(11)
    ]
    assert values == sorted(values)
    assert values[0] < values[-1]


def test_symmetry_follows_threshold_bands():
    pick = lambda s: map_features_to_params(dict(FEATURES, symmetry_score=s)).symmetry
    assert pick(0.1) == "none"
    assert pick(0.5) == "mirror"
    assert pick(0.9) == "four_fold"


def test_low_confidence_falls_back_to_defaults():
    zero = {"tempo": 0.0, "pitch": 0.0, "cycle": 0.0}
    full = {"tempo": 0.9, "pitch": 0.9, "cycle": 0.9}
    wild = dict(
        pitch_range_cents=99, distinct_pitch_count=1, gamaka_intensity=1.0,
        symmetry_score=1.0, tempo_bpm=299, cycle_beats=3,
    )
    # Reliable analysis steers the result...
    assert map_features_to_params(dict(FEATURES, confidence=full)) != \
        map_features_to_params(dict(wild, confidence=full))
    # ...unreliable analysis must not: wildly different raw values give the
    # same parameters because both fall back to the defaults.
    assert map_features_to_params(dict(FEATURES, confidence=zero)) == \
        map_features_to_params(dict(wild, confidence=zero))


def test_similar_pitch_shapes_share_a_seed_and_different_ones_do_not():
    a = map_features_to_params(dict(FEATURES, contour_signature="130001000200000200010000"))
    b = map_features_to_params(dict(FEATURES, contour_signature="130001000200000200010000"))
    c = map_features_to_params(dict(FEATURES, contour_signature="000000000000000000000020"))
    assert a.seed == b.seed
    assert a.seed != c.seed


def test_ordered_contour_changes_seed_when_pitch_class_counts_match():
    common = dict(FEATURES, contour_signature="same histogram")
    ascending = map_features_to_params(
        dict(common, ordered_contour_signature="ascending phrase")
    )
    descending = map_features_to_params(
        dict(common, ordered_contour_signature="descending phrase")
    )
    assert ascending.seed != descending.seed
