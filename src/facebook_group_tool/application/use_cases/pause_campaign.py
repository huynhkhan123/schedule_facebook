from uuid import UUID

from facebook_group_tool.domain.entities.campaign import Campaign
from facebook_group_tool.domain.repositories.campaign_repository import CampaignRepository


class CampaignNotFoundError(Exception):
    pass


class PauseCampaignUseCase:
    def __init__(self, campaign_repository: CampaignRepository) -> None:
        self._campaign_repository = campaign_repository

    async def execute(self, campaign_id: UUID) -> Campaign:
        campaign = await self._campaign_repository.get(campaign_id)
        if campaign is None:
            raise CampaignNotFoundError(f"Campaign not found: {campaign_id}")
        return await self._campaign_repository.save(campaign.mark_paused())
