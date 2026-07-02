import re

from playwright.async_api import Page

from facebook_group_tool.application.dto import SyncedGroupInput

GROUP_ID_PATTERN = re.compile(r"/groups/([^/?#]+)")


class FacebookGroupSync:
    def __init__(self, page: Page) -> None:
        self._page = page

    async def collect_visible_groups(self) -> list[SyncedGroupInput]:
        anchors = self._page.locator('a[role="link"][href*="/groups/"]')
        count = await anchors.count()
        groups: list[SyncedGroupInput] = []
        for index in range(count):
            anchor = anchors.nth(index)
            if not await anchor.is_visible():
                continue
            href = await anchor.get_attribute("href")
            name = (await anchor.inner_text()).strip()
            if not href or not name:
                continue
            match = GROUP_ID_PATTERN.search(href)
            groups.append(
                SyncedGroupInput(
                    name=name,
                    url=href.rstrip("/"),
                    facebook_group_id=match.group(1) if match else None,
                    cover_image_url=None,
                )
            )
        return groups
