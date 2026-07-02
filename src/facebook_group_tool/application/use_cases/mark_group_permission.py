from uuid import UUID

from facebook_group_tool.domain.entities.group import Group
from facebook_group_tool.domain.repositories.group_repository import GroupRepository


class GroupNotFoundError(Exception):
    pass


class MarkGroupPermissionUseCase:
    def __init__(self, group_repository: GroupRepository) -> None:
        self._group_repository = group_repository

    async def execute(self, group_id: UUID, is_allowed: bool) -> Group:
        group = await self._group_repository.get(group_id)
        if group is None:
            raise GroupNotFoundError(f"Group not found: {group_id}")
        updated = group.with_posting_permission(is_allowed)
        return await self._group_repository.save(updated)
