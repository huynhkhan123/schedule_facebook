from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from facebook_group_tool.application.dto import CreatePostInput, SyncedGroupInput
from facebook_group_tool.application.use_cases.create_post import CreatePostUseCase
from facebook_group_tool.application.use_cases.mark_group_permission import (
    MarkGroupPermissionUseCase,
)
from facebook_group_tool.application.use_cases.sync_groups import SyncGroupsUseCase
from facebook_group_tool.domain.entities.group import Group
from facebook_group_tool.domain.entities.post import Post


class FakePostRepository:
    def __init__(self) -> None:
        self.saved: list[Post] = []

    async def get(self, post_id: UUID) -> Post | None:
        return next((post for post in self.saved if post.id == post_id), None)

    async def list(self) -> list[Post]:
        return self.saved

    async def save(self, post: Post) -> Post:
        self.saved = [*self.saved, post]
        return post


class FakeGroupRepository:
    def __init__(self, groups: list[Group] | None = None) -> None:
        self.groups = groups or []
        self.saved_groups: list[Group] = []

    async def get(self, group_id: UUID) -> Group | None:
        return next((group for group in self.groups if group.id == group_id), None)

    async def list(self, *, enabled_only: bool = False) -> list[Group]:
        if enabled_only:
            return [group for group in self.groups if group.is_enabled]
        return self.groups

    async def save(self, group: Group) -> Group:
        self.groups = [candidate for candidate in self.groups if candidate.id != group.id]
        self.groups = [*self.groups, group]
        return group

    async def upsert_many(self, groups: list[Group]) -> list[Group]:
        self.saved_groups = groups
        self.groups = groups
        return groups


def make_group(*, is_posting_allowed: bool = False) -> Group:
    now = datetime.now(UTC)
    return Group(
        id=uuid4(),
        facebook_group_id="123",
        name="Allowed Group",
        url="https://facebook.com/groups/123",
        cover_image_url=None,
        tags=(),
        note="",
        is_enabled=True,
        is_posting_allowed=is_posting_allowed,
        last_synced_at=now,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_create_post_saves_post() -> None:
    repository = FakePostRepository()
    use_case = CreatePostUseCase(repository)

    saved_post = await use_case.execute(
        CreatePostInput(title="Launch", body_text="Hello", media_paths=())
    )

    assert saved_post.title == "Launch"


@pytest.mark.asyncio
async def test_sync_groups_deduplicates_visible_groups_by_id() -> None:
    repository = FakeGroupRepository()
    use_case = SyncGroupsUseCase(repository)

    saved_groups = await use_case.execute(
        [
            SyncedGroupInput(
                name="Group A",
                url="https://facebook.com/groups/123/",
                facebook_group_id="123",
            ),
            SyncedGroupInput(
                name="Group A Updated",
                url="https://facebook.com/groups/123",
                facebook_group_id="123",
            ),
        ]
    )

    assert len(saved_groups) == 1


@pytest.mark.asyncio
async def test_mark_group_permission_updates_immutably() -> None:
    group = make_group(is_posting_allowed=False)
    repository = FakeGroupRepository([group])
    use_case = MarkGroupPermissionUseCase(repository)

    updated_group = await use_case.execute(group.id, True)

    assert group.is_posting_allowed is False
    assert updated_group.is_posting_allowed is True
