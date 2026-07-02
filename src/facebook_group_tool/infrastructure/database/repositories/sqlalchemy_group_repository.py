from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from facebook_group_tool.domain.entities.group import Group
from facebook_group_tool.infrastructure.database.models import GroupModel


def to_domain(model: GroupModel) -> Group:
    return Group(
        id=model.id,
        facebook_group_id=model.facebook_group_id,
        name=model.name,
        url=model.url,
        cover_image_url=model.cover_image_url,
        tags=tuple(model.tags),
        note=model.note,
        is_enabled=model.is_enabled,
        is_posting_allowed=model.is_posting_allowed,
        last_synced_at=model.last_synced_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def from_domain(group: Group) -> GroupModel:
    return GroupModel(
        id=group.id,
        facebook_group_id=group.facebook_group_id,
        name=group.name,
        url=group.url,
        cover_image_url=group.cover_image_url,
        tags=list(group.tags),
        note=group.note,
        is_enabled=group.is_enabled,
        is_posting_allowed=group.is_posting_allowed,
        last_synced_at=group.last_synced_at,
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


class SqlAlchemyGroupRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, group_id: object) -> Group | None:
        model = await self._session.get(GroupModel, group_id)
        return to_domain(model) if model else None

    async def list(self, *, enabled_only: bool = False) -> list[Group]:
        statement = select(GroupModel).order_by(GroupModel.name)
        if enabled_only:
            statement = statement.where(GroupModel.is_enabled.is_(True))
        result = await self._session.execute(statement)
        return [to_domain(model) for model in result.scalars().all()]

    async def save(self, group: Group) -> Group:
        merged = await self._session.merge(from_domain(group))
        await self._session.commit()
        await self._session.refresh(merged)
        return to_domain(merged)

    async def upsert_many(self, groups: list[Group]) -> list[Group]:
        for group in groups:
            values = {
                "id": group.id,
                "facebook_group_id": group.facebook_group_id,
                "name": group.name,
                "url": group.url,
                "cover_image_url": group.cover_image_url,
                "tags": list(group.tags),
                "note": group.note,
                "is_enabled": group.is_enabled,
                "is_posting_allowed": group.is_posting_allowed,
                "last_synced_at": group.last_synced_at,
                "created_at": group.created_at,
                "updated_at": group.updated_at,
            }
            statement = insert(GroupModel).values(**values)
            conflict_target = ["facebook_group_id"] if group.facebook_group_id else ["url"]
            statement = statement.on_conflict_do_update(
                index_elements=conflict_target,
                set_={
                    "name": statement.excluded.name,
                    "url": statement.excluded.url,
                    "cover_image_url": statement.excluded.cover_image_url,
                    "last_synced_at": statement.excluded.last_synced_at,
                    "updated_at": statement.excluded.updated_at,
                },
            )
            await self._session.execute(statement)
        await self._session.commit()
        return await self.list()
