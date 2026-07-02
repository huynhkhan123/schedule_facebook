from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from facebook_group_tool.domain.value_objects.target_status import TargetStatus


@dataclass(frozen=True)
class CampaignTarget:
    id: UUID
    campaign_id: UUID
    group_id: UUID
    status: TargetStatus
    attempt_count: int
    last_error: str | None
    prepared_at: datetime | None
    posted_at: datetime | None
    next_run_at: datetime | None

    def with_status(self, status: TargetStatus, error: str | None = None) -> "CampaignTarget":
        return replace(self, status=status, last_error=error)
