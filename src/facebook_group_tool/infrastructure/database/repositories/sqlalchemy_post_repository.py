from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from facebook_group_tool.domain.entities.post import Post
from facebook_group_tool.infrastructure.database.models import PostModel


def to_domain(model: PostModel) -> Post:
    return Post(
        id=model.id,
        title=model.title,
        body_text=model.body_text,
        link_url=model.link_url,
        video_path=model.video_path,
        media_items=tuple(model.media_items),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def from_domain(post: Post) -> PostModel:
    return PostModel(
        id=post.id,
        title=post.title,
        body_text=post.body_text,
        link_url=post.link_url,
        video_path=post.video_path,
        media_items=list(post.media_items),
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


class SqlAlchemyPostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, post_id: object) -> Post | None:
        model = await self._session.get(PostModel, post_id)
        return to_domain(model) if model else None

    async def list(self) -> list[Post]:
        statement = select(PostModel).order_by(PostModel.created_at.desc())
        result = await self._session.execute(statement)
        return [to_domain(model) for model in result.scalars().all()]

    async def save(self, post: Post) -> Post:
        merged = await self._session.merge(from_domain(post))
        await self._session.commit()
        await self._session.refresh(merged)
        return to_domain(merged)
