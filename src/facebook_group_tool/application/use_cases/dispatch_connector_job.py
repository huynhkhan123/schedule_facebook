from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

from facebook_group_tool.domain.entities.connector_job import ConnectorJob
from facebook_group_tool.domain.repositories.connector_job_repository import ConnectorJobRepository
from facebook_group_tool.domain.repositories.connector_repository import ConnectorRepository

ALLOWED_CONNECTOR_JOB_TYPES = frozenset(
    {
        "group_sync.start",
        "group_sync.collect_visible",
        "group_sync.stop",
        "post.prepare",
        "post.publish_prepared",
        "group.open",
        "connector.self_test",
    }
)

JOB_REQUIRED_CAPABILITIES = {
    "group.open": "group_open",
    "group_sync.start": "group_sync",
    "group_sync.collect_visible": "group_sync",
    "group_sync.stop": "group_sync",
}


class DispatchConnectorJobUseCase:
    def __init__(
        self,
        connector_repository: ConnectorRepository,
        connector_job_repository: ConnectorJobRepository,
    ) -> None:
        self._connector_repository = connector_repository
        self._connector_job_repository = connector_job_repository

    async def execute(self, *, job_type: str, payload: dict[str, object]) -> ConnectorJob:
        if job_type not in ALLOWED_CONNECTOR_JOB_TYPES:
            raise ValueError("Connector job type is not allowed")
        connectors = await self._connector_repository.list()
        required_capability = JOB_REQUIRED_CAPABILITIES.get(job_type)
        capable_connectors = [
            connector
            for connector in connectors
            if required_capability is None or required_capability in connector.capabilities
        ]
        online_connectors = [item for item in capable_connectors if item.status == "online"]
        candidates = online_connectors or capable_connectors
        connector = max(
            candidates,
            key=lambda item: item.last_seen_at or item.created_at,
            default=None,
        )
        if connector is None:
            raise RuntimeError("No connector is paired")
        job = ConnectorJob(connector_id=connector.id, job_type=job_type, payload=payload)
        return await self._connector_job_repository.save(job)

    async def complete(self, job_id: UUID, result: dict[str, object]) -> ConnectorJob:
        job = await self._connector_job_repository.get(job_id)
        if job is None:
            raise RuntimeError("Connector job not found")
        completed = replace(
            job,
            status="completed",
            result=result,
            updated_at=datetime.now(UTC),
        )
        return await self._connector_job_repository.save(completed)

    async def fail(self, job_id: UUID, message: str) -> ConnectorJob:
        job = await self._connector_job_repository.get(job_id)
        if job is None:
            raise RuntimeError("Connector job not found")
        failed = replace(job, status="failed", error_message=message, updated_at=datetime.now(UTC))
        return await self._connector_job_repository.save(failed)
