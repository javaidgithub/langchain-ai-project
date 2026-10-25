class AppError(Exception):
    """Base class for errors that should be shown to the user."""

    status_code = 400

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if status_code:
            self.status_code = status_code


class ProviderNotConfigured(AppError):
    status_code = 400


class NotFound(AppError):
    status_code = 404
