from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from facebook_group_tool.domain.value_objects.run_log_level import RunLogLevel


@dataclass(frozen=True)
class RunLog:
    id: UUID
    campaign_id: UUID | None
    campaign_target_id: UUID | None
    level: RunLogLevel
    event_type: str
    message: str
    metadata: dict[str, object]
    created_at: datetime
