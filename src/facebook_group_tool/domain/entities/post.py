from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Post:
    id: UUID
    title: str
    body_text: str
    link_url: str | None
    video_path: str | None
    media_items: tuple[str, ...]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, title: str, body_text: str, media_items: tuple[str, ...]) -> "Post":
        clean_title = title.strip()
        clean_body = body_text.strip()
        if not clean_title:
            raise ValueError("title is required")
        if not clean_body and not media_items:
            raise ValueError("post requires body text or at least one media item")
        now = datetime.now(UTC)
        return cls(
            id=uuid4(),
            title=clean_title,
            body_text=clean_body,
            link_url=None,
            video_path=None,
            media_items=media_items,
            created_at=now,
            updated_at=now,
        )
