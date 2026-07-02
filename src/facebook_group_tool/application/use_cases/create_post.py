from facebook_group_tool.application.dto import CreatePostInput
from facebook_group_tool.domain.entities.post import Post
from facebook_group_tool.domain.repositories.post_repository import PostRepository


class CreatePostUseCase:
    def __init__(self, post_repository: PostRepository) -> None:
        self._post_repository = post_repository

    async def execute(self, data: CreatePostInput) -> Post:
        post = Post.create(data.title, data.body_text, data.media_paths)
        return await self._post_repository.save(post)
