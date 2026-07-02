from uuid import UUID

from pydantic import BaseModel, Field


class GroupResponse(BaseModel):
    id: UUID
    facebook_group_id: str | None
    name: str
    url: str
    cover_image_url: str | None
    tags: list[str]
    note: str
    is_enabled: bool
    is_posting_allowed: bool


class SyncedGroupRequest(BaseModel):
    name: str = Field(min_length=1)
    url: str = Field(min_length=1)
    facebook_group_id: str | None = None
    cover_image_url: str | None = None


class MarkPermissionRequest(BaseModel):
    is_posting_allowed: bool
