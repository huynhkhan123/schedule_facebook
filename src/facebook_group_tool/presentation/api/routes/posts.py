from typing import Annotated

from fastapi import APIRouter, Depends, status

from facebook_group_tool.application.dto import CreatePostInput
from facebook_group_tool.application.use_cases.create_post import CreatePostUseCase
from facebook_group_tool.domain.entities.post import Post
from facebook_group_tool.presentation.api.dependencies import (
    get_create_post_use_case,
    post_repository,
)
from facebook_group_tool.presentation.api.schemas.post_schema import CreatePostRequest, PostResponse

router = APIRouter()

CreatePostDependency = Annotated[CreatePostUseCase, Depends(get_create_post_use_case)]


def to_post_response(post: Post) -> PostResponse:
    return PostResponse(
        id=post.id,
        title=post.title,
        body_text=post.body_text,
        media_items=list(post.media_items),
    )


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    request: CreatePostRequest,
    use_case: CreatePostDependency,
) -> PostResponse:
    post = await use_case.execute(
        CreatePostInput(
            title=request.title,
            body_text=request.body_text,
            media_paths=tuple(request.media_paths),
        )
    )
    return to_post_response(post)


@router.get("", response_model=list[PostResponse])
async def list_posts() -> list[PostResponse]:
    posts = await post_repository.list()
    return [to_post_response(post) for post in posts]
