"""Expected application errors for diagram conversion workflows."""


class DiagramError(ValueError):
    """Base class for expected diagram input errors."""


class DiagramLoadError(DiagramError):
    """Raised when diagram input cannot be read or decoded as JSON."""


class DiagramValidationError(DiagramError):
    """Raised when decoded JSON does not match the diagram schema."""


class DiagramOutputError(DiagramError):
    """Raised when generated output cannot be safely written."""
