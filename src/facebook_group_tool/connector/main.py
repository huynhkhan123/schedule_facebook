import argparse
import asyncio
import sys
from pathlib import Path

if sys.platform == "win32":
    event_loop_policy = asyncio.WindowsSelectorEventLoopPolicy()  # type: ignore[attr-defined]
    asyncio.set_event_loop_policy(event_loop_policy)

from facebook_group_tool.connector.core import ConnectorCore
from facebook_group_tool.connector.token_store import ConnectorTokenStore

DEFAULT_CONFIG_PATH = Path.home() / ".facebook-group-tool" / "connector.json"
DEFAULT_PROFILE_PATH = Path.home() / ".facebook-group-tool" / "browser-profile"


async def pair_connector(args: argparse.Namespace) -> None:
    core = ConnectorCore(
        token_store=ConnectorTokenStore(args.config),
        browser_profile_path=args.browser_profile_path,
    )
    await core.pair(
        code=args.code,
        server_url=args.server,
        machine_name=args.machine_name,
        platform_name=args.platform,
    )
    print("✅ Connector paired successfully")


async def run_connector(args: argparse.Namespace) -> None:
    core = ConnectorCore(
        token_store=ConnectorTokenStore(args.config),
        browser_profile_path=DEFAULT_PROFILE_PATH,
    )
    await core.run()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Facebook Group Tool local connector")
    subparsers = parser.add_subparsers(dest="command", required=True)

    pair_parser = subparsers.add_parser("pair", help="Pair this machine with the cloud dashboard")
    pair_parser.add_argument("--code", required=True)
    pair_parser.add_argument("--server", required=True)
    pair_parser.add_argument("--machine-name", default="Local connector")
    pair_parser.add_argument("--platform", default=sys.platform)
    pair_parser.add_argument("--browser-profile-path", type=Path, default=DEFAULT_PROFILE_PATH)
    pair_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)

    run_parser = subparsers.add_parser("run", help="Run the connector loop")
    run_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "pair":
        asyncio.run(pair_connector(args))
        return
    asyncio.run(run_connector(args))


if __name__ == "__main__":
    main()
