from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from facebook_group_tool.domain.value_objects.campaign_status import CampaignStatus
from facebook_group_tool.domain.value_objects.post_mode import PostMode


@dataclass(frozen=True)
class Campaign:
    id: UUID
    name: str
    post_id: UUID
    mode: PostMode
    status: CampaignStatus
    daily_auto_limit: int
    min_delay_seconds: int
    max_delay_seconds: int
    scheduled_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        name: str,
        post_id: UUID,
        mode: PostMode,
        target_group_ids: tuple[UUID, ...],
        daily_auto_limit: int,
        min_delay_seconds: int,
        max_delay_seconds: int,
        scheduled_at: datetime | None,
    ) -> "Campaign":
        if not name.strip():
            raise ValueError("campaign name is required")
        if mode == PostMode.AUTO and len(target_group_ids) > 20:
            raise ValueError("Auto mode supports at most 20 targets")
        if mode == PostMode.AUTO and daily_auto_limit > 20:
            raise ValueError("daily_auto_limit cannot exceed 20")
        if min_delay_seconds < 300:
            raise ValueError("min_delay_seconds must be at least 300")
        if min_delay_seconds > max_delay_seconds:
            raise ValueError("min_delay_seconds must be <= max_delay_seconds")
        now = datetime.now(UTC)
        status = CampaignStatus.SCHEDULED if scheduled_at else CampaignStatus.DRAFT
        return cls(
            uuid4(),
            name.strip(),
            post_id,
            mode,
            status,
            daily_auto_limit,
            min_delay_seconds,
            max_delay_seconds,
            scheduled_at,
            now,
            now,
        )

    def mark_running(self) -> "Campaign":
        return replace(self, status=CampaignStatus.RUNNING, updated_at=datetime.now(UTC))

    def mark_paused(self) -> "Campaign":
        return replace(self, status=CampaignStatus.PAUSED, updated_at=datetime.now(UTC))
