"""Audio -> FeatureVector (as a plain dict).

librosa is used for decoding, onset strength, tempo and pYIN; all other
maths lives in ``audio.analysis`` so it can be tested without librosa.
"""

import librosa
import numpy as np

from audio import analysis
from audio.errors import NoVoicedContentError
from audio.preprocess import load_audio

HOP_LENGTH = 512
MIN_VOICED_FRAMES = 25  # about 0.6 s of pitched sound
LOW_VOICED_FRACTION = 0.10


def _tempo(onset_env: np.ndarray, sr: int) -> float:
    rhythm = getattr(librosa.feature, "rhythm", None)
    tempo_fn = getattr(rhythm, "tempo", None) or librosa.feature.tempo
    values = tempo_fn(onset_envelope=onset_env, sr=sr, hop_length=HOP_LENGTH)
    return analysis.clamp(np.asarray(values).reshape(-1)[0], 30, 300)


def _extract_f0(y: np.ndarray, sr: int):
    """pYIN f0 (NaN where unvoiced) and the per-frame voicing probability.

    CREPE (README 5.2) is not used: it would add a TensorFlow dependency.
    pYIN is the documented fallback and is what runs here.
    """
    f0, voiced_flag, voiced_prob = librosa.pyin(
        y,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C6"),
        sr=sr,
        frame_length=2048,
        hop_length=HOP_LENGTH,
    )
    f0 = np.asarray(f0, dtype=float)
    f0[~np.asarray(voiced_flag, dtype=bool)] = np.nan
    return f0, np.asarray(voiced_prob, dtype=float)


def analyze_audio(path: str, max_seconds: float = 180.0) -> dict:
    y, sr = load_audio(path, max_seconds)
    fps = sr / HOP_LENGTH
    notes = [
        "Pitch, gamaka, symmetry and cycle values are heuristic estimates, "
        "not Carnatic swara or tala transcription.",
    ]

    f0, voiced_prob = _extract_f0(y, sr)
    cents = analysis.hz_to_cents(f0)
    voiced = np.isfinite(cents)
    voiced_count = int(voiced.sum())
    if voiced_count < MIN_VOICED_FRAMES:
        raise NoVoicedContentError("No voiced (pitched) content was detected.")

    voiced_fraction = voiced_count / len(cents)
    if voiced_fraction < LOW_VOICED_FRACTION:
        notes.append("Little pitched content found; pitch features are unreliable.")
    pitch_conf = analysis.clamp(
        float(np.mean(voiced_prob[voiced])) * min(1.0, voiced_fraction / 0.25), 0, 1
    )

    stats = analysis.pitch_statistics(cents)
    gamaka = analysis.gamaka_intensity(cents, fps)
    symmetry = analysis.symmetry_score(cents, fps)

    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=HOP_LENGTH)
    if len(onset_env) > 10 and float(np.std(onset_env)) > 1e-8:
        tempo = _tempo(onset_env, sr)
        tempo_conf = analysis.tempo_confidence(onset_env, fps, tempo)
        cycle, cycle_conf = analysis.estimate_cycle(onset_env, fps, tempo)
    else:
        tempo, tempo_conf, cycle, cycle_conf = 90.0, 0.0, None, 0.0
        notes.append("No usable onsets found; tempo defaulted.")

    if tempo_conf < 0.15:
        notes.append(
            "Tempo confidence is low (free-time or unpulsed music); the mapping "
            "falls back to default tempo."
        )
    if cycle is None:
        notes.append("No repeating cycle was detected.")
    notes.append("The tonic (Sa) is taken as the dominant stable pitch class.")

    return {
        "tempo_bpm": round(tempo, 2),
        "cycle_beats": cycle,
        "pitch_range_cents": stats["pitch_range_cents"],
        "distinct_pitch_count": stats["distinct_pitch_count"],
        "gamaka_intensity": gamaka,
        "symmetry_score": symmetry,
        "confidence": {
            "tempo": tempo_conf,
            "pitch": round(pitch_conf, 4),
            "cycle": cycle_conf,
        },
        "duration_seconds": round(len(y) / sr, 2),
        "contour_signature": stats["contour_signature"],
        "ordered_contour_signature": stats["ordered_contour_signature"],
        "notes": notes,
    }
