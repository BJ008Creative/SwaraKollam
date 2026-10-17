# SwaraKollam frontend

A React + Vite frontend for the SwaraKollam audio-to-Kolam backend. The interface uses a black/charcoal base with turmeric-yellow and orange accents, with no hover-driven visual effects.

## Project structure

```text
src/
├── App.jsx                         # page composition and shared workflow state
├── main.jsx                        # React entry point
├── constants.js                    # accepted audio formats
├── styles.css                      # global design system and responsive styles
└── components/
    ├── layout/
    │   ├── SiteHeader.jsx
    │   ├── IntroSection.jsx
    │   ├── MethodNote.jsx
    │   └── SiteFooter.jsx
    ├── audio/
    │   └── UploadPanel.jsx          # file picker, drag/drop, audio preview, submit
    ├── analysis/
    │   └── AudioAnalysisPanel.jsx   # feature metrics, confidence, feature-to-form mapping
    ├── kolam/
    │   ├── PatternPanel.jsx         # SVG canvas, replay, downloads, validation
    │   └── ParametersPanel.jsx     # generated parameters and seed
    └── ui/
        ├── Metric.jsx
        ├── ConfidenceBar.jsx
        ├── MappingRow.jsx
        └── StatusPill.jsx
```

## Requirements

- Node.js 20 or newer
- npm
- The SwaraKollam FastAPI backend running separately

## Setup

```powershell
npm install
Copy-Item .env.example .env
npm run dev
```

The default backend URL is `http://127.0.0.1:8000`. To change it, edit `.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start the backend in another terminal from its backend folder:

```powershell
python -m uvicorn api.main:app --reload --port 8000
```

Open the Vite URL printed in the terminal, usually `http://localhost:5173`.

## Features

- WAV, MP3, OGG, FLAC and M4A upload with local audio preview
- `/health` status indicator and `/generate` multipart request
- Audio feature metrics and feature-to-Kolam mapping explanations
- Returned SVG rendering, replay animation, PNG export and SVG download
- Generator validation flags and mapped parameter summary
- Responsive desktop two-column and small-screen stacked layout

The visual interface reports the backend's validation honestly; it does not turn failed generator checks into a success state. Audio measurements shown as proxies are not presented as definitive raga or tala recognition.
