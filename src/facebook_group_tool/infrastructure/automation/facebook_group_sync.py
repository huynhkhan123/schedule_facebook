from urllib.parse import urlparse

from playwright.async_api import Locator, Page

from facebook_group_tool.application.dto import SyncedGroupInput
from facebook_group_tool.infrastructure.automation.facebook_group_urls import (
    normalize_facebook_group_url,
)

GENERIC_GROUP_ACTION_LABELS = frozenset(
    {
        "join group",
        "open group",
        "view group",
        "mở nhóm",
        "tham gia nhóm",
        "xem nhóm",
    }
)


class FacebookGroupSync:
    def __init__(self, page: Page) -> None:
        self._page = page

    async def collect_visible_groups(self) -> list[SyncedGroupInput]:
        anchors = self._page.locator('a[role="link"][href*="/groups/"]')
        count = await anchors.count()
        groups: list[SyncedGroupInput] = []
        seen_urls: set[str] = set()
        for index in range(count):
            anchor = anchors.nth(index)
            if not await anchor.is_visible():
                continue
            href = await anchor.get_attribute("href")
            if not href:
                continue
            normalized_url = normalize_facebook_group_url(href)
            if normalized_url is None or normalized_url in seen_urls:
                continue
            name = await extract_group_name(anchor)
            if name is None:
                continue
            seen_urls.add(normalized_url)
            groups.append(
                SyncedGroupInput(
                    name=name,
                    url=normalized_url,
                    facebook_group_id=group_id_from_url(normalized_url),
                    cover_image_url=None,
                )
            )
        return groups


async def extract_group_name(anchor: Locator) -> str | None:
    text = " ".join((await anchor.inner_text()).split())
    if not text:
        return None
    first_line = text.splitlines()[0].strip()
    candidate = first_line or text
    if candidate.strip().lower() in GENERIC_GROUP_ACTION_LABELS:
        return None
    activity_marker = " Lần hoạt động gần nhất:"
    if activity_marker in candidate:
        candidate = candidate.split(activity_marker, maxsplit=1)[0].strip()
    return candidate or None


def group_id_from_url(url: str) -> str | None:
    path_parts = [part for part in urlparse(url).path.split("/") if part]
    if len(path_parts) < 2 or path_parts[0] != "groups":
        return None
    return path_parts[1]
