from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from facebook_group_tool.domain.value_objects.post_mode import PostMode


@dataclass(frozen=True)
class SyncedGroupInput:
    name: str
    url: str
    facebook_group_id: str | None = None
    cover_image_url: str | None = None


@dataclass(frozen=True)
class CreatePostInput:
    title: str
    body_text: str
    media_paths: tuple[str, ...]


@dataclass(frozen=True)
class CreateCampaignInput:
    name: str
    post_id: UUID
    mode: PostMode
    target_group_ids: tuple[UUID, ...]
    daily_auto_limit: int
    min_delay_seconds: int
    max_delay_seconds: int


@dataclass(frozen=True)
class SafetyDetection:
    is_safe: bool
    reason: str | None = None


@dataclass(frozen=True)
class ComposerResult:
    status: str
    message: str


@dataclass(frozen=True)
class PreparePostCommand:
    group_url: str
    body_text: str
    media_paths: tuple[Path, ...]


@dataclass(frozen=True)
class RunWorkflowResult:
    status: str
    message: str
    prepared_count: int = 0
    posted_count: int = 0
    failed_count: int = 0
