import builtins
from typing import Protocol
from uuid import UUID

from facebook_group_tool.domain.entities.run_log import RunLog


class RunLogRepository(Protocol):
    async def append(self, log: RunLog) -> RunLog: ...
    async def list_for_campaign(self, campaign_id: UUID) -> builtins.list[RunLog]: ...
