from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.admin import setup_sqladmin
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.connections import lifespan


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=settings.api_prefix)
    setup_sqladmin(app)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
