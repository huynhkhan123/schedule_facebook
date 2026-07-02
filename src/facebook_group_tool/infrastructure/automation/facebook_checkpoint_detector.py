from playwright.async_api import Page

from facebook_group_tool.application.dto import SafetyDetection

UNSAFE_MARKERS = (
    "checkpoint",
    "captcha",
    "verification",
    "security check",
    "login",
)


class FacebookCheckpointDetector:
    def __init__(self, page: Page) -> None:
        self._page = page

    async def detect(self) -> SafetyDetection:
        body_text = (await self._page.locator("body").inner_text()).lower()
        if any(marker in body_text for marker in UNSAFE_MARKERS):
            return SafetyDetection(is_safe=False, reason="checkpoint_or_verification")
        return SafetyDetection(is_safe=True)
