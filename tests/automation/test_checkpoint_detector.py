from pathlib import Path

import pytest
from playwright.async_api import Page

from facebook_group_tool.infrastructure.automation.facebook_checkpoint_detector import (
    FacebookCheckpointDetector,
)


@pytest.mark.asyncio
async def test_checkpoint_detector_reports_unsafe_page(page: Page) -> None:
    fixture = Path("tests/automation/fixtures/checkpoint.html").read_text()
    await page.set_content(fixture)
    detector = FacebookCheckpointDetector(page)

    detection = await detector.detect()

    assert detection.is_safe is False
    assert detection.reason == "checkpoint_or_verification"
