from pathlib import Path

import pytest
from playwright.async_api import Page

from facebook_group_tool.infrastructure.automation.facebook_group_sync import FacebookGroupSync


@pytest.mark.asyncio
async def test_collect_visible_groups_extracts_group_ids(page: Page) -> None:
    fixture = Path("tests/automation/fixtures/facebook_groups.html").read_text()
    await page.set_content(fixture)
    sync = FacebookGroupSync(page)

    groups = await sync.collect_visible_groups()

    assert [group.facebook_group_id for group in groups] == ["123", "456"]
    assert [group.name for group in groups] == ["Allowed Group A", "Allowed Group B"]


@pytest.mark.asyncio
async def test_collect_visible_groups_ignores_navigation_and_action_links(page: Page) -> None:
    await page.set_content(
        """
        <!doctype html>
        <html lang="vi">
          <body>
            <main aria-label="Groups">
              <a role="link" href="https://www.facebook.com/groups/feed/">
                <span>Bảng feed của bạn</span>
              </a>
              <a role="link" href="https://www.facebook.com/groups/discover/">
                <span>Khám phá</span>
              </a>
              <a role="link" href="https://www.facebook.com/groups/joins/?nav_source=tab">
                <span>Xem tất cả</span>
              </a>
              <a role="link" href="https://www.facebook.com/groups/create/">
                <span>Tạo nhóm mới</span>
              </a>
              <a role="link" href="https://www.facebook.com/groups/789/">
                <span>Xem nhóm</span>
              </a>
              <a role="link" href="/groups/nha-tro-thu-duc/">
                <span>Nhà trọ - phòng trọ Quận 9, Thủ Đức, Quận 2 -TP.HCM</span>
                <span>Lần hoạt động gần nhất: khoảng 1 phút trước</span>
              </a>
            </main>
          </body>
        </html>
        """
    )
    sync = FacebookGroupSync(page)

    groups = await sync.collect_visible_groups()

    assert [group.name for group in groups] == [
        "Nhà trọ - phòng trọ Quận 9, Thủ Đức, Quận 2 -TP.HCM"
    ]
    assert [group.facebook_group_id for group in groups] == ["nha-tro-thu-duc"]
    assert [group.url for group in groups] == ["https://www.facebook.com/groups/nha-tro-thu-duc"]
