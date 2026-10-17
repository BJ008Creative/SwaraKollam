"""Audio error types, mapped to HTTP status codes by the API layer."""


class AudioError(Exception):
    """Base class for audio problems caused by the uploaded file."""


class AudioDecodeError(AudioError):
    """The file could not be decoded as audio (HTTP 400)."""


class AudioTooShortError(AudioError):
    """Decoded audio is too short to analyse (HTTP 422)."""


class NoVoicedContentError(AudioError):
    """No usable pitched/voiced content was found (HTTP 422)."""
