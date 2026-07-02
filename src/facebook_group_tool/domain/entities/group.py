from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Group:
    id: UUID
    facebook_group_id: str | None
    name: str
    url: str
    cover_image_url: str | None
    tags: tuple[str, ...]
    note: str
    is_enabled: bool
    is_posting_allowed: bool
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime

    def with_posting_permission(self, is_allowed: bool) -> "Group":
        return replace(self, is_posting_allowed=is_allowed)

    def with_tags(self, tags: tuple[str, ...]) -> "Group":
        return replace(self, tags=tuple(sorted(set(tags))))
