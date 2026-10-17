import librosa
import numpy as np

TARGET_SR = 22050


def load_audio(
    path: str,
    max_seconds: float = 45.0
) -> tuple[np.ndarray, int]:

    y, sr = librosa.load(
        path,
        sr=TARGET_SR,
        mono=True,
        duration=max_seconds
    )

    if y.size == 0:
        raise ValueError("No audio samples could be decoded.")

    # Remove leading and trailing silence.
    trimmed, _ = librosa.effects.trim(y, top_db=35)

    if trimmed.size:
        y = trimmed

    if len(y) < 2 * sr:
        raise ValueError(
            "Audio must contain at least 2 seconds of sound."
        )

    return y.astype(np.float32), sr