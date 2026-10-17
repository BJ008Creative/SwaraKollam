"""Public entry point of the kolam module.

``generate_kolam`` builds a single-closed-curve Brahma Mudi on the mirror
lattice, validates it independently, and only then returns it.  A kolam that
fails validation is never returned: ``KolamGenerationError`` is raised instead.
"""

from kolam.builder import KolamGenerationError, build_kolam
from kolam.render import render_svg
from schemas import KolamParams, KolamResult

__all__ = ["generate_kolam", "KolamGenerationError"]


def generate_kolam(params: KolamParams) -> KolamResult:
    core = build_kolam(
        n=params.grid_size,
        symmetry=params.symmetry,
        turn_density=params.turn_density,
        crossing_density=params.crossing_density,
        seed=params.seed,
    )
    lattice = core.lattice
    points = [lattice.pts[v] for v in core.loop]

    path = [[x / 2, y / 2] for x, y in points]
    path.append(list(path[0]))  # explicit closure for polyline renderers

    svg, curve_d = render_svg(params.grid_size, points)

    message = (
        "Valid single closed curve in the mirror-lattice model: every lattice "
        "segment is traced once and every pulli is enclosed."
    )
    if core.symmetry_applied != core.symmetry_requested:
        message += (
            f" Requested symmetry '{core.symmetry_requested}' could not be "
            f"combined with a single closed curve for these parameters; "
            f"'{core.symmetry_applied}' was applied instead."
        )

    return KolamResult(
        grid_size=params.grid_size,
        path=path,
        closed=core.validation["closed_path"],
        validated=core.valid,
        svg=svg,
        curve_path=curve_d,
        validation=core.validation,
        symmetry_requested=core.symmetry_requested,
        symmetry_applied=core.symmetry_applied,
        attempts=core.attempts,
        repairs=core.repairs,
        message=message,
    )
