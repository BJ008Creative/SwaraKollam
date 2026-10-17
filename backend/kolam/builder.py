"""Kolam construction: initial mirror configuration, repair, validation.

Pure Python and fully deterministic (own PRNG, no ``hash()``, no ``random``
module), so identical parameters give identical output on every platform and
Python version.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from kolam.lattice import CROSS, CUP, SKIM, Lattice
from kolam.validator import validate_kolam

MASK64 = (1 << 64) - 1
MAX_SYMMETRIC_TRIES = 40
SYMMETRY_FALLBACK = {
    "four_fold": ("four_fold", "mirror", "none"),
    "mirror": ("mirror", "none"),
    "none": ("none",),
}


class KolamGenerationError(RuntimeError):
    """Raised when no valid kolam could be produced (should never happen)."""


class Rng:
    """SplitMix64: small, fast, and identical on every platform."""

    def __init__(self, seed: int):
        self.state = seed & MASK64

    def next(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & MASK64
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK64
        return z ^ (z >> 31)

    def random(self) -> float:
        return (self.next() >> 11) / float(1 << 53)

    def shuffle(self, items: list) -> None:
        for i in range(len(items) - 1, 0, -1):
            j = self.next() % (i + 1)
            items[i], items[j] = items[j], items[i]


@dataclass
class KolamCore:
    lattice: Lattice
    states: list[int]
    loop: list[int]
    validation: dict[str, bool]
    symmetry_requested: str
    symmetry_applied: str
    attempts: int
    repairs: int

    @property
    def valid(self) -> bool:
        return all(self.validation.values())


@lru_cache(maxsize=16)
def get_lattice(n: int) -> Lattice:
    return Lattice(n)


def _state_weights(turn_density: float, crossing_density: float):
    """Probabilities of (CROSS, CUP, SKIM) for a randomly drawn vertex."""
    p_cross = min(max(crossing_density, 0.05), 0.95)
    rest = 1.0 - p_cross
    cup_share = 0.5 + 0.4 * min(max(turn_density, 0.0), 1.0)
    return (p_cross, rest * cup_share, rest * (1.0 - cup_share))


def _draw_state(rng: Rng, weights, exclude: int | None = None) -> int:
    w = list(weights)
    if exclude is not None:
        w[exclude] = 0.0
    total = sum(w)
    r = rng.random() * total
    acc = 0.0
    for state, weight in enumerate(w):
        acc += weight
        if r < acc and weight > 0:
            return state
    return max(range(3), key=lambda s: w[s])


def _loop_ids_by_vertex(lattice: Lattice, loops: list[list[int]]):
    ids: list[set[int]] = [set() for _ in range(lattice.count)]
    for li, loop in enumerate(loops):
        for v in loop:
            ids[v].add(li)
    return ids


def _try_build(lattice, symmetry, weights, rng):
    """Random configuration + repair.  Returns (states, loops, repairs) or None."""
    orbits = lattice.orbits(symmetry)
    states = [CROSS] * lattice.count
    for orbit in orbits:
        s = _draw_state(rng, weights)
        for v in orbit:
            states[v] = s

    loops = lattice.trace(states)
    repairs = 0
    budget = 6 * len(orbits) + 50

    while len(loops) > 1 and budget > 0:
        ids = _loop_ids_by_vertex(lattice, loops)
        candidates = [o for o in orbits if any(len(ids[v]) > 1 for v in o)]
        if not candidates:
            return None
        rng.shuffle(candidates)
        improved = False
        for orbit in candidates:
            budget -= 1
            old = states[orbit[0]]
            new = _draw_state(rng, weights, exclude=old)
            for v in orbit:
                states[v] = new
            trial = lattice.trace(states)
            if len(trial) < len(loops):
                loops = trial
                repairs += 1
                improved = True
                break
            for v in orbit:  # revert
                states[v] = old
            if budget <= 0:
                break
        if not improved:
            return None

    if len(loops) != 1:
        return None
    return states, loops, repairs


def build_kolam(
    n: int,
    symmetry: str,
    turn_density: float,
    crossing_density: float,
    seed: int,
) -> KolamCore:
    lattice = get_lattice(n)
    weights = _state_weights(turn_density, crossing_density)
    attempts = 0

    for level, sym in enumerate(SYMMETRY_FALLBACK[symmetry]):
        tries = MAX_SYMMETRIC_TRIES if sym != "none" else 8
        for t in range(tries):
            attempts += 1
            rng = Rng((seed * 0x9E3779B1 + level * 1_000_003 + t) & MASK64)
            built = _try_build(lattice, sym, weights, rng)
            if built is None:
                continue
            states, loops, repairs = built
            validation = validate_kolam(lattice, loops, sym)
            if all(validation.values()):
                return KolamCore(
                    lattice=lattice,
                    states=states,
                    loop=loops[0],
                    validation=validation,
                    symmetry_requested=symmetry,
                    symmetry_applied=sym,
                    attempts=attempts,
                    repairs=repairs,
                )

    raise KolamGenerationError(
        f"No valid kolam found for n={n}, symmetry={symmetry}, seed={seed}"
    )
