import librosa
import numpy as np

from audio.errors import AudioDecodeError, AudioTooShortError, NoVoicedContentError

TARGET_SR = 22050
MIN_SECONDS = 2.0
SILENCE_PEAK = 1e-4


def load_audio(
    path: str,
    max_seconds: float = 45.0,
) -> tuple[np.ndarray, int]:
    """Decode, convert to mono, resample, trim silence, peak-normalise.

    Raises AudioDecodeError (HTTP 400) for undecodable files and
    AudioTooShortError / NoVoicedContentError (HTTP 422) for unusable audio.
    """
    try:
        y, sr = librosa.load(path, sr=TARGET_SR, mono=True, duration=max_seconds)
    except Exception as exc:  # decoders raise many unrelated exception types
        raise AudioDecodeError("The file could not be decoded as audio.") from exc

    if y.size == 0:
        raise AudioDecodeError("No audio samples could be decoded.")

    if float(np.max(np.abs(y))) < SILENCE_PEAK:
        raise NoVoicedContentError("The recording is silent.")

    trimmed, _ = librosa.effects.trim(y, top_db=35)
    if trimmed.size:
        y = trimmed

    if len(y) < MIN_SECONDS * sr:
        raise AudioTooShortError(
            f"Audio must contain at least {MIN_SECONDS:.0f} seconds of sound."
        )

    peak = float(np.max(np.abs(y)))
    return (y / peak).astype(np.float32), sr
