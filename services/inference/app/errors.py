from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AppError(Exception):
    code: str
    message: str
    detail: str | None = None
    retryable: bool = False
    status_code: int = 400

    def __str__(self) -> str:
        return self.message


class NotFoundError(AppError):
    def __init__(self, message: str, detail: str | None = None) -> None:
        super().__init__("not_found", message, detail=detail, status_code=404)


class ValidationAppError(AppError):
    def __init__(self, message: str, detail: str | None = None) -> None:
        super().__init__("validation_error", message, detail=detail, status_code=422)


class DependencyUnavailableError(AppError):
    def __init__(self, message: str, detail: str | None = None) -> None:
        super().__init__("dependency_unavailable", message, detail=detail, retryable=False, status_code=503)


class JobConflictError(AppError):
    def __init__(self, message: str, detail: str | None = None) -> None:
        super().__init__("job_conflict", message, detail=detail, retryable=False, status_code=409)
