"""Topology tests for the mirror-lattice generator and its validator.

These use only the standard library, so they run without any audio or web
dependencies (README phase 1: generator and validator tested independently).
"""

from kolam.builder import build_kolam, get_lattice
from kolam.lattice import CROSS, CUP, Lattice
from kolam.validator import validate_kolam, winding_number

SIZES = (5, 7, 9, 11, 13)
SYMMETRIES = ("none", "mirror", "four_fold")


def test_lattice_edge_count_is_four_n_squared():
    for n in SIZES:
        lattice = Lattice(n)
        assert lattice.expected_edges == 4 * n * n


def test_every_returned_kolam_is_valid_across_sizes_symmetries_and_seeds():
    for n in SIZES:
        for symmetry in SYMMETRIES:
            for seed in range(0, 400, 37):
                for turn, cross in ((0.1, 0.2), (0.5, 0.5), (0.95, 0.9)):
                    core = build_kolam(n, symmetry, turn, cross, seed)
                    assert core.valid, (n, symmetry, seed, core.validation)
                    assert len(core.loop) == 4 * n * n


def test_requested_symmetry_is_honoured():
    for n in SIZES:
        for symmetry in ("mirror", "four_fold"):
            for seed in range(0, 200, 29):
                core = build_kolam(n, symmetry, 0.5, 0.5, seed)
                assert core.symmetry_applied == symmetry


def test_same_parameters_give_identical_output():
    first = build_kolam(9, "four_fold", 0.4, 0.6, 123456)
    second = build_kolam(9, "four_fold", 0.4, 0.6, 123456)
    assert first.loop == second.loop
    assert first.states == second.states


def test_different_seeds_give_different_kolams():
    loops = {tuple(build_kolam(9, "none", 0.5, 0.5, s).loop) for s in range(10)}
    assert len(loops) > 1


def test_validator_rejects_multiple_loops():
    lattice = get_lattice(7)
    loops = lattice.trace([CUP] * lattice.count)  # one small loop per pulli
    assert len(loops) == 49
    result = validate_kolam(lattice, loops, "none")
    assert result["single_closed_curve"] is False
    assert not all(result.values())

    crossed = lattice.trace([CROSS] * lattice.count)
    assert len(crossed) > 1
    assert validate_kolam(lattice, crossed, "none")["single_closed_curve"] is False


def test_validator_rejects_a_curve_with_a_missing_vertex():
    lattice = get_lattice(7)
    loop = build_kolam(7, "none", 0.5, 0.5, 42).loop
    broken = loop[:5] + loop[6:]
    result = validate_kolam(lattice, [broken], "none")
    assert result["closed_path"] is False
    assert result["no_dangling_segments"] is False


def test_validator_rejects_a_truncated_curve():
    lattice = get_lattice(7)
    loop = build_kolam(7, "none", 0.5, 0.5, 42).loop
    result = validate_kolam(lattice, [loop[:-10]], "none")
    assert not all(result.values())


def test_validator_detects_symmetry_violations():
    lattice = get_lattice(7)
    asymmetric = build_kolam(7, "none", 0.5, 0.5, 42).loop
    assert validate_kolam(lattice, [asymmetric], "mirror")["symmetry_consistent"] is False
    assert validate_kolam(lattice, [asymmetric], "four_fold")["symmetry_consistent"] is False

    mirrored = build_kolam(7, "mirror", 0.5, 0.5, 42).loop
    assert validate_kolam(lattice, [mirrored], "mirror")["symmetry_consistent"] is True
    assert validate_kolam(lattice, [mirrored], "four_fold")["symmetry_consistent"] is False


def test_every_pulli_is_enclosed_and_outside_is_not():
    lattice = get_lattice(7)
    loop = build_kolam(7, "none", 0.5, 0.5, 42).loop
    poly = [lattice.pts[v] for v in loop]
    assert all(winding_number(poly, x, y) != 0 for x, y in lattice.pulli_points())
    assert winding_number(poly, -9, -9) == 0


def test_loop_steps_are_unit_diagonals_and_close():
    lattice = get_lattice(9)
    loop = build_kolam(9, "mirror", 0.3, 0.4, 7).loop
    pts = [lattice.pts[v] for v in loop]
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        assert abs(a[0] - b[0]) == 1 and abs(a[1] - b[1]) == 1
