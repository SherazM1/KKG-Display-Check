"""Small exception adapters with stable, JSON-safe error envelopes."""

import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.schemas import ErrorCode, ErrorDetail, ErrorResponse, ValidationIssue
from app.v2.services.display_resolver import DisplayResolutionError
from app.v2.services.display_knowledge_service import DisplayKnowledgeError
from app.v2.services.estimate_basis_service import EstimateBasisError


logger = logging.getLogger(__name__)


class ProjectNotReadyError(ValueError):
    """Validated intake did not satisfy domain readiness."""


DOMAIN_ERRORS: dict[type[Exception], tuple[int, ErrorCode]] = {
    ProjectNotReadyError: (400, "PROJECT_NOT_READY"),
    DisplayResolutionError: (422, "DISPLAY_RESOLUTION_FAILED"),
    DisplayKnowledgeError: (422, "DISPLAY_KNOWLEDGE_UNAVAILABLE"),
    EstimateBasisError: (422, "ESTIMATE_BASIS_FAILED"),
}


def error_response(
    status: int, code: ErrorCode, message: str,
    *, details: list[ValidationIssue] | None = None, request_id: str | None = None,
) -> JSONResponse:
    envelope = ErrorResponse(error=ErrorDetail(
        code=code, message=message,
        field=details[0].field if details else None,
        details=details, request_id=request_id or str(uuid4()),
    ))
    return JSONResponse(status_code=status, content=envelope.model_dump(mode="json"))


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Never echo raw input/ctx: these can contain NaN, exceptions, or user data.
    issues = [ValidationIssue(
        field=".".join(str(part) for part in error["loc"]),
        message=error["msg"], type=error["type"],
    ) for error in exc.errors()]
    return error_response(400, "INVALID_REQUEST", "Request validation failed.", details=issues)


async def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    for error_type, (status, code) in DOMAIN_ERRORS.items():
        if isinstance(exc, error_type):
            return error_response(status, code, str(exc))
    return await internal_error_handler(request, exc)


async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = str(uuid4())
    logger.error("API failure request_id=%s", request_id, exc_info=exc)
    return error_response(
        500, "INTERNAL_ERROR", "An unexpected error occurred.", request_id=request_id,
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    for error_type in DOMAIN_ERRORS:
        app.add_exception_handler(error_type, domain_error_handler)
    app.add_exception_handler(Exception, internal_error_handler)
