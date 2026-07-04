from collections.abc import Mapping
from dataclasses import replace
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from facebook_group_tool.application.dto import SyncedGroupInput
from facebook_group_tool.application.use_cases.dispatch_connector_job import (
    DispatchConnectorJobUseCase,
)
from facebook_group_tool.application.use_cases.register_connector import RegisterConnectorUseCase
from facebook_group_tool.application.use_cases.sync_groups import SyncGroupsUseCase
from facebook_group_tool.domain.entities.connector import Connector
from facebook_group_tool.domain.entities.connector_job import ConnectorJob
from facebook_group_tool.presentation.api.dependencies import (
    connector_job_repository,
    connector_repository,
    get_dispatch_connector_job_use_case,
    get_register_connector_use_case,
    get_sync_groups_use_case,
    pairing_code_repository,
)

router = APIRouter()
active_connector_sockets: dict[UUID, WebSocket] = {}

RegisterConnectorDependency = Annotated[
    RegisterConnectorUseCase,
    Depends(get_register_connector_use_case),
]
DispatchConnectorJobDependency = Annotated[
    DispatchConnectorJobUseCase,
    Depends(get_dispatch_connector_job_use_case),
]
SyncGroupsDependency = Annotated[SyncGroupsUseCase, Depends(get_sync_groups_use_case)]


class PairConnectorRequest(BaseModel):
    code: str = Field(min_length=1)
    machine_name: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    capabilities: list[str] = Field(default_factory=list)
    profile_configured: bool = False


class CreateConnectorJobRequest(BaseModel):
    job_type: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class CompleteConnectorJobRequest(BaseModel):
    result: dict[str, Any] = Field(default_factory=dict)


class FailConnectorJobRequest(BaseModel):
    message: str = Field(min_length=1)


def connector_response(connector: Connector, *, include_token: bool = False) -> dict[str, object]:
    response: dict[str, object] = {
        "id": str(connector.id),
        "machine_name": connector.machine_name,
        "platform": connector.platform,
        "capabilities": list(connector.capabilities),
        "profile_configured": connector.profile_configured,
        "status": connector.status,
        "last_seen_at": connector.last_seen_at.isoformat() if connector.last_seen_at else None,
    }
    if include_token:
        response = {**response, "token": connector.token}
    return response


def connector_job_response(job: ConnectorJob) -> dict[str, object]:
    return {
        "id": str(job.id),
        "connector_id": str(job.connector_id),
        "job_type": job.job_type,
        "payload": job.payload,
        "status": job.status,
        "result": job.result,
        "error_message": job.error_message,
    }


@router.post("/pairing-codes", status_code=201)
async def create_pairing_code() -> dict[str, str]:
    return {"code": pairing_code_repository.create()}


@router.post("/pair", status_code=201)
async def pair_connector(
    request: PairConnectorRequest,
    use_case: RegisterConnectorDependency,
) -> dict[str, object]:
    if not pairing_code_repository.consume(request.code):
        raise HTTPException(status_code=404, detail="Pairing code not found")
    connector = await use_case.execute(
        machine_name=request.machine_name,
        platform=request.platform,
        capabilities=tuple(request.capabilities),
        profile_configured=request.profile_configured,
    )
    return connector_response(connector, include_token=True)


@router.get("")
async def list_connectors() -> list[dict[str, object]]:
    connectors = await connector_repository.list()
    return [connector_response(connector) for connector in connectors]


@router.post("/jobs", status_code=201)
async def create_connector_job(
    request: CreateConnectorJobRequest,
    use_case: DispatchConnectorJobDependency,
) -> dict[str, object]:
    try:
        job = await use_case.execute(job_type=request.job_type, payload=request.payload)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    await notify_connector_job_available(job)
    return connector_job_response(job)


async def notify_connector_job_available(job: ConnectorJob) -> None:
    websocket = active_connector_sockets.get(job.connector_id)
    if websocket is None:
        return
    await websocket.send_json(
        {
            "type": "job_available",
            "job_id": str(job.id),
            "job_type": job.job_type,
        }
    )


@router.get("/jobs/{job_id}")
async def get_connector_job(job_id: UUID) -> dict[str, object]:
    job = await connector_job_repository.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Connector job not found")
    return connector_job_response(job)


@router.post("/jobs/{job_id}/complete")
async def complete_connector_job(
    job_id: UUID,
    request: CompleteConnectorJobRequest,
    use_case: DispatchConnectorJobDependency,
    sync_groups: SyncGroupsDependency,
) -> dict[str, object]:
    try:
        job = await use_case.complete(job_id, request.result)
    except RuntimeError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    if job.job_type == "group_sync.collect_visible":
        await sync_connector_groups(request.result, sync_groups)
    return connector_job_response(job)


async def sync_connector_groups(
    result: dict[str, Any],
    sync_groups: SyncGroupsUseCase,
) -> None:
    payload = result.get("result")
    if not isinstance(payload, dict):
        return
    result_payload = cast(Mapping[str, object], payload)
    groups_payload = result_payload.get("groups")
    if not isinstance(groups_payload, list):
        return
    raw_groups = cast(list[object], groups_payload)
    groups: list[Mapping[str, object]] = []
    for group_payload in raw_groups:
        if not isinstance(group_payload, dict):
            continue
        group = cast(Mapping[str, object], group_payload)
        if group.get("name") and group.get("url"):
            groups = [*groups, group]
    await sync_groups.execute(
        [
            SyncedGroupInput(
                name=str(group.get("name", "")),
                url=str(group.get("url", "")),
                facebook_group_id=optional_string(group.get("facebook_group_id")),
                cover_image_url=optional_string(group.get("cover_image_url")),
            )
            for group in groups
        ]
    )


def optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


@router.post("/jobs/{job_id}/fail")
async def fail_connector_job(
    job_id: UUID,
    request: FailConnectorJobRequest,
    use_case: DispatchConnectorJobDependency,
) -> dict[str, object]:
    try:
        job = await use_case.fail(job_id, request.message)
    except RuntimeError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return connector_job_response(job)


@router.websocket("/ws/{connector_id}")
async def connector_socket(websocket: WebSocket, connector_id: UUID) -> None:
    token = websocket.query_params.get("token", "")
    connector = await connector_repository.get(connector_id)
    if connector is None or connector.token != token:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    active_connector_sockets[connector_id] = websocket
    await connector_repository.save(replace(connector, status="online"))
    try:
        while True:
            message = await websocket.receive_json()
            if message.get("type") == "hello":
                await websocket.send_json(
                    {"type": "hello_ack", "heartbeat_interval_seconds": 20}
                )
    except WebSocketDisconnect:
        current = await connector_repository.get(connector_id)
        if current is not None:
            await connector_repository.save(replace(current, status="offline"))
    finally:
        active_connector_sockets.pop(connector_id, None)
