# pyright: reportUnknownMemberType=false

from typing import Any, cast
from uuid import uuid4

from fastapi.testclient import TestClient


def test_create_post_returns_created_post(client: TestClient) -> None:
    response = cast(
        Any,
        client.post(
            "/api/posts",
            json={"title": "Launch", "body_text": "Hello", "media_paths": []},
        ),
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Launch"


def test_auto_campaign_rejects_more_than_twenty_targets(client: TestClient) -> None:
    group_ids = [str(uuid4()) for _ in range(21)]

    response = cast(
        Any,
        client.post(
            "/api/campaigns",
            json={
                "name": "Too many",
                "post_id": str(uuid4()),
                "mode": "auto",
                "target_group_ids": group_ids,
                "daily_auto_limit": 20,
                "min_delay_seconds": 300,
                "max_delay_seconds": 900,
            },
        ),
    )

    assert response.status_code == 422
