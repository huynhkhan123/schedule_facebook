from typing import Protocol
from uuid import UUID

from facebook_group_tool.domain.entities.connector_job import ConnectorJob


class ConnectorJobRepository(Protocol):
    async def get(self, job_id: UUID) -> ConnectorJob | None: ...

    async def list_pending(self, connector_id: UUID) -> list[ConnectorJob]: ...

    async def save(self, job: ConnectorJob) -> ConnectorJob: ...
