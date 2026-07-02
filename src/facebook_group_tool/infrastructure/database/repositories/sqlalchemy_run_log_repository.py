from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from facebook_group_tool.domain.entities.run_log import RunLog
from facebook_group_tool.domain.value_objects.run_log_level import RunLogLevel
from facebook_group_tool.infrastructure.database.models import RunLogModel


def to_domain(model: RunLogModel) -> RunLog:
    return RunLog(
        id=model.id,
        campaign_id=model.campaign_id,
        campaign_target_id=model.campaign_target_id,
        level=RunLogLevel(model.level),
        event_type=model.event_type,
        message=model.message,
        metadata=model.log_metadata,
        created_at=model.created_at,
    )


def from_domain(log: RunLog) -> RunLogModel:
    return RunLogModel(
        id=log.id,
        campaign_id=log.campaign_id,
        campaign_target_id=log.campaign_target_id,
        level=log.level.value,
        event_type=log.event_type,
        message=log.message,
        log_metadata=log.metadata,
        created_at=log.created_at,
    )


class SqlAlchemyRunLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, log: RunLog) -> RunLog:
        self._session.add(from_domain(log))
        await self._session.commit()
        model = await self._session.get(RunLogModel, log.id)
        if model is None:
            raise RuntimeError("Run log was not persisted")
        return to_domain(model)

    async def list_for_campaign(self, campaign_id: object) -> list[RunLog]:
        result = await self._session.execute(
            select(RunLogModel)
            .where(RunLogModel.campaign_id == campaign_id)
            .order_by(RunLogModel.created_at.desc())
        )
        return [to_domain(model) for model in result.scalars().all()]
