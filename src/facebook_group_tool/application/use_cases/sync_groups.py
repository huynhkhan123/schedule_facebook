from datetime import UTC, datetime
from uuid import uuid4

from facebook_group_tool.application.dto import SyncedGroupInput
from facebook_group_tool.domain.entities.group import Group
from facebook_group_tool.domain.repositories.group_repository import GroupRepository


class SyncGroupsUseCase:
    def __init__(self, group_repository: GroupRepository) -> None:
        self._group_repository = group_repository

    async def execute(self, inputs: list[SyncedGroupInput]) -> list[Group]:
        deduped: dict[str, SyncedGroupInput] = {}
        for group_input in inputs:
            normalized_url = self._normalize_url(group_input.url)
            key = (
                f"id:{group_input.facebook_group_id}"
                if group_input.facebook_group_id
                else f"url:{normalized_url}"
            )
            deduped[key] = SyncedGroupInput(
                name=group_input.name.strip(),
                url=normalized_url,
                facebook_group_id=group_input.facebook_group_id,
                cover_image_url=group_input.cover_image_url,
            )

        now = datetime.now(UTC)
        groups = [
            Group(
                id=uuid4(),
                facebook_group_id=item.facebook_group_id,
                name=item.name,
                url=item.url,
                cover_image_url=item.cover_image_url,
                tags=(),
                note="",
                is_enabled=True,
                is_posting_allowed=False,
                last_synced_at=now,
                created_at=now,
                updated_at=now,
            )
            for item in deduped.values()
            if item.name and item.url
        ]
        return await self._group_repository.upsert_many(groups)

    def _normalize_url(self, url: str) -> str:
        return url.strip().rstrip("/")
