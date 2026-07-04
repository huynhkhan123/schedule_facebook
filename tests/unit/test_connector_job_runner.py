from pathlib import Path

import pytest

from facebook_group_tool.connector.job_runner import ConnectorJobRunner


@pytest.mark.asyncio
async def test_connector_job_runner_rejects_unknown_job_type(tmp_path: Path) -> None:
    runner = ConnectorJobRunner(tmp_path / "profile")

    result = await runner.run({"job_type": "shell.exec", "payload": {}})

    assert result["status"] == "failed"
    assert result["error_code"] == "unsupported_job_type"


@pytest.mark.asyncio
async def test_connector_job_runner_opens_group_url_in_managed_browser(tmp_path: Path) -> None:
    opened_urls: list[str] = []

    async def open_group(url: str) -> None:
        opened_urls.append(url)

    runner = ConnectorJobRunner(tmp_path / "profile", open_group_url=open_group)

    result = await runner.run(
        {
            "job_type": "group.open",
            "payload": {"url": "https://www.facebook.com/groups/123/?ref=dashboard"},
        }
    )

    assert result == {
        "status": "completed",
        "result": {"status": "opened", "url": "https://www.facebook.com/groups/123"},
    }
    assert opened_urls == ["https://www.facebook.com/groups/123"]


@pytest.mark.asyncio
async def test_connector_job_runner_rejects_non_group_open_urls(tmp_path: Path) -> None:
    async def open_group(_url: str) -> None:
        raise AssertionError("invalid URL should not be opened")

    runner = ConnectorJobRunner(tmp_path / "profile", open_group_url=open_group)

    result = await runner.run(
        {
            "job_type": "group.open",
            "payload": {"url": "https://www.facebook.com/groups/feed/"},
        }
    )

    assert result["status"] == "failed"
    assert result["error_code"] == "invalid_group_url"
