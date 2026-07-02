from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from facebook_group_tool.domain.entities.campaign import Campaign
from facebook_group_tool.domain.entities.campaign_target import CampaignTarget
from facebook_group_tool.domain.value_objects.campaign_status import CampaignStatus
from facebook_group_tool.domain.value_objects.post_mode import PostMode
from facebook_group_tool.domain.value_objects.target_status import TargetStatus
from facebook_group_tool.infrastructure.database.models import CampaignModel, CampaignTargetModel


def campaign_to_domain(model: CampaignModel) -> Campaign:
    return Campaign(
        id=model.id,
        name=model.name,
        post_id=model.post_id,
        mode=PostMode(model.mode),
        status=CampaignStatus(model.status),
        daily_auto_limit=model.daily_auto_limit,
        min_delay_seconds=model.min_delay_seconds,
        max_delay_seconds=model.max_delay_seconds,
        scheduled_at=model.scheduled_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def campaign_from_domain(campaign: Campaign) -> CampaignModel:
    return CampaignModel(
        id=campaign.id,
        name=campaign.name,
        post_id=campaign.post_id,
        mode=campaign.mode.value,
        status=campaign.status.value,
        daily_auto_limit=campaign.daily_auto_limit,
        min_delay_seconds=campaign.min_delay_seconds,
        max_delay_seconds=campaign.max_delay_seconds,
        scheduled_at=campaign.scheduled_at,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
    )


def target_to_domain(model: CampaignTargetModel) -> CampaignTarget:
    return CampaignTarget(
        id=model.id,
        campaign_id=model.campaign_id,
        group_id=model.group_id,
        status=TargetStatus(model.status),
        attempt_count=model.attempt_count,
        last_error=model.last_error,
        prepared_at=model.prepared_at,
        posted_at=model.posted_at,
        next_run_at=model.next_run_at,
    )


def target_from_domain(target: CampaignTarget) -> CampaignTargetModel:
    return CampaignTargetModel(
        id=target.id,
        campaign_id=target.campaign_id,
        group_id=target.group_id,
        status=target.status.value,
        attempt_count=target.attempt_count,
        last_error=target.last_error,
        prepared_at=target.prepared_at,
        posted_at=target.posted_at,
        next_run_at=target.next_run_at,
    )


class SqlAlchemyCampaignRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, campaign_id: object) -> Campaign | None:
        model = await self._session.get(CampaignModel, campaign_id)
        return campaign_to_domain(model) if model else None

    async def save(self, campaign: Campaign) -> Campaign:
        merged = await self._session.merge(campaign_from_domain(campaign))
        await self._session.commit()
        await self._session.refresh(merged)
        return campaign_to_domain(merged)

    async def save_targets(self, targets: list[CampaignTarget]) -> list[CampaignTarget]:
        merged_targets: list[CampaignTargetModel] = []
        for target in targets:
            merged = await self._session.merge(target_from_domain(target))
            merged_targets.append(merged)
        await self._session.commit()
        for model in merged_targets:
            await self._session.refresh(model)
        return [target_to_domain(model) for model in merged_targets]

    async def list_targets(self, campaign_id: object) -> list[CampaignTarget]:
        result = await self._session.execute(
            select(CampaignTargetModel).where(CampaignTargetModel.campaign_id == campaign_id)
        )
        return [target_to_domain(model) for model in result.scalars().all()]

    async def count_auto_posts_since_midnight(self) -> int:
        midnight = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self._session.execute(
            select(func.count())
            .select_from(CampaignTargetModel)
            .join(CampaignModel, CampaignModel.id == CampaignTargetModel.campaign_id)
            .where(CampaignModel.mode == PostMode.AUTO.value)
            .where(CampaignTargetModel.status == TargetStatus.POSTED.value)
            .where(CampaignTargetModel.posted_at >= midnight)
        )
        return int(result.scalar_one())

    async def has_running_auto_campaign(self) -> bool:
        result = await self._session.execute(
            select(func.count())
            .select_from(CampaignModel)
            .where(CampaignModel.mode == PostMode.AUTO.value)
            .where(CampaignModel.status == CampaignStatus.RUNNING.value)
        )
        return int(result.scalar_one()) > 0
