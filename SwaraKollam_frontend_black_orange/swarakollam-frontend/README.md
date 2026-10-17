# SwaraKollam frontend

React + Vite frontend for the SwaraKollam FastAPI backend. The interface uses a near-black canvas, turmeric yellow and orange accents, orange primary buttons, and intentionally static controls (no hover-driven effects).

## What it does

- Upload and preview WAV, MP3, OGG, FLAC or M4A recordings.
- Send the recording as multipart field `audio` to `POST /generate`.
- Show returned audio features, confidence scores, analysis notes and the feature-to-parameter mapping.
- Show the exact mapped generator parameters (grid size, symmetry, turn density, crossing density and deterministic seed).
- Render the backend-returned SVG Kolam, replay its single-line drawing animation, and download PNG or SVG.
- Display generator validation checks from the backend response without fabricating a successful result.

The mapping is an intentional designed correspondence, not raga recognition or a claim that the generated Kolam is a canonical translation of the recording.

## Requirements

- Node.js 18+ (Node 20+ recommended)
- npm
- The corrected SwaraKollam FastAPI backend running separately

## Run locally (Windows PowerShell)

```powershell
npm install
Copy-Item .env.example .env
npm run dev
```

By default, the frontend expects the backend at `http://127.0.0.1:8000`. Set `VITE_API_BASE_URL` in `.env` if your backend runs elsewhere. Do not add a trailing slash.

In a second terminal, from the backend project root (the directory containing `api/`, `audio/`, `kolam/`, `mapping/`, and `schemas.py`):

```powershell
python -m uvicorn api.main:app --reload --port 8000
```

Open the local Vite URL printed in the terminal, normally `http://localhost:5173`.

## API contract used

- `GET /health` — connection status.
- `POST /generate` — multipart upload using the `audio` field. Backend defaults are 15 MB maximum and analysis of up to 45 seconds.
- Successful response must include `features`, `params`, and `kolam.svg`.

The frontend's feature mapping panel reflects the backend output: pitch range + pitch classes → grid size; contour repetition → symmetry; gamaka + tempo → turn density; contour signature → seed; tempo + cycle estimate → crossing density. Confidence is shown separately for tempo, pitch and cycle.

## Build

```powershell
npm run build
npm run preview
```
