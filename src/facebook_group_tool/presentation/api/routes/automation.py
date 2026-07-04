from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from facebook_group_tool.application.use_cases.dispatch_connector_job import (
    DispatchConnectorJobUseCase,
)
from facebook_group_tool.infrastructure.automation.facebook_group_urls import (
    normalize_facebook_group_url,
)
from facebook_group_tool.presentation.api.dependencies import get_dispatch_connector_job_use_case
from facebook_group_tool.presentation.api.routes.connectors import notify_connector_job_available

router = APIRouter()

DispatchConnectorJobDependency = Annotated[
    DispatchConnectorJobUseCase,
    Depends(get_dispatch_connector_job_use_case),
]


class OpenGroupRequest(BaseModel):
    url: str = Field(min_length=1)


def sync_response(
    status: str,
    synced_count: int,
    message: str = "",
    **extra: object,
) -> dict[str, object]:
    return {"status": status, "synced_count": synced_count, "message": message, **extra}


async def dispatch_group_sync_job(
    use_case: DispatchConnectorJobDependency,
    job_type: str,
    message: str,
) -> dict[str, object]:
    job = await dispatch_connector_job(use_case, job_type, {})
    return sync_response("syncing_visible_groups", 0, message, job_id=str(job.id))


async def dispatch_connector_job(
    use_case: DispatchConnectorJobDependency,
    job_type: str,
    payload: dict[str, object],
):
    try:
        job = await use_case.execute(job_type=job_type, payload=payload)
    except RuntimeError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    await notify_connector_job_available(job)
    return job


@router.get("/status")
async def automation_status() -> dict[str, str]:
    return {"status": "idle"}


@router.get("/group-sync/status")
async def group_sync_status() -> dict[str, object]:
    return sync_response("idle", 0)


@router.post("/group-sync/start")
async def start_group_sync(
    use_case: DispatchConnectorJobDependency,
) -> dict[str, object]:
    return await dispatch_group_sync_job(
        use_case,
        "group_sync.start",
        "Đã gửi lệnh mở browser xuống desktop connector.",
    )


@router.post("/group-sync/collect-visible")
async def collect_visible_groups(
    use_case: DispatchConnectorJobDependency,
) -> dict[str, object]:
    return await dispatch_group_sync_job(
        use_case,
        "group_sync.collect_visible",
        "Đã gửi lệnh thu thập nhóm đang hiển thị xuống desktop connector.",
    )


@router.post("/group-sync/stop")
async def stop_group_sync(
    use_case: DispatchConnectorJobDependency,
) -> dict[str, object]:
    return await dispatch_group_sync_job(
        use_case,
        "group_sync.stop",
        "Đã gửi lệnh dừng sync xuống desktop connector.",
    )


@router.post("/groups/open")
async def open_group_in_connector(
    request: OpenGroupRequest,
    use_case: DispatchConnectorJobDependency,
) -> dict[str, object]:
    normalized_url = normalize_facebook_group_url(request.url)
    if normalized_url is None:
        raise HTTPException(status_code=422, detail="Only Facebook group URLs can be opened")
    job = await dispatch_connector_job(use_case, "group.open", {"url": normalized_url})
    return sync_response(
        "opening_browser",
        0,
        "Đã gửi lệnh mở nhóm trong browser của desktop connector.",
        job_id=str(job.id),
    )
