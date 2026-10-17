# Kolam Generator Contract

Function:
generate_kolam(params: KolamParams) -> KolamResult

The generator receives:
- grid_size
- symmetry
- turn_density
- seed

It returns:
- ordered path
- SVG
- closed-path status
- validation results

## Required work

1. Define the mirror-lattice representation.
2. Trace line trajectories through lattice states.
3. Detect repeated states and closed loops.
4. Implement bounded repair for multiple loops.
5. Validate that exactly one closed trajectory exists.
6. Check for dangling segments and pulli encirclement.
7. Check requested symmetry.
8. Return validated=true only if every required check passes.

The current parametric curve is only a rendering prototype.
It must be replaced before claiming traditional Brahma Mudi validity.