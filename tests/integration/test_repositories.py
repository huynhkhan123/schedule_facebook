import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from facebook_group_tool.domain.entities.group import Group
from facebook_group_tool.infrastructure.database.models import Base
from facebook_group_tool.infrastructure.database.repositories.sqlalchemy_group_repository import (
    SqlAlchemyGroupRepository,
)

pytestmark = pytest.mark.integration


def make_group(*, facebook_group_id: str | None, name: str) -> Group:
    now = datetime.now(UTC)
    return Group(
        id=uuid4(),
        facebook_group_id=facebook_group_id,
        name=name,
        url=f"https://facebook.com/groups/{facebook_group_id or name.lower().replace(' ', '-')}",
        cover_image_url=None,
        tags=("promo",),
        note="",
        is_enabled=True,
        is_posting_allowed=False,
        last_synced_at=now,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    database_url = os.getenv("DATABASE_URL_TEST")
    if not database_url:
        pytest.skip("DATABASE_URL_TEST is required for PostgreSQL integration tests")
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as db_session:
        yield db_session
    await engine.dispose()


@pytest.mark.asyncio
async def test_group_repository_upserts_by_facebook_group_id(session: AsyncSession) -> None:
    repo = SqlAlchemyGroupRepository(session)
    first = make_group(facebook_group_id="123", name="Original")
    second = make_group(facebook_group_id="123", name="Updated")

    await repo.upsert_many([first])
    await repo.upsert_many([second])
    groups = await repo.list()

    assert len(groups) == 1
    assert groups[0].name == "Updated"
