"""Mirror-lattice model for Sikku Kolam / Brahma Mudi.

Pure Python, no third-party imports, so the topology code can be tested alone.

Geometry (all coordinates are doubled, so pullis sit on even/even points)
------------------------------------------------------------------------
* The n x n pullis are at (2i, 2j), 0 <= i, j < n.
* A *vertex* of the model is the midpoint of an edge joining two adjacent
  pullis.  Midpoints of horizontal edges are (odd, even); of vertical edges
  (even, odd).  The curve crosses itself or bounces at these points, which is
  exactly where traditional Sikku Kolam lines cross.
* A ring of *rim* vertices sits on the edges between each border pulli and the
  (virtual) pulli just outside the grid.  They act as the enclosing wall, so
  the curve always runs around the outside of the border pullis.
* The curve travels along the four diagonal directions between neighbouring
  vertices.  Every vertex has four diagonal "ports" (NE, NW, SE, SW), except
  rim vertices which have two (the ones facing the grid).

Vertex states (interior vertices only; rim vertices are fixed walls)
--------------------------------------------------------------------
CROSS  the two strands pass straight through (a sikku crossing)
CUP    both strands bounce away from the edge's two end-pullis, i.e. each
       strand is an arc cupping one of the two pullis
SKIM   both strands bounce along the edge, skimming past it on either side

Each state pairs up the four ports into two strands.  Tracing the strands
gives a set of closed curves.  Re-pairing a vertex whose two strands belong to
different curves always merges them into one, which is the basis of the
repair step in ``builder.py``.
"""

from __future__ import annotations

CROSS, CUP, SKIM = 0, 1, 2
STATE_NAMES = ("cross", "cup", "skim")

PORT_VECTORS = {"NE": (1, 1), "NW": (-1, 1), "SE": (1, -1), "SW": (-1, -1)}
PORT_ORDER = ("NE", "NW", "SE", "SW")
OPPOSITE = {"NE": "SW", "SW": "NE", "NW": "SE", "SE": "NW"}

_CROSS_PAIRS = (("SW", "NE"), ("NW", "SE"))
# Horizontal-edge midpoints: pullis to the left and right.
_H_PAIRS = {
    CUP: (("NE", "SE"), ("NW", "SW")),
    SKIM: (("NE", "NW"), ("SE", "SW")),
}
# Vertical-edge midpoints: pullis above and below.
_V_PAIRS = {
    CUP: (("NE", "NW"), ("SE", "SW")),
    SKIM: (("NE", "SE"), ("NW", "SW")),
}


def _pairs_to_map(pairs):
    mapping = {}
    for a, b in pairs:
        mapping[a] = b
        mapping[b] = a
    return mapping


Point = tuple[int, int]


class Lattice:
    """Vertex set, adjacency and strand pairings for an n x n pulli grid."""

    def __init__(self, n: int):
        if n < 2:
            raise ValueError("grid size must be at least 2")
        self.n = n
        top = 2 * n - 1

        pts: list[Point] = []
        # Rim vertices first, so vertex 0 is always (-1, 0): a stable start.
        for y in range(0, 2 * n - 1, 2):
            pts.append((-1, y))
        for y in range(0, 2 * n - 1, 2):
            pts.append((top, y))
        for x in range(0, 2 * n - 1, 2):
            pts.append((x, -1))
        for x in range(0, 2 * n - 1, 2):
            pts.append((x, top))
        self.rim_count = len(pts)

        for y in range(0, 2 * n - 1, 2):  # horizontal-edge midpoints
            for x in range(1, 2 * n - 2, 2):
                pts.append((x, y))
        for x in range(0, 2 * n - 1, 2):  # vertical-edge midpoints
            for y in range(1, 2 * n - 2, 2):
                pts.append((x, y))

        self.pts = pts
        self.index = {p: i for i, p in enumerate(pts)}
        self.count = len(pts)

        # nbr[v][port] -> neighbouring vertex id
        self.nbr: list[dict[str, int]] = []
        for (x, y) in pts:
            ports = {}
            for name in PORT_ORDER:
                dx, dy = PORT_VECTORS[name]
                q = (x + dx, y + dy)
                if q in self.index:
                    ports[name] = self.index[q]
            self.nbr.append(ports)

        # partner[v][state] -> {in_port: out_port}
        self.partner: list[dict[int, dict[str, str]]] = []
        for v, (x, y) in enumerate(pts):
            ports = list(self.nbr[v].keys())
            if v < self.rim_count:
                if len(ports) != 2:
                    raise AssertionError(f"rim vertex {pts[v]} has {len(ports)} ports")
                wall = _pairs_to_map([tuple(ports)])
                self.partner.append({CROSS: wall, CUP: wall, SKIM: wall})
                continue
            if len(ports) != 4:
                raise AssertionError(f"interior vertex {pts[v]} has {len(ports)} ports")
            table = _H_PAIRS if y % 2 == 0 else _V_PAIRS
            self.partner.append(
                {
                    CROSS: _pairs_to_map(_CROSS_PAIRS),
                    CUP: _pairs_to_map(table[CUP]),
                    SKIM: _pairs_to_map(table[SKIM]),
                }
            )

        self.expected_edges = self.count_edges()

    # ------------------------------------------------------------------
    def count_edges(self) -> int:
        return sum(len(p) for p in self.nbr) // 2

    def is_rim(self, v: int) -> bool:
        return v < self.rim_count

    def interior_vertices(self) -> range:
        return range(self.rim_count, self.count)

    def pulli_points(self) -> list[Point]:
        n = self.n
        return [(2 * i, 2 * j) for j in range(n) for i in range(n)]

    # ------------------------------------------------------------------
    def trace(self, states: list[int]) -> list[list[int]]:
        """Trace every closed curve.

        ``states[v]`` is the state of vertex v (ignored for rim vertices).
        Returns a list of loops; each loop is the cyclic sequence of vertices
        entered, so a crossing vertex appears twice in a single loop.
        """
        visited: set[tuple[int, str]] = set()
        loops: list[list[int]] = []
        limit = 4 * self.count + 8

        for v0 in range(self.count):
            for p0 in PORT_ORDER:
                if p0 not in self.nbr[v0] or (v0, p0) in visited:
                    continue
                loop: list[int] = []
                v, inport = v0, p0
                for _ in range(limit):
                    out = self.partner[v][states[v]][inport]
                    visited.add((v, inport))
                    visited.add((v, out))
                    loop.append(v)
                    v = self.nbr[v][out]
                    inport = OPPOSITE[out]
                    if v == v0 and inport == p0:
                        break
                else:  # pragma: no cover - indicates a model bug
                    raise RuntimeError("trace did not close")
                loops.append(loop)
        return loops

    # ------------------------------------------------------------------
    def symmetry_maps(self, symmetry: str):
        """Point maps generating the requested symmetry group."""
        c2 = 2 * (self.n - 1)
        if symmetry == "mirror":  # reflection about the vertical axis
            return [lambda p: (c2 - p[0], p[1])]
        if symmetry == "four_fold":  # 90 degree rotation about the centre
            return [lambda p: (c2 - p[1], p[0])]
        return []

    def orbits(self, symmetry: str) -> list[tuple[int, ...]]:
        """Orbits of interior vertices under the symmetry group."""
        maps = self.symmetry_maps(symmetry)
        seen: set[int] = set()
        result: list[tuple[int, ...]] = []
        for v in self.interior_vertices():
            if v in seen:
                continue
            orbit = {v}
            frontier = [v]
            while frontier:
                cur = frontier.pop()
                for f in maps:
                    img = self.index[f(self.pts[cur])]
                    if img not in orbit:
                        orbit.add(img)
                        frontier.append(img)
            seen |= orbit
            result.append(tuple(sorted(orbit)))
        return result
