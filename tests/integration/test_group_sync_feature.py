# pyright: reportUnknownMemberType=false

from typing import Any, cast

from fastapi.testclient import TestClient


def test_group_sync_collect_visible_groups_returns_synced_groups(client: TestClient) -> None:
    start_response = cast(Any, client.post("/api/automation/group-sync/start"))
    assert start_response.status_code == 200
    assert start_response.json()["status"] in {"opening_browser", "waiting_for_user_scroll"}

    collect_response = cast(Any, client.post("/api/automation/group-sync/collect-visible"))

    assert collect_response.status_code == 200
    payload = collect_response.json()
    assert payload["status"] == "syncing_visible_groups"
    assert payload["synced_count"] >= 0


def test_groups_page_contains_sync_controls_and_group_table(client: TestClient) -> None:
    response = cast(Any, client.get("/groups"))

    assert response.status_code == 200
    assert "Start sync" in response.text
    assert "Collect visible groups" in response.text
    assert "Stop sync" in response.text
    assert "Posting allowed" in response.text
