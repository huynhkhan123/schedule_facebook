from collections.abc import Awaitable, Callable, Mapping
from pathlib import Path
from typing import Any, cast

from facebook_group_tool.infrastructure.automation.facebook_group_urls import (
    normalize_facebook_group_url,
)
from facebook_group_tool.infrastructure.automation.group_sync_session import GroupSyncSessionService

CONNECTOR_JOB_TYPES = frozenset(
    {
        "group_sync.start",
        "group_sync.collect_visible",
        "group_sync.stop",
        "group.open",
        "connector.self_test",
    }
)


class ConnectorJobRunner:
    def __init__(
        self,
        browser_profile_path: Path,
        *,
        open_group_url: Callable[[str], Awaitable[None]] | None = None,
    ) -> None:
        self._sync_session = GroupSyncSessionService(browser_profile_path)
        self._open_group_url = open_group_url or self._sync_session.open_group_url

    async def run(self, job: dict[str, Any]) -> dict[str, object]:
        job_type = str(job.get("job_type", ""))
        if job_type not in CONNECTOR_JOB_TYPES:
            return {
                "status": "failed",
                "error_code": "unsupported_job_type",
                "message": f"Unsupported connector job type: {job_type}",
            }
        if job_type == "connector.self_test":
            return {"status": "completed", "result": {"ok": True}}
        if job_type == "group_sync.start":
            status = await self._sync_session.start()
            return {"status": "completed", "result": status.__dict__}
        if job_type == "group_sync.collect_visible":
            status, groups = await self._sync_session.collect_visible_groups()
            return {
                "status": "completed",
                "result": {
                    **status.__dict__,
                    "groups": [group.__dict__ for group in groups],
                },
            }
        if job_type == "group.open":
            return await self._open_group(job)
        status = await self._sync_session.stop()
        return {"status": "completed", "result": status.__dict__}

    async def _open_group(self, job: dict[str, Any]) -> dict[str, object]:
        payload = job.get("payload")
        if not isinstance(payload, dict):
            return invalid_group_url_response()
        group_payload = cast(Mapping[str, object], payload)
        raw_url = group_payload.get("url")
        if not isinstance(raw_url, str):
            return invalid_group_url_response()
        url = normalize_facebook_group_url(raw_url)
        if url is None:
            return invalid_group_url_response()
        await self._open_group_url(url)
        return {"status": "completed", "result": {"status": "opened", "url": url}}


def invalid_group_url_response() -> dict[str, object]:
    return {
        "status": "failed",
        "error_code": "invalid_group_url",
        "message": "Only Facebook group URLs can be opened in the connector browser.",
    }
