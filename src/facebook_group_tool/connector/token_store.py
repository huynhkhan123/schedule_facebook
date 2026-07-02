import json
from pathlib import Path

from facebook_group_tool.connector.config import ConnectorConfig


class ConnectorTokenStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def save(self, config: ConnectorConfig) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(
                {
                    "server_url": config.server_url,
                    "connector_id": config.connector_id,
                    "token": config.token,
                    "browser_profile_path": config.browser_profile_path,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def load(self) -> ConnectorConfig:
        data = json.loads(self._path.read_text(encoding="utf-8"))
        return ConnectorConfig(
            server_url=str(data["server_url"]),
            connector_id=str(data["connector_id"]),
            token=str(data["token"]),
            browser_profile_path=str(data["browser_profile_path"]),
        )
