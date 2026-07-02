from pathlib import Path

import pytest
from playwright.async_api import Page

from facebook_group_tool.infrastructure.automation.facebook_checkpoint_detector import (
    FacebookCheckpointDetector,
)
from facebook_group_tool.infrastructure.automation.facebook_post_composer import (
    FacebookPostComposer,
)


@pytest.mark.asyncio
async def test_post_composer_prepares_post_without_publishing(page: Page) -> None:
    fixture = Path("tests/automation/fixtures/composer.html").read_text()
    await page.set_content(fixture)
    composer = FacebookPostComposer(page, FacebookCheckpointDetector(page))

    result = await composer.prepare_post("about:blank", "Hello group", [])

    assert result.status == "prepared"
    assert await page.locator('[role="textbox"]').inner_text() == "Hello group"
