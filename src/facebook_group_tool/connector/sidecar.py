import argparse
import asyncio
import json
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # pyright: ignore[reportAttributeAccessIssue]
from pathlib import Path
from typing import TextIO

from facebook_group_tool.connector.config import ConnectorConfig
from facebook_group_tool.connector.core import ConnectorCore
from facebook_group_tool.connector.main import DEFAULT_CONFIG_PATH, DEFAULT_PROFILE_PATH
from facebook_group_tool.connector.token_store import ConnectorTokenStore

DEFAULT_SERVER_URL = "https://api.schedule.bookinghome.one"
SENSITIVE_PAYLOAD_KEYS = frozenset({"token", "access_token", "refresh_token", "secret"})


def config_to_public_payload(config: ConnectorConfig) -> dict[str, object]:
    return {
        "server_url": config.server_url,
        "connector_id": config.connector_id,
        "browser_profile_configured": bool(config.browser_profile_path),
    }


class SidecarEventWriter:
    def __init__(self, stream: TextIO) -> None:
        self._stream = stream

    def emit(
        self,
        event_type: str,
        message: str,
        payload: dict[str, object] | None = None,
        *,
        level: str = "info",
    ) -> None:
        event = {
            "type": event_type,
            "level": level,
            "message": message,
            "payload": self._redact_payload(payload or {}),
        }
        self._stream.write(json.dumps(event, ensure_ascii=False) + "\n")
        self._stream.flush()

    @classmethod
    def _redact_payload(cls, payload: dict[str, object]) -> dict[str, object]:
        return {
            key: value
            for key, value in payload.items()
            if key.lower() not in SENSITIVE_PAYLOAD_KEYS
        }


async def pair_sidecar(args: argparse.Namespace, writer: SidecarEventWriter) -> int:
    core = ConnectorCore(
        token_store=ConnectorTokenStore(args.config),
        browser_profile_path=args.browser_profile_path,
    )
    writer.emit("pairing", "Pairing connector with dashboard")
    try:
        config = await core.pair(
            code=args.code,
            server_url=args.server,
            machine_name=args.machine_name,
            platform_name=args.platform,
        )
    except Exception as error:
        writer.emit("error", str(error), level="error")
        return 1

    writer.emit("paired", "Connector paired successfully", config_to_public_payload(config))
    return 0


async def run_sidecar(args: argparse.Namespace, writer: SidecarEventWriter) -> int:
    core = ConnectorCore(
        token_store=ConnectorTokenStore(args.config),
        browser_profile_path=args.browser_profile_path,
    )
    try:
        config = core.load_config()
    except Exception as error:
        writer.emit("error", f"Connector is not paired: {error}", level="error")
        return 1

    writer.emit("connecting", "Connecting to dashboard", config_to_public_payload(config))
    try:
        await core.run()
    except KeyboardInterrupt:
        writer.emit("stopped", "Connector stopped by user")
        return 0
    except Exception as error:
        writer.emit("error", str(error), level="error")
        return 1
    writer.emit("stopped", "Connector stopped")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Facebook Group Connector desktop sidecar")
    subparsers = parser.add_subparsers(dest="command", required=True)

    pair_parser = subparsers.add_parser("pair", help="Pair this machine with the cloud dashboard")
    pair_parser.add_argument("--code", required=True)
    pair_parser.add_argument("--server", default=DEFAULT_SERVER_URL)
    pair_parser.add_argument("--machine-name", default="Desktop connector")
    pair_parser.add_argument("--platform", default=sys.platform)
    pair_parser.add_argument("--browser-profile-path", type=Path, default=DEFAULT_PROFILE_PATH)
    pair_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)

    run_parser = subparsers.add_parser("run", help="Run the connector loop")
    run_parser.add_argument("--browser-profile-path", type=Path, default=DEFAULT_PROFILE_PATH)
    run_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)

    return parser


async def async_main(argv: list[str] | None = None, stream: TextIO = sys.stdout) -> int:
    args = build_parser().parse_args(argv)
    writer = SidecarEventWriter(stream)
    if args.command == "pair":
        return await pair_sidecar(args, writer)
    return await run_sidecar(args, writer)


def main() -> None:
    raise SystemExit(asyncio.run(async_main()))


if __name__ == "__main__":
    main()
