# SwaraKollam API Contract

## POST /generate

Request:
- Content type: multipart/form-data
- Field name: `audio` (README). The legacy name `file` is still accepted.
- Accepted formats: WAV, MP3, OGG, FLAC, M4A (M4A generally needs ffmpeg on
  the server; MP3 needs libsndfile >= 1.1 or ffmpeg)
- Maximum size: `MAX_UPLOAD_MB` (default 15); analysed length: first
  `MAX_AUDIO_SECONDS` (default 45)

Response `200`:
- `features`: extracted audio features, each with a confidence value
  (`confidence.tempo`, `.pitch`, `.cycle`) and a `contour_signature`
- `params`: mapped kolam parameters
  (`grid_size`, `symmetry`, `turn_density`, `crossing_density`, `seed`)
- `kolam`:
  - `path`: ordered lattice coordinates in pulli units (pullis at integer
    x, y in `0..grid_size-1`, y up; crossings/bounces at half-integers; first
    point repeated at the end)
  - `svg`: ready-to-embed drawing; `curve_path`: smoothed SVG path data
    (600x600 canvas, `pathLength="1"` for stroke-dash animation)
  - `closed`, `validated`, `validation` (per-check booleans)
  - `symmetry_requested`, `symmetry_applied`, `attempts`, `repairs`, `message`

Errors:
- 400: no file, unsupported extension, empty or undecodable audio
- 413: upload exceeds the configured size (enforced while streaming)
- 422: audio too short (< 2 s of sound), silent, or no voiced content detected
- 500: unexpected analysis failure, or no kolam passed validation (a kolam
  that fails validation is never returned)

## POST /generate/params

Accepts JSON:

    {
      "grid_size": 7,
      "symmetry": "mirror",
      "turn_density": 0.5,
      "crossing_density": 0.5,
      "seed": 12345
    }

`grid_size` must be odd and between 5 and 13; `crossing_density` is optional
(default 0.5). Returns the same response shape as `/generate`, with neutral
placeholder features. Useful for developing and testing the generator without
audio.

## Validation

`validated` is `true` only when every check in `validation` passes:

- `closed_path`: consecutive points are unit diagonal steps and the curve closes
- `single_closed_curve`: exactly one closed curve results
- `no_dangling_segments`: every lattice segment is traced exactly once and
  every crossing/bounce point is visited the expected number of times
- `every_pulli_encircled`: every pulli has a non-zero winding number
- `symmetry_consistent`: the traced curve is invariant under the applied symmetry

This is validity within the documented mirror-lattice model (see
`generator_contract.md`). If the requested symmetry cannot be combined with a
single closed curve for the given parameters, the generator falls back
four_fold -> mirror -> none and reports it in `symmetry_applied` and `message`.
