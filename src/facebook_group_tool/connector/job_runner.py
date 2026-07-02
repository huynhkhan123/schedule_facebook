from pathlib import Path
from typing import Any

from facebook_group_tool.infrastructure.automation.group_sync_session import GroupSyncSessionService

CONNECTOR_JOB_TYPES = frozenset(
    {
        "group_sync.start",
        "group_sync.collect_visible",
        "group_sync.stop",
        "connector.self_test",
    }
)


class ConnectorJobRunner:
    def __init__(self, browser_profile_path: Path) -> None:
        self._sync_session = GroupSyncSessionService(browser_profile_path)

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
        status = await self._sync_session.stop()
        return {"status": "completed", "result": status.__dict__}
