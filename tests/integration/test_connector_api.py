# pyright: reportUnknownMemberType=false

from typing import Any, cast

from fastapi.testclient import TestClient


def test_connector_pairing_cors_preflight_allows_dashboard_origin(client: TestClient) -> None:
    response = cast(
        Any,
        client.options(
            "/api/connectors/pairing-codes",
            headers={
                "origin": "https://schedule.bookinghome.one",
                "access-control-request-method": "POST",
            },
        ),
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://schedule.bookinghome.one"


def test_connector_pairing_and_job_lifecycle(client: TestClient) -> None:
    pairing_response = cast(Any, client.post("/api/connectors/pairing-codes"))

    assert pairing_response.status_code == 201
    code = pairing_response.json()["code"]

    pair_response = cast(
        Any,
        client.post(
            "/api/connectors/pair",
            json={
                "code": code,
                "machine_name": "Customer MacBook",
                "platform": "darwin",
                "capabilities": ["group_sync"],
                "profile_configured": True,
            },
        ),
    )

    assert pair_response.status_code == 201
    connector = pair_response.json()
    assert connector["machine_name"] == "Customer MacBook"
    assert connector["status"] == "offline"
    assert connector["token"]

    connectors_response = cast(Any, client.get("/api/connectors"))

    assert connectors_response.status_code == 200
    connector_ids = {item["id"] for item in connectors_response.json()}
    assert connector["id"] in connector_ids

    job_response = cast(
        Any,
        client.post(
            "/api/connectors/jobs",
            json={"job_type": "group_sync.start", "payload": {}},
        ),
    )

    assert job_response.status_code == 201
    job = job_response.json()
    assert job["connector_id"] in connector_ids
    assert job["status"] == "pending"

    complete_response = cast(
        Any,
        client.post(
            f"/api/connectors/jobs/{job['id']}/complete",
            json={"result": {"status": "started"}},
        ),
    )

    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "completed"


def test_connector_websocket_marks_connector_online(client: TestClient) -> None:
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

    with client.websocket_connect(
        f"/api/connectors/ws/{connector['id']}?token={connector['token']}"
    ) as websocket:
        websocket.send_json(
            {
                "type": "hello",
                "connector_id": connector["id"],
                "version": "0.1.0",
                "platform": "darwin",
                "capabilities": ["group_sync"],
                "profile_configured": True,
            }
        )
        assert websocket.receive_json()["type"] == "hello_ack"

        connectors = cast(Any, client.get("/api/connectors")).json()
        matched = next(item for item in connectors if item["id"] == connector["id"])
        assert matched["status"] == "online"
