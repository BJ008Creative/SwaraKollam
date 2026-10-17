import math

from schemas import KolamParams, KolamResult


def generate_kolam(params: KolamParams) -> KolamResult:
    canvas = 600
    center = canvas / 2

    radius = 205
    sample_count = 720

    # The mapped parameters affect the shape.
    lobes = 2 + round(params.turn_density * 5)
    depth = 0.08 + params.turn_density * 0.18

    phase = (params.seed % 360) * math.pi / 180

    path = []

    for i in range(sample_count + 1):
        t = 2 * math.pi * i / sample_count + phase

        r = radius * (1 + depth * math.cos(lobes * t))

        x = center + r * math.cos(t)
        y = center + r * math.sin(t)

        path.append([round(x, 3), round(y, 3)])

    # SVG Z closes the path.
    path_data = "M " + " L ".join(
        f"{x},{y}" for x, y in path[:-1]
    ) + " Z"

    # Draw a regular grid of pullis.
    size = params.grid_size
    spacing = min(30, 230 / max(size - 1, 1))
    start = center - (size - 1) * spacing / 2

    dots = []

    for row in range(size):
        for col in range(size):
            x = start + col * spacing
            y = start + row * spacing

            dots.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" '
                f'r="2.8" fill="#b77935"/>'
            )

    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg"
         viewBox="0 0 600 600"
         role="img"
         aria-label="Kolam generation prototype">
        <rect width="600" height="600" fill="#fffdf8"/>
        <g>{''.join(dots)}</g>
        <path d="{path_data}"
              fill="none"
              stroke="#262626"
              stroke-width="2.5"
              stroke-linecap="round"
              stroke-linejoin="round"/>
    </svg>
    """

    # Numerical closure alone does not prove Brahma Mudi validity.
    closed = path[0] == path[-1]

    validation = {
        "closed_path": closed,
        "single_path_rendered": True,
        "every_pulli_encircled": False,
        "mirror_model_topology_checked": False,
        "traditional_brahma_mudi_validity": False
    }

    return KolamResult(
        grid_size=size,
        path=path,
        closed=closed,
        validated=False,
        svg=svg,
        validation=validation,
        message=(
            "Prototype renderer only. Implement and test the mirror-model "
            "generator and pulli-encirclement validator before claiming "
            "traditional Brahma Mudi validity."
        )
    )