import builtins
from typing import Protocol
from uuid import UUID

from facebook_group_tool.domain.entities.post import Post


class PostRepository(Protocol):
    async def get(self, post_id: UUID) -> Post | None: ...
    async def list(self) -> builtins.list[Post]: ...
    async def save(self, post: Post) -> Post: ...
