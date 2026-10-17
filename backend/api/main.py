import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from audio.features import analyze_audio
from mapping.mapper import map_features_to_params
from kolam.generator import generate_kolam
from schemas import (
    FeatureVector,
    GenerateResponse,
    KolamParams,
)

app = FastAPI(
    title="SwaraKollam API",
    description="Music-driven procedural Kolam generation",
    version="1.0.0"
)

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "15"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
MAX_AUDIO_SECONDS = float(os.getenv("MAX_AUDIO_SECONDS", "45"))

ALLOWED_EXTENSIONS = {
    ".wav", ".mp3", ".ogg", ".flac", ".m4a"
}

origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in origins.split(",")
        if origin.strip()
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)


@app.get("/")
def root():
    return {
        "name": "SwaraKollam API",
        "status": "ok",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


def build_response(features: dict, params: KolamParams):
    kolam = generate_kolam(params)

    return GenerateResponse(
        features=FeatureVector(**features),
        params=params,
        kolam=kolam
    )


@app.post("/generate", response_model=GenerateResponse)
async def generate_from_audio(
    file: UploadFile = File(...)
):
    suffix = Path(file.filename or "").suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Upload WAV, MP3, OGG, FLAC or M4A."
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty."
        )

    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Maximum file size is {MAX_UPLOAD_MB} MB."
        )

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp:
            temp.write(contents)
            temp_path = temp.name

        try:
            features = analyze_audio(
                temp_path,
                max_seconds=MAX_AUDIO_SECONDS
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail=str(exc)
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail="Audio decoding or analysis failed."
            ) from exc

        params = map_features_to_params(features)

        return build_response(features, params)

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

        await file.close()


@app.post(
    "/generate/params",
    response_model=GenerateResponse
)
def generate_from_params(params: KolamParams):
    """
    Generate a pattern without audio.
    Useful for developing and testing the Kolam module.
    """

    neutral_features = {
        "tempo_bpm": 0.0,
        "cycle_beats": None,
        "pitch_range_cents": 0.0,
        "distinct_pitch_count": 0,
        "gamaka_intensity": 0.0,
        "symmetry_score": 0.0,
        "confidence": {
            "tempo": 0.0,
            "pitch": 0.0
        },
        "duration_seconds": 0.0,
        "notes": [
            "Audio analysis was skipped; parameters were supplied directly."
        ]
    }

    return build_response(neutral_features, params)