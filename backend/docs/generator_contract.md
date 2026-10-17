# Kolam Generator Contract

Function: `generate_kolam(params: KolamParams) -> KolamResult`
(`kolam/generator.py`; the pure-Python core is `kolam/builder.py`)

## Model

Pullis sit at the points of an n x n grid. A *vertex* is the midpoint of an
edge joining two adjacent pullis (where traditional Sikku Kolam lines cross or
turn), plus a ring of *rim* vertices on the edges between border pullis and the
outside, which act as an enclosing wall. The curve moves along diagonals
between neighbouring vertices. Each interior vertex is in one of three states,
which pair its four diagonal ports into two strands:

| State | Effect |
| ----- | ------ |
| `cross` | both strands pass straight through (a sikku crossing) |
| `cup`   | each strand is an arc cupping one of the edge's two pullis |
| `skim`  | each strand bounces along the edge, on either side of it |

The lattice has exactly `4 * n^2` segments (one diamond of four per pulli); a
valid Brahma Mudi traces each exactly once as one closed curve.

## Procedure

1. Draw a random state for each vertex orbit (orbits make the requested
   symmetry hold by construction). `crossing_density` sets P(cross);
   `turn_density` skews the remainder toward `cup`.
2. Trace every closed curve.
3. While there is more than one curve, flip a vertex orbit whose two strands
   belong to different curves. Re-pairing a vertex shared by two distinct
   curves always merges them; for symmetric orbits a flip is kept only if the
   curve count drops. The repair budget is bounded.
4. On failure, reseed deterministically (own SplitMix64 PRNG, no `hash()`),
   then fall back four_fold -> mirror -> none.
5. Run the independent validator (`kolam/validator.py`), which re-derives
   everything from vertex coordinates. Only a kolam passing every check is
   returned; otherwise `KolamGenerationError` is raised.
6. Render: smooth the polyline with a closed Catmull-Rom spline.

Symmetry: `mirror` = reflection about the vertical axis; `four_fold` = 90-degree
rotation about the centre.

Determinism: identical `KolamParams` always give identical output.

## Why pulli encirclement holds

Any horizontal ray from a pulli to the east meets the curve an odd number of
times (each interior vertex contributes 0 or 2 crossings, and the single
rim vertex at the end contributes 1), so every pulli has odd, hence non-zero,
winding number. The validator still checks this numerically rather than
assuming it.
