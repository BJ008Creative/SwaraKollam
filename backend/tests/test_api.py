import io
import math
import struct
import wave

import pytest
from fastapi.testclient import TestClient

from api import main
from api.main import app

client = TestClient(app)

PARAMS = {"grid_size": 7, "symmetry": "mirror", "turn_density": 0.5, "seed": 12345}


def make_wav(seconds=6.0, freq=0.0, sr=22050, vibrato=True) -> bytes:
    """Mono 16-bit WAV: a sung-like tone with vibrato (silence if freq == 0)."""
    frames = []
    phase = 0.0
    for i in range(int(seconds * sr)):
        t = i / sr
        f = freq * (1 + 0.02 * math.sin(2 * math.pi * 5.5 * t)) if vibrato else freq
        phase += 2 * math.pi * f / sr
        frames.append(struct.pack("<h", int(12000 * math.sin(phase)) if freq else 0))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"".join(frames))
    return buf.getvalue()


def post_audio(data: bytes, name="clip.wav", field="audio"):
    return client.post("/generate", files={field: (name, data, "audio/wav")})


def test_root_and_health():
    assert client.get("/").json()["status"] == "ok"
    assert client.get("/health").status_code == 200


def test_generate_from_parameters_returns_a_validated_kolam():
    response = client.post("/generate/params", json=PARAMS)
    assert response.status_code == 200
    body = response.json()
    assert body["params"]["grid_size"] == 7
    kolam = body["kolam"]
    assert kolam["closed"] is True
    assert kolam["validated"] is True
    assert all(kolam["validation"].values())
    assert kolam["svg"].startswith("<svg")


def test_generate_from_parameters_is_deterministic():
    first = client.post("/generate/params", json=PARAMS).json()["kolam"]
    second = client.post("/generate/params", json=PARAMS).json()["kolam"]
    assert first["path"] == second["path"]


def test_invalid_grid_size_is_rejected():
    assert client.post("/generate/params", json=dict(PARAMS, grid_size=100)).status_code == 422


def test_even_grid_size_is_rejected():
    assert client.post("/generate/params", json=dict(PARAMS, grid_size=8)).status_code == 422


def test_missing_audio_field_is_400():
    assert client.post("/generate", files={}).status_code in (400, 422)


def test_unsupported_extension_is_400():
    assert post_audio(b"hello", name="notes.txt").status_code == 400


def test_empty_file_is_400():
    assert post_audio(b"").status_code == 400


def test_oversized_upload_is_413(monkeypatch):
    monkeypatch.setattr(main, "MAX_UPLOAD_BYTES", 1000)
    assert post_audio(b"\0" * 5000).status_code == 413


def test_undecodable_audio_is_400():
    pytest.importorskip("librosa")
    assert post_audio(b"this is definitely not audio" * 50).status_code == 400


def test_silent_audio_is_422():
    pytest.importorskip("librosa")
    assert post_audio(make_wav(freq=0.0)).status_code == 422


def test_too_short_audio_is_422():
    pytest.importorskip("librosa")
    assert post_audio(make_wav(seconds=1.0, freq=220.0)).status_code == 422


def test_generate_from_audio_end_to_end():
    pytest.importorskip("librosa")
    response = post_audio(make_wav(seconds=6.0, freq=220.0))
    assert response.status_code == 200
    body = response.json()
    assert body["features"]["duration_seconds"] >= 2
    assert 0 <= body["features"]["gamaka_intensity"] <= 1
    assert body["params"]["grid_size"] in (5, 7, 9, 11, 13)
    assert body["kolam"]["validated"] is True
    assert body["kolam"]["closed"] is True


def test_legacy_file_field_is_still_accepted():
    pytest.importorskip("librosa")
    response = post_audio(make_wav(seconds=6.0, freq=220.0), field="file")
    assert response.status_code == 200
