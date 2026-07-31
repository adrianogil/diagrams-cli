"""Application errors raised while loading diagram descriptions."""


class DiagramError(ValueError):
    """Base class for expected diagram input errors."""


class DiagramLoadError(DiagramError):
    """Raised when diagram input cannot be read or decoded as JSON."""


class DiagramValidationError(DiagramError):
    """Raised when decoded JSON does not match the diagram schema."""
