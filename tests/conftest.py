import os
from collections.abc import AsyncIterator, Iterator

os.environ.setdefault("APP_ENV", "test")

import pytest
from fastapi.testclient import TestClient
from playwright.async_api import Page, async_playwright

from facebook_group_tool.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture
async def page() -> AsyncIterator[Page]:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        browser_page = await browser.new_page()
        try:
            yield browser_page
        finally:
            await browser.close()
