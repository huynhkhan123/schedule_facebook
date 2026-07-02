from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Connector:
    machine_name: str
    platform: str
    capabilities: tuple[str, ...]
    profile_configured: bool
    id: UUID = field(default_factory=uuid4)
    token: str = ""
    status: str = "offline"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_seen_at: datetime | None = None
