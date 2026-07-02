from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectorConfig:
    server_url: str
    connector_id: str
    token: str
    browser_profile_path: str
