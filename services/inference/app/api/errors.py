from __future__ import annotations

from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.models.common import ErrorEnvelope, StructuredError


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = HTTPStatus.BAD_REQUEST,
        details: str | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.error = StructuredError(
            code=code,
            message=message,
            details=details,
            retryable=retryable,
        )
        self.status_code = int(status_code)


class NotFoundError(AppError):
    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            code=f"{resource}_not_found",
            message=f"{resource.replace('_', ' ').title()} was not found.",
            status_code=HTTPStatus.NOT_FOUND,
            details=f"Missing resource id: {identifier}",
        )


class ConflictError(AppError):
    def __init__(self, code: str, message: str, *, details: str | None = None) -> None:
        super().__init__(code=code, message=message, status_code=HTTPStatus.CONFLICT, details=details)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorEnvelope(error=exc.error).model_dump(mode="json"),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
        error = StructuredError(
            code="internal_error",
            message="The request could not be completed.",
            details=str(exc),
            retryable=False,
        )
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            content=ErrorEnvelope(error=error).model_dump(mode="json"),
        )
