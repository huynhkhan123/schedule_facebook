from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from facebook_group_tool.domain.value_objects.post_mode import PostMode


class CreateCampaignRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    post_id: UUID
    mode: PostMode
    target_group_ids: list[UUID] = Field(min_length=1)
    daily_auto_limit: int = Field(ge=1, le=20)
    min_delay_seconds: int = Field(ge=300)
    max_delay_seconds: int = Field(ge=300)

    @model_validator(mode="after")
    def validate_auto_target_count(self) -> "CreateCampaignRequest":
        if self.mode == PostMode.AUTO and len(self.target_group_ids) > 20:
            raise ValueError("Auto mode supports at most 20 targets; switch to semi-auto mode")
        if self.min_delay_seconds > self.max_delay_seconds:
            raise ValueError("min_delay_seconds must be <= max_delay_seconds")
        return self


class CampaignResponse(BaseModel):
    id: UUID
    name: str
    post_id: UUID
    mode: PostMode
    status: str
    daily_auto_limit: int
    min_delay_seconds: int
    max_delay_seconds: int
