# pyright: reportUnusedFunction=false

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from facebook_group_tool.config import get_settings
from facebook_group_tool.presentation.api.routes import (
    automation,
    campaigns,
    connectors,
    groups,
    posts,
)
from facebook_group_tool.presentation.web.routes import router as web_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Facebook Group Tool", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins(),
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "environment": settings.app_env}

    static_dir = Path(__file__).parent / "presentation" / "web" / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    app.include_router(groups.router, prefix="/api/groups", tags=["groups"])
    app.include_router(posts.router, prefix="/api/posts", tags=["posts"])
    app.include_router(campaigns.router, prefix="/api/campaigns", tags=["campaigns"])
    app.include_router(automation.router, prefix="/api/automation", tags=["automation"])
    app.include_router(connectors.router, prefix="/api/connectors", tags=["connectors"])
    app.include_router(web_router)

    return app


app = create_app()
