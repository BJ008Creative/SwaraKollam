import logging
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from audio.errors import AudioDecodeError, AudioError
from audio.features import analyze_audio
from kolam.generator import KolamGenerationError, generate_kolam
from mapping.mapper import map_features_to_params
from schemas import FeatureVector, GenerateResponse, KolamParams

logger = logging.getLogger("swarakollam")

app = FastAPI(
    title="SwaraKollam API",
    description="Music-driven procedural Brahma Mudi (single-line Sikku Kolam) generation",
    version="1.1.0",
)

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "15"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
# Analyse a full musical excerpt by default. Operators can lower this for
# constrained deployments, while uploads remain bounded by MAX_UPLOAD_MB.
MAX_AUDIO_SECONDS = float(os.getenv("MAX_AUDIO_SECONDS", "180"))
READ_CHUNK = 1024 * 1024
MULTIPART_SLACK = 1024 * 1024  # form boundaries and headers

# README lists mp3/wav; the extra formats work when libsndfile/ffmpeg can
# decode them (m4a generally needs ffmpeg installed on the server).
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac", ".m4a"}

origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins.split(",") if o.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"name": "SwaraKollam API", "status": "ok", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}


def build_response(features: dict, params: KolamParams) -> GenerateResponse:
    kolam = generate_kolam(params)
    return GenerateResponse(
        features=FeatureVector(**features),
        params=params,
        kolam=kolam,
    )


async def save_upload(upload: UploadFile, suffix: str) -> str:
    """Stream the upload to a temp file, enforcing the size limit as it goes."""
    total = 0
    path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            path = temp.name
            while True:
                chunk = await upload.read(READ_CHUNK)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Maximum file size is {MAX_UPLOAD_MB} MB.",
                    )
                temp.write(chunk)
    except BaseException:
        if path and os.path.exists(path):
            os.remove(path)
        raise
    if total == 0:
        os.remove(path)
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    return path


@app.post("/generate", response_model=GenerateResponse)
async def generate_from_audio(
    request: Request,
    audio: UploadFile | None = File(default=None),
    file: UploadFile | None = File(default=None),  # legacy field name
):
    """Analyse a Carnatic recording and return a validated Brahma Mudi.

    Send the recording as multipart field ``audio`` (``file`` is still
    accepted for backward compatibility).
    """
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > MAX_UPLOAD_BYTES + MULTIPART_SLACK:
        raise HTTPException(
            status_code=413, detail=f"Maximum file size is {MAX_UPLOAD_MB} MB."
        )

    upload = audio if audio is not None else file
    if upload is None:
        raise HTTPException(
            status_code=400, detail="Send the recording as multipart field 'audio'."
        )

    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Upload WAV, MP3, OGG, FLAC or M4A.")

    temp_path = None
    try:
        temp_path = await save_upload(upload, suffix)

        try:
            # Analysis is CPU-heavy: keep it off the event loop.
            features = await run_in_threadpool(analyze_audio, temp_path, MAX_AUDIO_SECONDS)
        except AudioDecodeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except AudioError as exc:  # too short / no voiced content
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            logger.exception("Unexpected audio analysis failure")
            raise HTTPException(
                status_code=500, detail="Audio analysis failed unexpectedly."
            ) from exc

        params = map_features_to_params(features)
        try:
            return await run_in_threadpool(build_response, features, params)
        except KolamGenerationError as exc:
            logger.exception("Kolam generation failed validation")
            raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        for item in (audio, file):
            if item is not None:
                await item.close()


@app.post("/generate/params", response_model=GenerateResponse)
def generate_from_params(params: KolamParams):
    """Generate a kolam from parameters directly, without audio.

    Useful for developing and testing the kolam module.
    """
    neutral_features = {
        "tempo_bpm": 0.0,
        "cycle_beats": None,
        "pitch_range_cents": 0.0,
        "distinct_pitch_count": 0,
        "gamaka_intensity": 0.0,
        "symmetry_score": 0.0,
        "confidence": {"tempo": 0.0, "pitch": 0.0, "cycle": 0.0},
        "duration_seconds": 0.0,
        "notes": ["Audio analysis was skipped; parameters were supplied directly."],
    }
    try:
        return build_response(neutral_features, params)
    except KolamGenerationError as exc:
        logger.exception("Kolam generation failed validation")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
