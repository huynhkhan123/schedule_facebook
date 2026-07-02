from typing import Protocol
from uuid import UUID

from facebook_group_tool.domain.entities.connector import Connector


class ConnectorRepository(Protocol):
    async def get(self, connector_id: UUID) -> Connector | None: ...

    async def get_by_token(self, token: str) -> Connector | None: ...

    async def list(self) -> list[Connector]: ...

    async def save(self, connector: Connector) -> Connector: ...
