from pathlib import Path

from playwright.async_api import BrowserContext, Page, Playwright, async_playwright


class PlaywrightBrowserSession:
    def __init__(self, profile_path: Path) -> None:
        self._profile_path = profile_path
        self._playwright: Playwright | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def open(self) -> None:
        self._playwright = await async_playwright().start()
        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(self._profile_path),
            headless=False,
        )
        self._page = (
            self._context.pages[0]
            if self._context.pages
            else await self._context.new_page()
        )

    async def close(self) -> None:
        if self._context is not None:
            await self._context.close()
            self._context = None
            self._page = None
        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None

    async def goto(self, url: str) -> None:
        if self._page is None:
            raise RuntimeError("browser session is not open")
        await self._page.goto(url)

    async def open_url(self, url: str) -> None:
        if self._context is None:
            await self.open()
        if self._page is None:
            raise RuntimeError("browser session is not open")
        await self._page.bring_to_front()
        await self._page.goto(url)

    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError("browser session is not open")
        return self._page
