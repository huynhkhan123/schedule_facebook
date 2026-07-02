# pyright: reportUnknownMemberType=false

from typing import Any, cast

from fastapi.testclient import TestClient


def test_group_sync_requires_paired_connector(client: TestClient) -> None:
    response = cast(Any, client.post("/api/automation/group-sync/start"))

    assert response.status_code == 409
    assert response.json()["detail"] == "No connector is paired"


def test_group_sync_dispatches_connector_job(client: TestClient) -> None:
    code = cast(Any, client.post("/api/connectors/pairing-codes")).json()["code"]
    connector = cast(
        Any,
        client.post(
            "/api/connectors/pair",
            json={
                "code": code,
                "machine_name": "Runner",
                "platform": "darwin",
                "capabilities": ["group_sync"],
                "profile_configured": True,
            },
        ),
    ).json()

    start_response = cast(Any, client.post("/api/automation/group-sync/start"))

    assert start_response.status_code == 200
    assert start_response.json()["status"] == "syncing_visible_groups"

    job_response = cast(Any, client.get(f"/api/connectors/jobs/{start_response.json()['job_id']}"))

    assert job_response.status_code == 200
    job = job_response.json()
    assert job["connector_id"] == connector["id"]
    assert job["job_type"] == "group_sync.start"


def test_groups_page_contains_sync_controls_and_group_table(client: TestClient) -> None:
    response = cast(Any, client.get("/groups"))

    assert response.status_code == 200
    assert "Start sync" in response.text
    assert "Collect visible groups" in response.text
    assert "Stop sync" in response.text
    assert "Posting allowed" in response.text
