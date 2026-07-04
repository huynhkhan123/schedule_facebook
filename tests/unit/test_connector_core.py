from pathlib import Path
from typing import Any, cast

import pytest

from facebook_group_tool.connector.client import ConnectorApiClient
from facebook_group_tool.connector.config import ConnectorConfig
from facebook_group_tool.connector.core import ConnectorCore, process_connector_job, websocket_url
from facebook_group_tool.connector.job_runner import ConnectorJobRunner
from facebook_group_tool.connector.token_store import ConnectorTokenStore


class FakePairResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, str]:
        return {"id": "connector-123", "token": "secret-token"}


class FakeAsyncClient:
    instances: list["FakeAsyncClient"] = []

    def __init__(self, timeout: int) -> None:
        self.timeout = timeout
        self.posts: list[dict[str, Any]] = []
        FakeAsyncClient.instances.append(self)

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    async def post(self, url: str, json: dict[str, object]) -> FakePairResponse:
        self.posts.append({"url": url, "json": json})
        return FakePairResponse()


def test_websocket_url_converts_https_server_to_wss() -> None:
    url = websocket_url("https://api.schedule.bookinghome.one/", "abc", "token")

    assert url == "wss://api.schedule.bookinghome.one/api/connectors/ws/abc?token=token"


def test_websocket_url_converts_http_server_to_ws() -> None:
    url = websocket_url("http://localhost:8000", "abc", "token")

    assert url == "ws://localhost:8000/api/connectors/ws/abc?token=token"


@pytest.mark.asyncio
async def test_connector_core_pair_posts_expected_payload_and_saves_config(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    FakeAsyncClient.instances = []
    monkeypatch.setattr("facebook_group_tool.connector.core.httpx.AsyncClient", FakeAsyncClient)
    config_path = tmp_path / "connector.json"
    profile_path = tmp_path / "browser-profile"
    core = ConnectorCore(
        token_store=ConnectorTokenStore(config_path),
        browser_profile_path=profile_path,
    )

    config = await core.pair(
        code="ABC123",
        server_url="https://api.schedule.bookinghome.one",
        machine_name="Support Mac",
        platform_name="darwin-arm64",
    )

    assert config == ConnectorConfig(
        server_url="https://api.schedule.bookinghome.one",
        connector_id="connector-123",
        token="secret-token",
        browser_profile_path=str(profile_path),
    )
    assert ConnectorTokenStore(config_path).load() == config
    assert FakeAsyncClient.instances[0].posts == [
        {
            "url": "https://api.schedule.bookinghome.one/api/connectors/pair",
            "json": {
                "code": "ABC123",
                "machine_name": "Support Mac",
                "platform": "darwin-arm64",
                "capabilities": ["group_sync", "group_open"],
                "profile_configured": True,
            },
        }
    ]


class FakeConnectorApiClient:
    def __init__(self) -> None:
        self.failed_jobs: list[dict[str, str]] = []
        self.completed_jobs: list[dict[str, object]] = []

    async def fetch_job(self, job_id: str) -> dict[str, object]:
        return {"id": job_id, "job_type": "group_sync.collect_visible", "payload": {}}

    async def complete_job(self, job_id: str, result: dict[str, object]) -> None:
        self.completed_jobs.append({"job_id": job_id, "result": result})

    async def fail_job(self, job_id: str, message: str) -> None:
        self.failed_jobs.append({"job_id": job_id, "message": message})


class FailingConnectorJobRunner:
    async def run(self, job: dict[str, Any]) -> dict[str, object]:
        raise RuntimeError(f"browser page closed for {job['id']}")


@pytest.mark.asyncio
async def test_process_connector_job_reports_job_failure_without_crashing_loop() -> None:
    api_client = FakeConnectorApiClient()
    runner = FailingConnectorJobRunner()

    await process_connector_job(
        api_client=cast(ConnectorApiClient, api_client),
        runner=cast(ConnectorJobRunner, runner),
        job_id="job-123",
    )

    assert api_client.failed_jobs == [
        {"job_id": "job-123", "message": "browser page closed for job-123"}
    ]
    assert api_client.completed_jobs == []
