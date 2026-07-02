from pathlib import Path

from facebook_group_tool.connector.config import ConnectorConfig
from facebook_group_tool.connector.token_store import ConnectorTokenStore


def test_connector_token_store_saves_and_loads_config(tmp_path: Path) -> None:
    store = ConnectorTokenStore(tmp_path / "connector.json")
    config = ConnectorConfig(
        server_url="https://example.test",
        connector_id="connector-1",
        token="secret-token",
        browser_profile_path=str(tmp_path / "profile"),
    )

    store.save(config)

    assert store.load() == config
