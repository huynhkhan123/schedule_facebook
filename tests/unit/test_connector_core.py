from pathlib import Path
from typing import Any

import pytest

from facebook_group_tool.connector.config import ConnectorConfig
from facebook_group_tool.connector.core import ConnectorCore, websocket_url
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
                "capabilities": ["group_sync"],
                "profile_configured": True,
            },
        }
    ]
