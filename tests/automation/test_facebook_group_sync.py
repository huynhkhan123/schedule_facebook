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
