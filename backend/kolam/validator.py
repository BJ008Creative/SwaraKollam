"""Independent validator for a traced kolam.

It deliberately re-derives everything from the vertex *coordinates* and the
traced vertex sequence, rather than reusing the tracer's port tables, so a bug
in the tracer cannot silently validate itself.
"""

from __future__ import annotations

from kolam.lattice import Lattice


def winding_number(poly: list[tuple[int, int]], px: int, py: int) -> int:
    """Exact integer winding number of a closed polygon about (px, py)."""
    wn = 0
    count = len(poly)
    for i in range(count):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % count]
        cross = (x2 - x1) * (py - y1) - (px - x1) * (y2 - y1)
        if y1 <= py:
            if y2 > py and cross > 0:
                wn += 1
        elif y2 <= py and cross < 0:
            wn -= 1
    return wn


def _edge(a, b):
    return (a, b) if a <= b else (b, a)


def validate_kolam(
    lattice: Lattice,
    loops: list[list[int]],
    symmetry: str,
) -> dict[str, bool]:
    pts = lattice.pts
    point_set = set(pts)
    checks = {
        "closed_path": False,
        "single_closed_curve": False,
        "no_dangling_segments": False,
        "every_pulli_encircled": False,
        "symmetry_consistent": False,
    }

    checks["single_closed_curve"] = len(loops) == 1
    if not loops:
        return checks
    loop = loops[0]
    poly = [pts[v] for v in loop]
    count = len(poly)

    # 1. Closed, and each step is a unit diagonal move between valid vertices.
    steps_ok = count >= 4
    for i in range(count):
        a, b = poly[i], poly[(i + 1) % count]
        if abs(a[0] - b[0]) != 1 or abs(a[1] - b[1]) != 1:
            steps_ok = False
            break
    checks["closed_path"] = steps_ok

    # 2. Every lattice edge is used exactly once; no vertex is left dangling.
    expected = set()
    for p in point_set:
        for dx, dy in ((1, 1), (1, -1)):
            q = (p[0] + dx, p[1] + dy)
            if q in point_set:
                expected.add(_edge(p, q))
    used: dict = {}
    for i in range(count):
        e = _edge(poly[i], poly[(i + 1) % count])
        used[e] = used.get(e, 0) + 1
    edges_ok = set(used) == expected and all(c == 1 for c in used.values())

    visits: dict = {}
    for p in poly:
        visits[p] = visits.get(p, 0) + 1
    rim_points = set(pts[: lattice.rim_count])
    visits_ok = all(
        visits.get(p, 0) == (1 if p in rim_points else 2) for p in point_set
    )
    checks["no_dangling_segments"] = edges_ok and visits_ok

    # 3. Every pulli has a non-zero winding number (is enclosed by the curve).
    if steps_ok:
        checks["every_pulli_encircled"] = all(
            winding_number(poly, x, y) != 0 for x, y in lattice.pulli_points()
        )

    # 4. Symmetry: the set of strand "passes" must be invariant under the map.
    maps = lattice.symmetry_maps(symmetry)
    if not maps:
        checks["symmetry_consistent"] = True
    elif steps_ok:
        passes = set()
        for i in range(count):
            prev, cur, nxt = poly[i - 1], poly[i], poly[(i + 1) % count]
            passes.add((cur, frozenset((prev, nxt))))
        sym_ok = True
        for f in maps:
            for cur, pair in passes:
                img = (f(cur), frozenset(f(p) for p in pair))
                if img not in passes:
                    sym_ok = False
                    break
            if not sym_ok:
                break
        checks["symmetry_consistent"] = sym_ok

    return checks
