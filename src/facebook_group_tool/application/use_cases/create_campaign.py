from datetime import UTC, datetime
from uuid import uuid4

from facebook_group_tool.application.dto import CreateCampaignInput
from facebook_group_tool.application.services.safety_guard import SafetyGuard
from facebook_group_tool.domain.entities.campaign import Campaign
from facebook_group_tool.domain.entities.campaign_target import CampaignTarget
from facebook_group_tool.domain.repositories.campaign_repository import CampaignRepository
from facebook_group_tool.domain.value_objects.post_mode import PostMode
from facebook_group_tool.domain.value_objects.target_status import TargetStatus


class CreateCampaignUseCase:
    def __init__(
        self,
        campaign_repository: CampaignRepository,
        safety_guard: SafetyGuard,
    ) -> None:
        self._campaign_repository = campaign_repository
        self._safety_guard = safety_guard

    async def execute(
        self,
        data: CreateCampaignInput,
        *,
        dry_run_completed: bool = False,
    ) -> Campaign:
        if data.mode == PostMode.AUTO:
            auto_posts_used_today = (
                await self._campaign_repository.count_auto_posts_since_midnight()
            )
            has_running_auto_campaign = await self._campaign_repository.has_running_auto_campaign()
            await self._safety_guard.validate_campaign_start(
                mode=data.mode,
                target_count=len(data.target_group_ids),
                campaign_daily_limit=data.daily_auto_limit,
                auto_posts_used_today=auto_posts_used_today,
                has_running_auto_campaign=has_running_auto_campaign,
                dry_run_completed=dry_run_completed,
                min_delay_seconds=data.min_delay_seconds,
                max_delay_seconds=data.max_delay_seconds,
            )
        campaign = Campaign.create(
            name=data.name,
            post_id=data.post_id,
            mode=data.mode,
            target_group_ids=data.target_group_ids,
            daily_auto_limit=data.daily_auto_limit,
            min_delay_seconds=data.min_delay_seconds,
            max_delay_seconds=data.max_delay_seconds,
            scheduled_at=None,
        )
        saved_campaign = await self._campaign_repository.save(campaign)
        now = datetime.now(UTC)
        targets = [
            CampaignTarget(
                id=uuid4(),
                campaign_id=saved_campaign.id,
                group_id=group_id,
                status=TargetStatus.PENDING,
                attempt_count=0,
                last_error=None,
                prepared_at=None,
                posted_at=None,
                next_run_at=now,
            )
            for group_id in data.target_group_ids
        ]
        await self._campaign_repository.save_targets(targets)
        return saved_campaign
