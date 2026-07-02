from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from facebook_group_tool.application.dto import SyncedGroupInput
from facebook_group_tool.application.use_cases.mark_group_permission import (
    MarkGroupPermissionUseCase,
)
from facebook_group_tool.application.use_cases.sync_groups import SyncGroupsUseCase
from facebook_group_tool.domain.entities.group import Group
from facebook_group_tool.presentation.api.dependencies import (
    get_mark_group_permission_use_case,
    get_sync_groups_use_case,
    group_repository,
)
from facebook_group_tool.presentation.api.schemas.group_schema import (
    GroupResponse,
    MarkPermissionRequest,
    SyncedGroupRequest,
)

router = APIRouter()

SyncGroupsDependency = Annotated[SyncGroupsUseCase, Depends(get_sync_groups_use_case)]
MarkGroupPermissionDependency = Annotated[
    MarkGroupPermissionUseCase,
    Depends(get_mark_group_permission_use_case),
]


def to_group_response(group: Group) -> GroupResponse:
    return GroupResponse(
        id=group.id,
        facebook_group_id=group.facebook_group_id,
        name=group.name,
        url=group.url,
        cover_image_url=group.cover_image_url,
        tags=list(group.tags),
        note=group.note,
        is_enabled=group.is_enabled,
        is_posting_allowed=group.is_posting_allowed,
    )


@router.get("", response_model=list[GroupResponse])
async def list_groups() -> list[GroupResponse]:
    groups = await group_repository.list()
    return [to_group_response(group) for group in groups]


@router.post("/sync-visible", response_model=list[GroupResponse])
async def sync_visible_groups(
    request: list[SyncedGroupRequest],
    use_case: SyncGroupsDependency,
) -> list[GroupResponse]:
    groups = await use_case.execute(
        [
            SyncedGroupInput(
                name=item.name,
                url=item.url,
                facebook_group_id=item.facebook_group_id,
                cover_image_url=item.cover_image_url,
            )
            for item in request
        ]
    )
    return [to_group_response(group) for group in groups]


@router.patch("/{group_id}/permission", response_model=GroupResponse)
async def mark_permission(
    group_id: UUID,
    request: MarkPermissionRequest,
    use_case: MarkGroupPermissionDependency,
) -> GroupResponse:
    try:
        group = await use_case.execute(group_id, request.is_posting_allowed)
    except Exception as error:
        raise HTTPException(status_code=404, detail="Group not found") from error
    return to_group_response(group)
