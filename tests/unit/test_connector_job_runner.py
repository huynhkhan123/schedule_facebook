from pathlib import Path

import pytest

from facebook_group_tool.connector.job_runner import ConnectorJobRunner


@pytest.mark.asyncio
async def test_connector_job_runner_rejects_unknown_job_type(tmp_path: Path) -> None:
    runner = ConnectorJobRunner(tmp_path / "profile")

    result = await runner.run({"job_type": "shell.exec", "payload": {}})

    assert result["status"] == "failed"
    assert result["error_code"] == "unsupported_job_type"
