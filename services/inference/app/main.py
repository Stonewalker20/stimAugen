from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deps import ServiceContainer
from app.api.errors import install_error_handlers
from app.api.routes import exports, health, isolation, jobs, profiles, settings, tts, voice_conversion
from app.services.runtime import build_service_container

LOCAL_ORIGINS = [
    "http://127.0.0.1:1420",
    "http://localhost:1420",
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.services = await build_service_container()
    try:
        yield
    finally:
        services: ServiceContainer = app.state.services
        shutdown = getattr(services, "shutdown", None)
        if shutdown is not None:
            await shutdown()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Home Voice Studio Inference API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=LOCAL_ORIGINS,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_error_handlers(app)
    app.include_router(health.router)
    app.include_router(tts.router)
    app.include_router(voice_conversion.router)
    app.include_router(isolation.router)
    app.include_router(profiles.router)
    app.include_router(jobs.router)
    app.include_router(exports.router)
    app.include_router(settings.router)
    return app


app = create_app()
