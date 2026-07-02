from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ConnectorJob:
    connector_id: UUID
    job_type: str
    payload: dict[str, object]
    id: UUID = field(default_factory=uuid4)
    status: str = "pending"
    result: dict[str, object] = field(default_factory=lambda: {})
    error_message: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
