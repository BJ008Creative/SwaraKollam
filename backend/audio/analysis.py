"""Pure-numpy feature maths (no librosa), so it can be unit-tested directly.

All pitch values are in cents.  Pitch is expressed relative to an estimated
tonic (Sa) so results are comparable across singers and recordings.
"""

from __future__ import annotations

import numpy as np

REF_HZ = 55.0  # arbitrary absolute reference for the cents scale


def clamp(value, low, high) -> float:
    return float(max(low, min(high, float(value))))


def hz_to_cents(f0_hz: np.ndarray) -> np.ndarray:
    """Hz -> cents above REF_HZ; non-positive / non-finite become NaN."""
    f0 = np.asarray(f0_hz, dtype=float)
    out = np.full(f0.shape, np.nan)
    ok = np.isfinite(f0) & (f0 > 0)
    out[ok] = 1200.0 * np.log2(f0[ok] / REF_HZ)
    return out


# ----------------------------------------------------------------------
# Tonic and pitch statistics
# ----------------------------------------------------------------------
def _stable_cents(cents: np.ndarray, max_step: float = 8.0, minimum: int = 20):
    """Voiced frames whose pitch barely moved since the previous frame."""
    c = np.asarray(cents, dtype=float)
    stable = np.zeros(len(c), dtype=bool)
    if len(c) > 1:
        step = np.abs(np.diff(c))
        stable[1:] = np.isfinite(step) & (step < max_step)
    chosen = c[stable]
    return chosen if len(chosen) >= minimum else c[np.isfinite(c)]


def estimate_tonic(cents: np.ndarray) -> float:
    """Tonic (Sa) pitch class in cents (0..1200): dominant stable histogram peak."""
    values = _stable_cents(cents)
    if len(values) == 0:
        return 0.0
    bins = 120  # 10-cent bins
    hist, _ = np.histogram(np.mod(values, 1200.0), bins=bins, range=(0, 1200))
    kernel = np.exp(-0.5 * (np.arange(-6, 7) / 2.0) ** 2)
    kernel /= kernel.sum()
    padded = np.concatenate([hist[-6:], hist, hist[:6]]).astype(float)
    smooth = np.convolve(padded, kernel, mode="valid")
    return float((int(np.argmax(smooth)) + 0.5) * (1200.0 / bins))


def pitch_statistics(cents: np.ndarray, min_class_fraction: float = 0.03) -> dict:
    """Tonic-relative pitch range, distinct swara-like positions, signature."""
    voiced = np.asarray(cents, dtype=float)
    voiced = voiced[np.isfinite(voiced)]
    if len(voiced) == 0:
        raise ValueError("no voiced frames")
    tonic = estimate_tonic(cents)
    rel = voiced - tonic
    pitch_range = float(np.percentile(rel, 95) - np.percentile(rel, 5))

    classes = (np.floor((np.mod(rel, 1200.0) + 50.0) / 100.0).astype(int)) % 12
    hist = np.bincount(classes, minlength=12) / len(classes)
    distinct = int(np.sum(hist >= min_class_fraction))
    signature = "".join(f"{int(round(h * 20)):02d}" for h in hist)
    return {
        "tonic_cents": tonic,
        "pitch_range_cents": round(pitch_range, 2),
        "distinct_pitch_count": distinct,
        "contour_signature": signature,
    }


# ----------------------------------------------------------------------
# Gamaka
# ----------------------------------------------------------------------
def gamaka_intensity(
    cents: np.ndarray,
    frames_per_second: float,
    transition_step: float = 10.0,
) -> float:
    """Normalised 0..1 ornamentation proxy.

    Combines (a) the fraction of consecutive voiced frames in motion rather
    than on a steady note and (b) local oscillation energy around a short
    moving average.  Steps are only measured between *adjacent* voiced
    frames, so gaps in the contour do not create fake jumps.
    """
    c = np.asarray(cents, dtype=float)
    if len(c) < 3:
        return 0.0
    both = np.isfinite(c[1:]) & np.isfinite(c[:-1])
    if both.sum() < 10:
        return 0.0
    steps = np.abs(np.diff(c))[both]
    moving = float(np.mean(steps > transition_step))

    window = max(3, int(round(0.2 * frames_per_second)) | 1)
    deviations = []
    finite = np.isfinite(c)
    idx = 0
    while idx < len(c):
        if not finite[idx]:
            idx += 1
            continue
        end = idx
        while end < len(c) and finite[end]:
            end += 1
        run = c[idx:end]
        if len(run) >= window + 2:
            trend = np.convolve(run, np.ones(window) / window, mode="valid")
            half = window // 2
            core = run[half : half + len(trend)]
            deviations.append(np.abs(core - trend))
        idx = end
    oscillation = float(np.mean(np.concatenate(deviations))) if deviations else 0.0

    score = 0.5 * clamp(moving / 0.4, 0, 1) + 0.5 * clamp(oscillation / 40.0, 0, 1)
    return round(clamp(score, 0, 1), 4)


# ----------------------------------------------------------------------
# Masked normalised correlation (shared by symmetry and cycle estimation)
# ----------------------------------------------------------------------
def _xcorr(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    """corr[l] = sum_t u[t] * v[t + l] for l = -(L-1) .. (L-1)."""
    length = len(u)
    size = 1 << (2 * length - 1).bit_length()
    full = np.fft.irfft(np.conj(np.fft.rfft(u, size)) * np.fft.rfft(v, size), size)
    return np.concatenate([full[size - (length - 1) :], full[:length]])


def masked_ncc(a, ma, b, mb, min_overlap: int) -> np.ndarray:
    """Normalised correlation of a with b at every lag, ignoring invalid samples.

    Returns values in [-1, 1] for lags -(L-1)..(L-1); NaN where fewer than
    ``min_overlap`` valid sample pairs overlap.
    """
    a = np.where(ma, a, 0.0)
    b = np.where(mb, b, 0.0)
    ma = ma.astype(float)
    mb = mb.astype(float)
    n = _xcorr(ma, mb)
    sa = _xcorr(a, mb)
    sb = _xcorr(ma, b)
    saa = _xcorr(a * a, mb)
    sbb = _xcorr(ma, b * b)
    sab = _xcorr(a, b)
    with np.errstate(divide="ignore", invalid="ignore"):
        num = sab - sa * sb / n
        den = np.sqrt(np.maximum(saa - sa**2 / n, 0) * np.maximum(sbb - sb**2 / n, 0))
        ncc = num / den
    ncc[(n < min_overlap) | ~np.isfinite(ncc) | (den < 1e-9)] = np.nan
    return np.clip(ncc, -1, 1)


def fill_short_gaps(values: np.ndarray, max_gap: int) -> np.ndarray:
    """Linearly interpolate NaN runs of at most ``max_gap`` frames."""
    out = np.array(values, dtype=float)
    n = len(out)
    i = 0
    while i < n:
        if np.isfinite(out[i]):
            i += 1
            continue
        j = i
        while j < n and not np.isfinite(out[j]):
            j += 1
        if i > 0 and j < n and (j - i) <= max_gap:
            out[i:j] = np.linspace(out[i - 1], out[j], j - i + 2)[1:-1]
        i = j
    return out


def _highpass(values: np.ndarray, mask: np.ndarray, window: int) -> np.ndarray:
    """Subtract a mask-aware moving average, leaving phrase shape only.

    Without this, slowly drifting contours correlate trivially with
    themselves at long lags and inflate the symmetry score.
    """
    kernel = np.ones(window)
    num = np.convolve(np.where(mask, values, 0.0), kernel, mode="same")
    den = np.convolve(mask.astype(float), kernel, mode="same")
    with np.errstate(divide="ignore", invalid="ignore"):
        local_mean = np.where(den > 0, num / den, 0.0)
    return np.where(mask, values - local_mean, 0.0)


# Normalised correlation of unrelated contours already reaches roughly this
# level at the best of many lags, so only the excess above it counts.
CHANCE_LEVEL = 0.75


def symmetry_score(
    cents: np.ndarray,
    frames_per_second: float,
    min_repeat_seconds: float = 1.5,
    min_overlap_seconds: float = 3.0,
    highpass_seconds: float = 2.0,
) -> float:
    """Proxy for phrase repetition and arohanam/avarohanam mirroring (0..1).

    * repetition: best normalised autocorrelation of the (high-passed) pitch
      contour at lags of at least ``min_repeat_seconds`` (short lags are
      trivially similar for any smooth contour and are excluded);
    * mirroring: best normalised correlation of the contour with its own time
      reversal over all mirror centres with enough overlap.

    The score is the stronger of the two, rescaled so chance-level similarity
    maps to 0 and an exact repeat or palindrome maps to 1.
    """
    c = fill_short_gaps(np.asarray(cents, dtype=float), int(0.3 * frames_per_second))
    mask = np.isfinite(c)
    length = len(c)
    min_overlap = int(min_overlap_seconds * frames_per_second)
    if mask.sum() < 2 * min_overlap or length < 2 * min_overlap:
        return 0.0
    x = _highpass(np.where(mask, c, 0.0), mask, int(highpass_seconds * frames_per_second) | 1)

    ncc = masked_ncc(x, mask, x, mask, min_overlap)
    lags = np.arange(-(length - 1), length)
    sel = lags >= int(min_repeat_seconds * frames_per_second)
    rep = np.nanmax(ncc[sel]) if np.any(np.isfinite(ncc[sel])) else 0.0

    rev_ncc = masked_ncc(x, mask, x[::-1], mask[::-1], min_overlap)
    rev = np.nanmax(rev_ncc) if np.any(np.isfinite(rev_ncc)) else 0.0

    best = max(float(rep), float(rev), 0.0)
    score = (best - CHANCE_LEVEL) / (1.0 - CHANCE_LEVEL)
    return round(clamp(score, 0, 1), 4)


# ----------------------------------------------------------------------
# Tempo confidence and cycle length (onset-envelope autocorrelation)
# ----------------------------------------------------------------------
def _autocorr(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    x = x - x.mean()
    energy = float(np.dot(x, x))
    if len(x) < 4 or energy < 1e-12:
        return np.zeros(max(len(x), 1))
    ac = _xcorr(x, x)[len(x) - 1 :]
    return ac / energy


def _peak_near(ac: np.ndarray, lag: float, tol: int) -> float:
    centre = int(round(lag))
    lo, hi = max(1, centre - tol), min(len(ac) - 1, centre + tol)
    if lo > hi:
        return 0.0
    return float(np.max(ac[lo : hi + 1]))


def tempo_confidence(onset_env: np.ndarray, frames_per_second: float, tempo_bpm: float) -> float:
    ac = _autocorr(onset_env)
    beat = frames_per_second * 60.0 / max(tempo_bpm, 1e-6)
    tol = max(1, int(0.08 * beat))
    return round(clamp(_peak_near(ac, beat, tol), 0, 1), 4)


def estimate_cycle(
    onset_env: np.ndarray,
    frames_per_second: float,
    tempo_bpm: float,
    min_confidence: float = 0.15,
    max_beats: int = 32,
) -> tuple[int | None, float]:
    """Return (cycle length in beats or None, confidence).

    This is a repetition proxy for a tala-like cycle, not tala recognition.
    """
    ac = _autocorr(onset_env)
    beat = frames_per_second * 60.0 / max(tempo_bpm, 1e-6)
    tol = max(1, int(0.08 * beat))
    scores = {}
    for k in range(2, max_beats + 1):
        lag = k * beat
        if lag + tol >= len(ac) * 0.6:
            break
        scores[k] = _peak_near(ac, lag, tol)
    if not scores:
        return None, 0.0
    best = max(scores.values())
    if best < min_confidence:
        return None, round(clamp(best, 0, 1), 4)
    # Prefer the smallest cycle whose score is within 3% of the best, so a
    # true period is not replaced by one of its multiples.
    cycle = min(k for k, s in scores.items() if s >= 0.97 * best)
    return int(cycle), round(clamp(scores[cycle], 0, 1), 4)
