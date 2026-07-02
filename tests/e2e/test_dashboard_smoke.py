# pyright: reportUnknownMemberType=false

from typing import Any, cast

from fastapi.testclient import TestClient


def test_dashboard_overview_loads(client: TestClient) -> None:
    response = cast(Any, client.get("/"))

    assert response.status_code == 200
    assert "Facebook Group Tool" in response.text
    assert "Auto posts used today" in response.text
