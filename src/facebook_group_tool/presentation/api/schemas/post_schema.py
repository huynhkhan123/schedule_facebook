from uuid import UUID

from pydantic import BaseModel, Field


class CreatePostRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body_text: str = ""
    media_paths: list[str] = Field(default_factory=list)


class PostResponse(BaseModel):
    id: UUID
    title: str
    body_text: str
    media_items: list[str]
