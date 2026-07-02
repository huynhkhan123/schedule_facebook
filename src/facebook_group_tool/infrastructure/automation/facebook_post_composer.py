from pathlib import Path

from playwright.async_api import Page

from facebook_group_tool.application.dto import ComposerResult
from facebook_group_tool.application.ports import CheckpointDetectorPort


class FacebookPostComposer:
    def __init__(self, page: Page, checkpoint_detector: CheckpointDetectorPort) -> None:
        self._page = page
        self._checkpoint_detector = checkpoint_detector

    async def prepare_post(
        self,
        target_url: str,
        body_text: str,
        media_paths: list[Path],
    ) -> ComposerResult:
        if target_url != "about:blank":
            await self._page.goto(target_url)
        detection = await self._checkpoint_detector.detect()
        if not detection.is_safe:
            return ComposerResult(
                status="needs_user_action",
                message=detection.reason or "unsafe page",
            )

        textbox = self._page.locator('[role="textbox"]').first
        if await textbox.count() == 0:
            return ComposerResult(status="failed", message="Composer not found")
        await textbox.fill(body_text)

        file_input = self._page.locator('input[type="file"]').first
        if media_paths and await file_input.count() > 0:
            await file_input.set_input_files([str(path) for path in media_paths])
        return ComposerResult(status="prepared", message="Post prepared for review")

    async def publish_prepared_post(self) -> ComposerResult:
        detection = await self._checkpoint_detector.detect()
        if not detection.is_safe:
            return ComposerResult(
                status="needs_user_action",
                message=detection.reason or "unsafe page",
            )
        button = self._page.get_by_role("button", name="Post").first
        if await button.count() == 0 or not await button.is_enabled():
            return ComposerResult(status="needs_user_action", message="Post button is unavailable")
        await button.click()
        return ComposerResult(status="posted", message="Post published")
