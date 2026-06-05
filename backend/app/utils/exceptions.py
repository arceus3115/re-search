"""
Custom exception classes for the application.
"""


class ApplicationError(Exception):
    """Base exception for all application errors."""

    pass


class OpenAlexAPIError(ApplicationError):
    """Raised when OpenAlex API calls fail."""

    pass


class ProfileNotFoundError(ApplicationError):
    """Raised when a profile is not found."""

    pass


class ProfileStorageError(ApplicationError):
    """Raised when profile storage operations fail."""

    pass


class DocumentParsingError(ApplicationError):
    """Raised when document parsing fails."""

    pass


class AIGenerationError(ApplicationError):
    """Raised when AI content generation fails."""

    pass


class ValidationError(ApplicationError):
    """Raised when input validation fails."""

    pass


class ClinicalTrialsAPIError(ApplicationError):
    """Raised when ClinicalTrials.gov API calls fail."""

    pass


class TrialNotFoundError(ApplicationError):
    """Raised when no clinical trials are found for a PI."""

    pass


class NIHReporterAPIError(ApplicationError):
    """Raised when NIH Reporter API calls fail."""

    pass


class ScrapingError(ApplicationError):
    """Raised when web scraping fails or returns invalid data."""

    pass
