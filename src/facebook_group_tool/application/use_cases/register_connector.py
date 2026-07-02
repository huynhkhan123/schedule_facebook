from dataclasses import replace
from secrets import token_urlsafe

from facebook_group_tool.domain.entities.connector import Connector
from facebook_group_tool.domain.repositories.connector_repository import ConnectorRepository


class RegisterConnectorUseCase:
    def __init__(self, connector_repository: ConnectorRepository) -> None:
        self._connector_repository = connector_repository

    async def execute(
        self,
        *,
        machine_name: str,
        platform: str,
        capabilities: tuple[str, ...],
        profile_configured: bool,
    ) -> Connector:
        connector = Connector(
            machine_name=machine_name,
            platform=platform,
            capabilities=capabilities,
            profile_configured=profile_configured,
            token=token_urlsafe(32),
        )
        return await self._connector_repository.save(connector)

    async def mark_online(self, connector: Connector) -> Connector:
        return await self._connector_repository.save(replace(connector, status="online"))

    async def mark_offline(self, connector: Connector) -> Connector:
        return await self._connector_repository.save(replace(connector, status="offline"))
