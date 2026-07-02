import json
from pathlib import Path

from facebook_group_tool.connector.config import ConnectorConfig
from facebook_group_tool.connector.sidecar import SidecarEventWriter, config_to_public_payload


def test_sidecar_event_writer_outputs_json_line_without_token(tmp_path: Path) -> None:
    output_path = tmp_path / "events.jsonl"

    with output_path.open("w", encoding="utf-8") as stream:
        writer = SidecarEventWriter(stream)
        writer.emit(
            "paired",
            "Connector paired successfully",
            {
                "connector_id": "connector-123",
                "token": "secret-token",
            },
        )

    [line] = output_path.read_text(encoding="utf-8").splitlines()
    event = json.loads(line)

    assert event == {
        "type": "paired",
        "level": "info",
        "message": "Connector paired successfully",
        "payload": {"connector_id": "connector-123"},
    }


def test_config_to_public_payload_hides_token(tmp_path: Path) -> None:
    payload = config_to_public_payload(
        ConnectorConfig(
            server_url="https://schedule.bookinghome.one",
            connector_id="connector-123",
            token="secret-token",
            browser_profile_path=str(tmp_path / "profile"),
        )
    )

    assert payload == {
        "server_url": "https://schedule.bookinghome.one",
        "connector_id": "connector-123",
        "browser_profile_configured": True,
    }
