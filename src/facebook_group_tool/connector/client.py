from urllib.parse import urljoin

import httpx

from facebook_group_tool.connector.config import ConnectorConfig


class ConnectorApiClient:
    def __init__(self, config: ConnectorConfig) -> None:
        self._config = config

    async def fetch_job(self, job_id: str) -> dict[str, object]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(self._url(f"/api/connectors/jobs/{job_id}"))
            response.raise_for_status()
            return dict(response.json())

    async def complete_job(self, job_id: str, result: dict[str, object]) -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self._url(f"/api/connectors/jobs/{job_id}/complete"),
                json={"result": result},
            )
            response.raise_for_status()

    async def fail_job(self, job_id: str, message: str) -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self._url(f"/api/connectors/jobs/{job_id}/fail"),
                json={"message": message},
            )
            response.raise_for_status()

    def _url(self, path: str) -> str:
        return urljoin(f"{self._config.server_url.rstrip('/')}/", path.lstrip("/"))
