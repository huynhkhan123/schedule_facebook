from typing import Annotated

from fastapi import APIRouter, Depends

from facebook_group_tool.application.dto import SyncedGroupInput
from facebook_group_tool.application.use_cases.sync_groups import SyncGroupsUseCase
from facebook_group_tool.infrastructure.automation.group_sync_session import (
    GroupSyncSessionService,
)
from facebook_group_tool.presentation.api.dependencies import (
    get_group_sync_session,
    get_sync_groups_use_case,
)

router = APIRouter()

GroupSyncSessionDependency = Annotated[GroupSyncSessionService, Depends(get_group_sync_session)]
SyncGroupsDependency = Annotated[SyncGroupsUseCase, Depends(get_sync_groups_use_case)]


def sync_response(status: str, synced_count: int, message: str = "") -> dict[str, object]:
    return {"status": status, "synced_count": synced_count, "message": message}


@router.get("/status")
async def automation_status() -> dict[str, str]:
    return {"status": "idle"}


@router.get("/group-sync/status")
async def group_sync_status(
    session: GroupSyncSessionDependency,
) -> dict[str, object]:
    status = session.status()
    return sync_response(status.status, status.synced_count, status.message)


@router.post("/group-sync/start")
async def start_group_sync(
    session: GroupSyncSessionDependency,
) -> dict[str, object]:
    status = await session.start()
    return sync_response(status.status, status.synced_count, status.message)


@router.post("/group-sync/collect-visible")
async def collect_visible_groups(
    session: GroupSyncSessionDependency,
    sync_groups: SyncGroupsDependency,
) -> dict[str, object]:
    status, visible_groups = await session.collect_visible_groups()
    synced = await sync_groups.execute(
        [
            SyncedGroupInput(
                name=group.name,
                url=group.url,
                facebook_group_id=group.facebook_group_id,
                cover_image_url=group.cover_image_url,
            )
            for group in visible_groups
        ]
    )
    return sync_response(status.status, len(synced), status.message)


@router.post("/group-sync/stop")
async def stop_group_sync(
    session: GroupSyncSessionDependency,
) -> dict[str, object]:
    status = await session.stop()
    return sync_response(status.status, status.synced_count, status.message)
