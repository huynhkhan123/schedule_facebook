from enum import StrEnum


class TargetStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PREPARED = "prepared"
    POSTED = "posted"
    SKIPPED = "skipped"
    FAILED = "failed"
    NEEDS_USER_ACTION = "needs_user_action"
    CANCELLED = "cancelled"
