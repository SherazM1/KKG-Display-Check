"""ASGI entry point for Display Check's thin API adapter."""

from fastapi import FastAPI

from api.errors import register_error_handlers
from api.routes import displays, health, projects
from api.schemas import ErrorResponse


app = FastAPI(title="Display Check v2", responses={
    400: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
})
register_error_handlers(app)
app.include_router(health.router, prefix="/api")
app.include_router(displays.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
