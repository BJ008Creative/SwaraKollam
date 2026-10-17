from schemas import KolamParams
from kolam.generator import generate_kolam


def test_generator_returns_svg():
    params = KolamParams(
        grid_size=7,
        symmetry="mirror",
        turn_density=0.5,
        seed=12345
    )

    result = generate_kolam(params)

    assert result.svg.startswith("<svg")
    assert "</svg>" in result.svg
    assert result.closed is True


def test_generator_does_not_claim_unverified_validity():
    params = KolamParams(
        grid_size=7,
        symmetry="mirror",
        turn_density=0.5,
        seed=12345
    )

    result = generate_kolam(params)

    assert result.validated is False
    assert result.validation["every_pulli_encircled"] is False


def test_same_parameters_give_same_path():
    params = KolamParams(
        grid_size=7,
        symmetry="mirror",
        turn_density=0.5,
        seed=12345
    )

    first = generate_kolam(params)
    second = generate_kolam(params)

    assert first.path == second.path