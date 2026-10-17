"""SVG rendering of a traced kolam (stdlib only)."""

from __future__ import annotations

CANVAS = 600


def to_canvas(n: int, point: tuple[int, int]) -> tuple[float, float]:
    """Doubled lattice coordinates -> canvas pixels (y axis flipped)."""
    unit = CANVAS / (n + 1)
    x = (point[0] / 2 + 1) * unit
    y = CANVAS - (point[1] / 2 + 1) * unit
    return x, y


def smooth_closed_path(points: list[tuple[float, float]]) -> str:
    """Closed uniform Catmull-Rom spline as cubic Bezier SVG path data.

    The curve passes exactly through every vertex, so the drawn line crosses
    itself at crossings and bounces smoothly at mirrors.
    """
    count = len(points)
    parts = [f"M {points[0][0]:.2f},{points[0][1]:.2f}"]
    for i in range(count):
        p0 = points[(i - 1) % count]
        p1 = points[i]
        p2 = points[(i + 1) % count]
        p3 = points[(i + 2) % count]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        parts.append(
            f"C {c1[0]:.2f},{c1[1]:.2f} {c2[0]:.2f},{c2[1]:.2f} "
            f"{p2[0]:.2f},{p2[1]:.2f}"
        )
    parts.append("Z")
    return " ".join(parts)


def render_svg(n: int, loop_points: list[tuple[int, int]]) -> tuple[str, str]:
    """Return (svg_markup, curve_path_data)."""
    canvas_points = [to_canvas(n, p) for p in loop_points]
    d = smooth_closed_path(canvas_points)

    dots = []
    for j in range(n):
        for i in range(n):
            x, y = to_canvas(n, (2 * i, 2 * j))
            dots.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3" fill="#b77935"/>'
            )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS} {CANVAS}" '
        f'role="img" aria-label="Brahma Mudi kolam on a {n} by {n} grid">'
        f'<rect width="{CANVAS}" height="{CANVAS}" fill="#fffdf8"/>'
        f'<g class="pullis">{"".join(dots)}</g>'
        f'<path class="kolam-curve" d="{d}" pathLength="1" fill="none" '
        f'stroke="#262626" stroke-width="2.5" stroke-linecap="round" '
        f'stroke-linejoin="round"/>'
        f"</svg>"
    )
    return svg, d
