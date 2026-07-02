from uuid import UUID

from facebook_group_tool.application.dto import RunWorkflowResult
from facebook_group_tool.application.use_cases.run_campaign import RunCampaignUseCase


class RunQuickPostUseCase:
    def __init__(self, run_campaign_use_case: RunCampaignUseCase) -> None:
        self._run_campaign_use_case = run_campaign_use_case

    async def execute(self, campaign_id: UUID, *, dry_run: bool) -> RunWorkflowResult:
        return await self._run_campaign_use_case.execute(campaign_id, dry_run=dry_run)
