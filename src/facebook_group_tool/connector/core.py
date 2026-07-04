import json
from pathlib import Path
from typing import Any, cast

import httpx
import websockets

from facebook_group_tool.connector.client import ConnectorApiClient
from facebook_group_tool.connector.config import ConnectorConfig
from facebook_group_tool.connector.job_runner import ConnectorJobRunner
from facebook_group_tool.connector.token_store import ConnectorTokenStore

CONNECTOR_CAPABILITIES = ["group_sync", "group_open"]


def websocket_url(server_url: str, connector_id: str, token: str) -> str:
    base = server_url.rstrip("/").replace("https://", "wss://").replace("http://", "ws://")
    return f"{base}/api/connectors/ws/{connector_id}?token={token}"


async def process_connector_job(
    *,
    api_client: ConnectorApiClient,
    runner: ConnectorJobRunner,
    job_id: str,
) -> None:
    try:
        job = await api_client.fetch_job(job_id)
        result = await runner.run(job)
        if result.get("status") == "failed":
            message = str(result.get("message", "Connector job failed"))
            await api_client.fail_job(job_id, message)
            return
        await api_client.complete_job(job_id, result)
    except Exception as error:
        try:
            await api_client.fail_job(job_id, str(error) or error.__class__.__name__)
        except Exception:
            return


class ConnectorCore:
    def __init__(self, token_store: ConnectorTokenStore, browser_profile_path: Path) -> None:
        self._token_store = token_store
        self._browser_profile_path = browser_profile_path

    async def pair(
        self,
        *,
        code: str,
        server_url: str,
        machine_name: str,
        platform_name: str,
    ) -> ConnectorConfig:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{server_url.rstrip('/')}/api/connectors/pair",
                json={
                    "code": code,
                    "machine_name": machine_name,
                    "platform": platform_name,
                    "capabilities": CONNECTOR_CAPABILITIES,
                    "profile_configured": True,
                },
            )
            response.raise_for_status()
            payload = response.json()

        config = ConnectorConfig(
            server_url=server_url,
            connector_id=str(payload["id"]),
            token=str(payload["token"]),
            browser_profile_path=str(self._browser_profile_path),
        )
        self._token_store.save(config)
        return config

    async def run(self) -> None:
        config = self._token_store.load()
        api_client = ConnectorApiClient(config)
        runner = ConnectorJobRunner(Path(config.browser_profile_path))
        url = websocket_url(config.server_url, config.connector_id, config.token)

        async with websockets.connect(url) as websocket:
            await websocket.send(
                json.dumps(
                    {
                        "type": "hello",
                        "version": "0.1.0",
                        "platform": "local",
                        "capabilities": CONNECTOR_CAPABILITIES,
                        "profile_configured": True,
                    }
                )
            )
            await websocket.recv()

            async for raw_message in websocket:
                message = cast(str, raw_message)
                event = self._parse_event(message)
                if event.get("type") != "job_available":
                    continue
                job_id = str(event.get("job_id", ""))
                if not job_id:
                    continue
                await process_connector_job(api_client=api_client, runner=runner, job_id=job_id)

    def load_config(self) -> ConnectorConfig:
        return self._token_store.load()

    @staticmethod
    def _parse_event(message: str) -> dict[str, Any]:
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            return {}
        if not isinstance(payload, dict):
            return {}
        return cast(dict[str, Any], payload)
