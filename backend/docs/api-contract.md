# SwaraKollam API Contract

## POST /generate

Request:
- Content type: multipart/form-data
- Field name: file
- Accepted formats: WAV, MP3, OGG, FLAC, M4A

Response:
- features: extracted audio features
- params: mapped Kolam parameters
- kolam: generated path, SVG and validation metadata

Errors:
- 400: unsupported or undecodable audio
- 413: upload exceeds configured size
- 422: invalid or too-short audio

## POST /generate/params

Accepts JSON:

{
  "grid_size": 7,
  "symmetry": "mirror",
  "turn_density": 0.5,
  "seed": 12345
}

This endpoint allows the generator to be tested without audio.

## Validation

A closed curve does not automatically qualify as a valid
Brahma Mudi Kolam. The validated field must remain false until
the required topology and pulli-encirclement checks pass.