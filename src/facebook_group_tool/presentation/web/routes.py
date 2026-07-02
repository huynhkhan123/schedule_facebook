from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from facebook_group_tool.presentation.api.dependencies import group_repository

TEMPLATE_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
router = APIRouter()


@router.get("/")
async def overview(request: Request):
    return templates.TemplateResponse(
        request,
        "overview.html",
        {
            "synced_groups": 0,
            "active_campaigns": 0,
            "auto_posts_used_today": 0,
            "needs_user_action": 0,
        },
    )


@router.get("/groups")
async def groups(request: Request):
    synced_groups = await group_repository.list()
    return templates.TemplateResponse(
        request,
        "groups.html",
        {"groups": synced_groups},
    )


@router.get("/posts")
async def posts(request: Request):
    return templates.TemplateResponse(request, "posts.html", {})


@router.get("/campaigns")
async def campaigns(request: Request):
    return templates.TemplateResponse(request, "campaigns.html", {})


@router.get("/logs")
async def logs(request: Request):
    return templates.TemplateResponse(request, "logs.html", {})
