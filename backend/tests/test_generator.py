from kolam.generator import generate_kolam
from schemas import KolamParams


def make(**overrides):
    base = dict(grid_size=7, symmetry="mirror", turn_density=0.5, seed=12345)
    base.update(overrides)
    return KolamParams(**base)


def test_generator_returns_svg():
    result = generate_kolam(make())
    assert result.svg.startswith("<svg")
    assert result.svg.endswith("</svg>")
    assert result.closed is True


def test_generator_returns_a_validated_kolam():
    result = generate_kolam(make())
    assert result.validated is True
    assert all(result.validation.values())
    assert result.validation["every_pulli_encircled"] is True
    assert result.validation["single_closed_curve"] is True


def test_validated_is_true_only_when_every_check_passes():
    for size in (5, 9, 13):
        for symmetry in ("none", "mirror", "four_fold"):
            result = generate_kolam(make(grid_size=size, symmetry=symmetry))
            assert result.validated == all(result.validation.values())
            assert result.symmetry_applied == symmetry


def test_same_parameters_give_same_path():
    first = generate_kolam(make())
    second = generate_kolam(make())
    assert first.path == second.path
    assert first.svg == second.svg


def test_path_is_in_pulli_units_and_explicitly_closed():
    result = generate_kolam(make(grid_size=7))
    path = result.path
    assert path[0] == path[-1]
    for x, y in path:
        assert -0.5 <= x <= 6.5 and -0.5 <= y <= 6.5
    # 4 * n^2 segments, plus the repeated closing point.
    assert len(path) == 4 * 7 * 7 + 1


def test_svg_contains_one_dot_per_pulli_and_one_curve():
    result = generate_kolam(make(grid_size=9))
    assert result.svg.count("<circle") == 81
    assert result.svg.count('class="kolam-curve"') == 1
