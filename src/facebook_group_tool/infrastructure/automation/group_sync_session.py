from dataclasses import dataclass
from pathlib import Path

from playwright.async_api import Page

from facebook_group_tool.application.dto import SyncedGroupInput
from facebook_group_tool.infrastructure.automation.browser_session import PlaywrightBrowserSession
from facebook_group_tool.infrastructure.automation.facebook_group_sync import FacebookGroupSync

FACEBOOK_GROUPS_URL = "https://www.facebook.com/groups/joins/?nav_source=tab&ordering=viewer_added"


@dataclass(frozen=True)
class GroupSyncStatus:
    status: str
    synced_count: int = 0
    message: str = ""


class GroupSyncSessionService:
    def __init__(self, profile_path: Path, *, test_mode: bool = False) -> None:
        self._profile_path = profile_path
        self._test_mode = test_mode
        self._browser_session: PlaywrightBrowserSession | None = None
        self._page: Page | None = None
        self._status = GroupSyncStatus(status="idle")

    async def start(self) -> GroupSyncStatus:
        if self._test_mode:
            self._status = GroupSyncStatus(
                status="waiting_for_user_scroll",
                message="Test sync session started",
            )
            return self._status
        if self._browser_session is None:
            self._browser_session = PlaywrightBrowserSession(self._profile_path)
        self._status = GroupSyncStatus(status="opening_browser")
        await self._browser_session.open()
        await self._browser_session.goto(FACEBOOK_GROUPS_URL)
        self._page = self._browser_session.page
        self._status = GroupSyncStatus(
            status="waiting_for_user_scroll",
            message="Scroll the Facebook groups page in the opened browser",
        )
        return self._status

    async def collect_visible_groups(self) -> tuple[GroupSyncStatus, list[SyncedGroupInput]]:
        if self._test_mode:
            self._status = GroupSyncStatus(status="syncing_visible_groups", synced_count=0)
            return self._status, []
        if self._page is None:
            self._status = GroupSyncStatus(status="needs_user_action", message="Start sync first")
            return self._status, []
        groups = await FacebookGroupSync(self._page).collect_visible_groups()
        self._status = GroupSyncStatus(status="syncing_visible_groups", synced_count=len(groups))
        return self._status, groups

    async def stop(self) -> GroupSyncStatus:
        if self._browser_session is not None:
            await self._browser_session.close()
        self._browser_session = None
        self._page = None
        self._status = GroupSyncStatus(status="stopped")
        return self._status

    def status(self) -> GroupSyncStatus:
        return self._status
