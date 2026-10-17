import numpy as np
import librosa

from audio.preprocess import load_audio


def clamp(value, low, high):
    return max(low, min(high, float(value)))


def estimate_pitch_features(y, sr, hop_length):
    try:
        f0, voiced_flag, voiced_prob = librosa.pyin(
            y,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
            sr=sr,
            frame_length=2048,
            hop_length=hop_length
        )

        f0 = np.asarray(f0, dtype=float)
        valid = f0[np.isfinite(f0) & (f0 > 0)]

        if len(valid) < 5:
            raise ValueError("Too few reliable pitch frames.")

        midi = librosa.hz_to_midi(valid)

        pitch_range = (
            np.percentile(midi, 90)
            - np.percentile(midi, 10)
        ) * 100

        distinct_pitches = len(
            np.unique(np.round(midi))
        )

        differences = np.abs(np.diff(midi)) * 100
        gamaka_proxy = clamp(
            np.mean(differences > 35)
            * np.percentile(differences, 75) / 250,
            0,
            1
        )

        confidence = float(np.mean(voiced_prob[
            np.isfinite(f0)
        ])) if np.any(np.isfinite(f0)) else 0.0

        return {
            "pitch_range_cents": round(float(pitch_range), 2),
            "distinct_pitch_count": int(distinct_pitches),
            "gamaka_intensity": round(gamaka_proxy, 4),
            "pitch_confidence": round(clamp(confidence, 0, 1), 4),
            "notes": [
                "Pitch and gamaka values are heuristic estimates.",
                "They are not Carnatic swara transcription."
            ]
        }

    except Exception:
        return {
            "pitch_range_cents": 0.0,
            "distinct_pitch_count": 0,
            "gamaka_intensity": 0.0,
            "pitch_confidence": 0.0,
            "notes": [
                "Reliable pitch could not be estimated; fallback values used."
            ]
        }


def estimate_symmetry(y, sr, hop_length):
    chroma = librosa.feature.chroma_stft(
        y=y,
        sr=sr,
        hop_length=hop_length
    )

    series = np.mean(chroma, axis=0)

    if len(series) < 8 or np.std(series) < 1e-8:
        return 0.0

    series = series - np.mean(series)
    correlation = np.correlate(series, series, mode="full")
    correlation = correlation[len(series) - 1:]

    if correlation[0] <= 0:
        return 0.0

    correlation = correlation / correlation[0]
    return round(clamp(np.max(correlation[2:]), 0, 1), 4)


def analyze_audio(
    path: str,
    max_seconds: float = 45.0
) -> dict:

    y, sr = load_audio(path, max_seconds)
    hop_length = 512

    onset_env = librosa.onset.onset_strength(
        y=y,
        sr=sr,
        hop_length=hop_length
    )

    tempo_values = librosa.feature.tempo(
        onset_envelope=onset_env,
        sr=sr,
        hop_length=hop_length
    )

    tempo = clamp(
        np.asarray(tempo_values).reshape(-1)[0],
        30,
        300
    )

    pitch = estimate_pitch_features(y, sr, hop_length)
    symmetry = estimate_symmetry(y, sr, hop_length)

    # This is a repetition proxy, not reliable tala recognition.
    cycle_beats = None

    return {
        "tempo_bpm": round(tempo, 2),
        "cycle_beats": cycle_beats,
        "pitch_range_cents": pitch["pitch_range_cents"],
        "distinct_pitch_count": pitch["distinct_pitch_count"],
        "gamaka_intensity": pitch["gamaka_intensity"],
        "symmetry_score": symmetry,
        "confidence": {
            "tempo": 0.5 if len(onset_env) > 10 else 0.0,
            "pitch": pitch["pitch_confidence"]
        },
        "duration_seconds": round(len(y) / sr, 2),
        "notes": pitch["notes"] + [
            "Tempo is estimated from onset strength.",
            "Tala/cycle detection has not yet been implemented."
        ]
    }