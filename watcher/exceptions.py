"""Custom exception hierarchy for VeilleAI application."""


class VeilleAIException(Exception):
    """Base exception for all VeilleAI errors."""

    pass


class ConfigError(VeilleAIException):
    """Configuration-related errors."""

    pass


class ConfigValidationError(ConfigError):
    """Configuration validation failed."""

    pass


class ConfigMissingKeyError(ConfigError):
    """Required configuration key is missing."""

    pass


class ConfigInvalidValueError(ConfigError):
    """Configuration value is invalid."""

    pass


class CollectorError(VeilleAIException):
    """Error in data collection phase."""

    pass


class FilterError(VeilleAIException):
    """Error in filtering/scoring phase."""

    pass


class StorageError(VeilleAIException):
    """Error accessing storage (SQLite, ChromaDB)."""

    pass


class SynthesizerError(VeilleAIException):
    """Error during synthesis/LLM generation."""

    pass


class SchedulerError(VeilleAIException):
    """Error in scheduler operations."""

    pass


class LLMProviderError(VeilleAIException):
    """Error with LLM provider initialization or API call."""

    pass


class NetworkError(VeilleAIException):
    """Network-related errors (API timeouts, connection failures)."""

    pass


class DataValidationError(VeilleAIException):
    """Data validation failed (e.g., article structure)."""

    pass
