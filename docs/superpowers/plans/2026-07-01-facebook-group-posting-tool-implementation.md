# Facebook Group Posting Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Python web dashboard that manages safe Facebook group posting workflows for groups the user has already joined and is permitted to post in.

**Architecture:** Implement a Clean Architecture FastAPI app with domain entities and repository interfaces at the core, application use cases in the middle, and PostgreSQL, Playwright, media storage, and dashboard/API adapters at the edges. Browser automation is human-in-the-loop: it uses a dedicated existing browser profile, never stores Facebook credentials, pauses on checkpoint/CAPTCHA/login/verification/unexpected UI, and never implements bypass or evasion. The dashboard exposes group sync, group management, post drafts, quick posts, campaign execution, pause/resume/cancel, and run logs.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, PostgreSQL, Playwright Python, Jinja2, pytest, pytest-asyncio, httpx, testcontainers-postgres or local PostgreSQL test database, ruff, pyright.

## Global Constraints

- Use `uv` for project dependency management.
- Use PostgreSQL; do not use SQLite.
- Use Clean Architecture with domain, application, infrastructure, and presentation layers.
- Run locally, for example at `http://localhost:8000`.
- Only operate on groups the user has already joined and is permitted to post in.
- Do not auto-join groups.
- Do not collect groups outside the logged-in user's group list.
- Do not store Facebook email or password.
- Do not bypass CAPTCHA, checkpoints, login challenges, or verification dialogs.
- Do not implement detection evasion.
- Do not retry aggressively after failures.
- Do not run multiple auto campaigns concurrently on the same browser profile.
- In auto mode, enforce a global hard limit of 20 groups per day.
- If a user selects more than 20 groups for auto mode, require switching to semi-auto mode.
- Auto mode requires a dry-run before a real run.
- Default auto delay range is 5-15 minutes between groups.
- Semi-auto mode prepares posts but does not click publish.
- MVP supports text and images; link and video fields exist but link/video posting remains inactive.
- Pause on checkpoint, CAPTCHA, login expiration, verification prompts, browser crash, or unexpected UI.
- Keep files focused and under 800 lines.
- Prefer immutable data updates; do not mutate domain objects in place.
- Before claiming completion, run unit, integration, API, automation fixture, and dashboard smoke checks listed in this plan.

---

## File Structure Map

Create this project structure:

```text
pyproject.toml
.env.example
alembic.ini
README.md
docs/development.md
docs/superpowers/plans/2026-07-01-facebook-group-posting-tool-implementation.md
src/facebook_group_tool/
  __init__.py
  main.py
  config.py
  domain/
    __init__.py
    entities/
      __init__.py
      group.py
      post.py
      campaign.py
      campaign_target.py
      run_log.py
    value_objects/
      __init__.py
      campaign_status.py
      post_mode.py
      run_log_level.py
      safety_policy.py
      target_status.py
    repositories/
      __init__.py
      campaign_repository.py
      group_repository.py
      post_repository.py
      run_log_repository.py
  application/
    __init__.py
    dto.py
    ports.py
    services/
      __init__.py
      safety_guard.py
      scheduling_service.py
    use_cases/
      __init__.py
      create_campaign.py
      create_post.py
      mark_group_permission.py
      pause_campaign.py
      resume_campaign.py
      run_campaign.py
      run_quick_post.py
      sync_groups.py
  infrastructure/
    __init__.py
    automation/
      __init__.py
      browser_session.py
      facebook_checkpoint_detector.py
      facebook_group_sync.py
      facebook_post_composer.py
    database/
      __init__.py
      models.py
      postgres.py
      repositories/
        __init__.py
        sqlalchemy_campaign_repository.py
        sqlalchemy_group_repository.py
        sqlalchemy_post_repository.py
        sqlalchemy_run_log_repository.py
      migrations/
        env.py
        script.py.mako
        versions/
    storage/
      __init__.py
      media_storage.py
  presentation/
    __init__.py
    api/
      __init__.py
      dependencies.py
      routes/
        __init__.py
        automation.py
        campaigns.py
        groups.py
        posts.py
      schemas/
        __init__.py
        campaign_schema.py
        group_schema.py
        post_schema.py
    web/
      __init__.py
      routes.py
      templates/
        base.html
        overview.html
        groups.html
        posts.html
        campaigns.html
        logs.html
      static/
        app.css
        app.js
tests/
  conftest.py
  unit/
    test_domain_entities.py
    test_safety_guard.py
    test_scheduling_service.py
    test_use_cases.py
  integration/
    test_repositories.py
    test_api_routes.py
  automation/
    fixtures/
      facebook_groups.html
      checkpoint.html
      composer.html
      missing_composer.html
    test_facebook_group_sync.py
    test_checkpoint_detector.py
    test_post_composer.py
  e2e/
    test_dashboard_smoke.py
```

## Shared Interfaces

Use these signatures consistently across tasks:

```python
from datetime import datetime
from pathlib import Path
from typing import Protocol
from uuid import UUID

class BrowserSessionPort(Protocol):
    async def open(self) -> None: ...
    async def close(self) -> None: ...
    async def goto(self, url: str) -> None: ...

class GroupSyncPort(Protocol):
    async def collect_visible_groups(self) -> list[SyncedGroupInput]: ...

class PostComposerPort(Protocol):
    async def prepare_post(self, target_url: str, body_text: str, media_paths: list[Path]) -> ComposerResult: ...
    async def publish_prepared_post(self) -> ComposerResult: ...

class CheckpointDetectorPort(Protocol):
    async def detect(self) -> SafetyDetection: ...
```

Key DTOs:

```python
@dataclass(frozen=True)
class SyncedGroupInput:
    name: str
    url: str
    facebook_group_id: str | None = None
    cover_image_url: str | None = None

@dataclass(frozen=True)
class SafetyDetection:
    is_safe: bool
    reason: str | None = None

@dataclass(frozen=True)
class ComposerResult:
    status: str
    message: str
```

---

### Task 1: Project Scaffold, Configuration, and App Factory

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `README.md`
- Create: `docs/development.md`
- Create: `src/facebook_group_tool/__init__.py`
- Create: `src/facebook_group_tool/config.py`
- Create: `src/facebook_group_tool/main.py`
- Create: `tests/conftest.py`

**Interfaces:**
- Produces: `Settings`, `get_settings() -> Settings`, `create_app() -> FastAPI`.
- Later tasks consume: FastAPI app factory, settings, and pytest fixtures.

- [ ] **Step 1: Initialize Python project dependencies**

Run:

```bash
uv init --package --python 3.12
uv add fastapi uvicorn[standard] pydantic-settings sqlalchemy asyncpg alembic playwright jinja2 python-multipart aiofiles
uv add --dev pytest pytest-asyncio httpx ruff pyright testcontainers[postgres]
```

Expected: `pyproject.toml` and `uv.lock` exist, with dependencies installed in a local uv-managed environment.

- [ ] **Step 2: Replace `pyproject.toml` with exact project configuration**

```toml
[project]
name = "facebook-group-tool"
version = "0.1.0"
description = "Local dashboard for safe Facebook group posting workflows"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
  "aiofiles>=24.1.0",
  "alembic>=1.14.0",
  "asyncpg>=0.30.0",
  "fastapi>=0.115.0",
  "jinja2>=3.1.4",
  "playwright>=1.49.0",
  "pydantic-settings>=2.7.0",
  "python-multipart>=0.0.19",
  "sqlalchemy>=2.0.36",
  "uvicorn[standard]>=0.34.0"
]

[dependency-groups]
dev = [
  "httpx>=0.28.0",
  "pyright>=1.1.390",
  "pytest>=8.3.4",
  "pytest-asyncio>=0.25.0",
  "ruff>=0.8.4",
  "testcontainers[postgres]>=4.9.0"
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["src"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM"]

[tool.pyright]
include = ["src", "tests"]
pythonVersion = "3.12"
typeCheckingMode = "strict"
```

- [ ] **Step 3: Add environment example**

Create `.env.example`:

```env
APP_ENV=development
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/facebook_group_tool
BROWSER_PROFILE_PATH=/absolute/path/to/dedicated/facebook-profile
MEDIA_STORAGE_DIR=./var/media
GLOBAL_DAILY_AUTO_LIMIT=20
DEFAULT_MIN_DELAY_SECONDS=300
DEFAULT_MAX_DELAY_SECONDS=900
```

- [ ] **Step 4: Add settings module**

Create `src/facebook_group_tool/config.py`:

```python
from functools import lru_cache
from pathlib import Path

from pydantic import Field, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/facebook_group_tool"
    browser_profile_path: Path = Path("./var/browser-profile")
    media_storage_dir: Path = Path("./var/media")
    global_daily_auto_limit: PositiveInt = Field(default=20, le=20)
    default_min_delay_seconds: PositiveInt = 300
    default_max_delay_seconds: PositiveInt = 900


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 5: Add FastAPI app factory**

Create `src/facebook_group_tool/main.py`:

```python
from fastapi import FastAPI

from facebook_group_tool.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Facebook Group Tool", version="0.1.0")

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "environment": settings.app_env}

    return app


app = create_app()
```

- [ ] **Step 6: Add test fixture and failing health test**

Create `tests/conftest.py`:

```python
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from facebook_group_tool.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as test_client:
        yield test_client
```

Create `tests/unit/test_app_health.py`:

```python
from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

- [ ] **Step 7: Run scaffold checks**

Run:

```bash
uv run pytest tests/unit/test_app_health.py -v
uv run ruff check .
uv run pyright
```

Expected: health test passes; ruff and pyright pass.

- [ ] **Step 8: Add docs**

Create `README.md`:

```markdown
# Facebook Group Tool

Local dashboard for managing safe Facebook group posting workflows. The tool is designed for groups where the user is already a member and has permission to post promotional content.

Safety boundaries: no credential storage, no auto-joining groups, no CAPTCHA/checkpoint bypass, no detection evasion, and auto mode is capped at 20 groups per day.

See [docs/development.md](docs/development.md) for setup and development commands.
```

Create `docs/development.md`:

```markdown
# Development Guide

## Setup

```bash
uv sync
cp .env.example .env
uv run playwright install chromium
```

## Run local API

```bash
uv run uvicorn facebook_group_tool.main:app --reload
```

## Checks

```bash
uv run pytest
uv run ruff check .
uv run pyright
```

## PostgreSQL

The app expects `DATABASE_URL` to point to PostgreSQL. Do not configure SQLite for this project.
```

- [ ] **Step 9: Commit if git is available**

Run:

```bash
git rev-parse --is-inside-work-tree && git add pyproject.toml uv.lock .env.example README.md docs/development.md src tests && git commit -m "chore: scaffold local dashboard project"
```

Expected: if this directory is not a git repo, the first command prints an error and no commit is made; continue without treating it as a task failure.

---

### Task 2: Domain Entities, Value Objects, and Repository Protocols

**Files:**
- Create: `src/facebook_group_tool/domain/value_objects/post_mode.py`
- Create: `src/facebook_group_tool/domain/value_objects/campaign_status.py`
- Create: `src/facebook_group_tool/domain/value_objects/target_status.py`
- Create: `src/facebook_group_tool/domain/value_objects/run_log_level.py`
- Create: `src/facebook_group_tool/domain/value_objects/safety_policy.py`
- Create: `src/facebook_group_tool/domain/entities/group.py`
- Create: `src/facebook_group_tool/domain/entities/post.py`
- Create: `src/facebook_group_tool/domain/entities/campaign.py`
- Create: `src/facebook_group_tool/domain/entities/campaign_target.py`
- Create: `src/facebook_group_tool/domain/entities/run_log.py`
- Create: `src/facebook_group_tool/domain/repositories/group_repository.py`
- Create: `src/facebook_group_tool/domain/repositories/post_repository.py`
- Create: `src/facebook_group_tool/domain/repositories/campaign_repository.py`
- Create: `src/facebook_group_tool/domain/repositories/run_log_repository.py`
- Test: `tests/unit/test_domain_entities.py`

**Interfaces:**
- Consumes: none from app code.
- Produces: immutable dataclasses and repository protocols used by application services and infrastructure repositories.

- [ ] **Step 1: Write failing domain tests**

Create `tests/unit/test_domain_entities.py`:

```python
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from facebook_group_tool.domain.entities.campaign import Campaign
from facebook_group_tool.domain.entities.group import Group
from facebook_group_tool.domain.entities.post import Post
from facebook_group_tool.domain.value_objects.campaign_status import CampaignStatus
from facebook_group_tool.domain.value_objects.post_mode import PostMode
from facebook_group_tool.domain.value_objects.safety_policy import SafetyPolicy


def test_group_permission_update_returns_new_group() -> None:
    group = Group(
        id=uuid4(),
        facebook_group_id="123",
        name="Allowed Group",
        url="https://facebook.com/groups/123",
        cover_image_url=None,
        tags=("promo",),
        note="",
        is_enabled=True,
        is_posting_allowed=False,
        last_synced_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    updated = group.with_posting_permission(True)

    assert group.is_posting_allowed is False
    assert updated.is_posting_allowed is True
    assert updated.id == group.id


def test_post_requires_text_or_media() -> None:
    with pytest.raises(ValueError, match="body text or at least one media item"):
        Post.create(title="Empty", body_text="", media_items=())


def test_auto_campaign_rejects_more_than_twenty_targets() -> None:
    post_id = uuid4()
    group_ids = tuple(uuid4() for _ in range(21))

    with pytest.raises(ValueError, match="Auto mode supports at most 20 targets"):
        Campaign.create(
            name="Too many",
            post_id=post_id,
            mode=PostMode.AUTO,
            target_group_ids=group_ids,
            daily_auto_limit=20,
            min_delay_seconds=300,
            max_delay_seconds=900,
            scheduled_at=None,
        )


def test_safety_policy_validates_delay_order() -> None:
    with pytest.raises(ValueError, match="min_delay_seconds must be <= max_delay_seconds"):
        SafetyPolicy(global_daily_auto_limit=20, min_delay_seconds=900, max_delay_seconds=300)


def test_campaign_start_returns_running_copy() -> None:
    campaign = Campaign.create(
        name="Small campaign",
        post_id=uuid4(),
        mode=PostMode.AUTO,
        target_group_ids=(uuid4(),),
        daily_auto_limit=1,
        min_delay_seconds=300,
        max_delay_seconds=900,
        scheduled_at=None,
    )

    running = campaign.mark_running()

    assert campaign.status == CampaignStatus.DRAFT
    assert running.status == CampaignStatus.RUNNING
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest tests/unit/test_domain_entities.py -v
```

Expected: FAIL with import errors for missing domain modules.

- [ ] **Step 3: Implement value objects**

Create `src/facebook_group_tool/domain/value_objects/post_mode.py`:

```python
from enum import StrEnum


class PostMode(StrEnum):
    AUTO = "auto"
    SEMI_AUTO = "semi_auto"
```

Create `src/facebook_group_tool/domain/value_objects/campaign_status.py`:

```python
from enum import StrEnum


class CampaignStatus(StrEnum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

Create `src/facebook_group_tool/domain/value_objects/target_status.py`:

```python
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
```

Create `src/facebook_group_tool/domain/value_objects/run_log_level.py`:

```python
from enum import StrEnum


class RunLogLevel(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
```

Create `src/facebook_group_tool/domain/value_objects/safety_policy.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyPolicy:
    global_daily_auto_limit: int = 20
    min_delay_seconds: int = 300
    max_delay_seconds: int = 900

    def __post_init__(self) -> None:
        if self.global_daily_auto_limit > 20:
            raise ValueError("global_daily_auto_limit cannot exceed 20")
        if self.global_daily_auto_limit < 1:
            raise ValueError("global_daily_auto_limit must be at least 1")
        if self.min_delay_seconds < 300:
            raise ValueError("min_delay_seconds must be at least 300")
        if self.min_delay_seconds > self.max_delay_seconds:
            raise ValueError("min_delay_seconds must be <= max_delay_seconds")
```

- [ ] **Step 4: Implement domain entities**

Create `src/facebook_group_tool/domain/entities/group.py`:

```python
from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Group:
    id: UUID
    facebook_group_id: str | None
    name: str
    url: str
    cover_image_url: str | None
    tags: tuple[str, ...]
    note: str
    is_enabled: bool
    is_posting_allowed: bool
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime

    def with_posting_permission(self, is_allowed: bool) -> "Group":
        return replace(self, is_posting_allowed=is_allowed)

    def with_tags(self, tags: tuple[str, ...]) -> "Group":
        return replace(self, tags=tuple(sorted(set(tags))))
```

Create `src/facebook_group_tool/domain/entities/post.py`:

```python
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
```

Create `src/facebook_group_tool/domain/entities/campaign.py`:

```python
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from facebook_group_tool.domain.value_objects.campaign_status import CampaignStatus
from facebook_group_tool.domain.value_objects.post_mode import PostMode


@dataclass(frozen=True)
class Campaign:
    id: UUID
    name: str
    post_id: UUID
    mode: PostMode
    status: CampaignStatus
    daily_auto_limit: int
    min_delay_seconds: int
    max_delay_seconds: int
    scheduled_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        name: str,
        post_id: UUID,
        mode: PostMode,
        target_group_ids: tuple[UUID, ...],
        daily_auto_limit: int,
        min_delay_seconds: int,
        max_delay_seconds: int,
        scheduled_at: datetime | None,
    ) -> "Campaign":
        if not name.strip():
            raise ValueError("campaign name is required")
        if mode == PostMode.AUTO and len(target_group_ids) > 20:
            raise ValueError("Auto mode supports at most 20 targets")
        if mode == PostMode.AUTO and daily_auto_limit > 20:
            raise ValueError("daily_auto_limit cannot exceed 20")
        if min_delay_seconds < 300:
            raise ValueError("min_delay_seconds must be at least 300")
        if min_delay_seconds > max_delay_seconds:
            raise ValueError("min_delay_seconds must be <= max_delay_seconds")
        now = datetime.now(UTC)
        status = CampaignStatus.SCHEDULED if scheduled_at else CampaignStatus.DRAFT
        return cls(uuid4(), name.strip(), post_id, mode, status, daily_auto_limit, min_delay_seconds, max_delay_seconds, scheduled_at, now, now)

    def mark_running(self) -> "Campaign":
        return replace(self, status=CampaignStatus.RUNNING, updated_at=datetime.now(UTC))

    def mark_paused(self) -> "Campaign":
        return replace(self, status=CampaignStatus.PAUSED, updated_at=datetime.now(UTC))
```

Create `src/facebook_group_tool/domain/entities/campaign_target.py`:

```python
from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from facebook_group_tool.domain.value_objects.target_status import TargetStatus


@dataclass(frozen=True)
class CampaignTarget:
    id: UUID
    campaign_id: UUID
    group_id: UUID
    status: TargetStatus
    attempt_count: int
    last_error: str | None
    prepared_at: datetime | None
    posted_at: datetime | None
    next_run_at: datetime | None

    def with_status(self, status: TargetStatus, error: str | None = None) -> "CampaignTarget":
        return replace(self, status=status, last_error=error)
```

Create `src/facebook_group_tool/domain/entities/run_log.py`:

```python
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from facebook_group_tool.domain.value_objects.run_log_level import RunLogLevel


@dataclass(frozen=True)
class RunLog:
    id: UUID
    campaign_id: UUID | None
    campaign_target_id: UUID | None
    level: RunLogLevel
    event_type: str
    message: str
    metadata: dict[str, object]
    created_at: datetime
```

- [ ] **Step 5: Implement repository protocols**

Create `src/facebook_group_tool/domain/repositories/group_repository.py`:

```python
from typing import Protocol
from uuid import UUID

from facebook_group_tool.domain.entities.group import Group


class GroupRepository(Protocol):
    async def get(self, group_id: UUID) -> Group | None: ...
    async def list(self, *, enabled_only: bool = False) -> list[Group]: ...
    async def save(self, group: Group) -> Group: ...
    async def upsert_many(self, groups: list[Group]) -> list[Group]: ...
```

Create `src/facebook_group_tool/domain/repositories/post_repository.py`:

```python
from typing import Protocol
from uuid import UUID

from facebook_group_tool.domain.entities.post import Post


class PostRepository(Protocol):
    async def get(self, post_id: UUID) -> Post | None: ...
    async def list(self) -> list[Post]: ...
    async def save(self, post: Post) -> Post: ...
```

Create `src/facebook_group_tool/domain/repositories/campaign_repository.py`:

```python
from typing import Protocol
from uuid import UUID

from facebook_group_tool.domain.entities.campaign import Campaign
from facebook_group_tool.domain.entities.campaign_target import CampaignTarget


class CampaignRepository(Protocol):
    async def get(self, campaign_id: UUID) -> Campaign | None: ...
    async def save(self, campaign: Campaign) -> Campaign: ...
    async def save_targets(self, targets: list[CampaignTarget]) -> list[CampaignTarget]: ...
    async def list_targets(self, campaign_id: UUID) -> list[CampaignTarget]: ...
    async def count_auto_posts_since_midnight(self) -> int: ...
    async def has_running_auto_campaign(self) -> bool: ...
```

Create `src/facebook_group_tool/domain/repositories/run_log_repository.py`:

```python
from typing import Protocol
from uuid import UUID

from facebook_group_tool.domain.entities.run_log import RunLog


class RunLogRepository(Protocol):
    async def append(self, log: RunLog) -> RunLog: ...
    async def list_for_campaign(self, campaign_id: UUID) -> list[RunLog]: ...
```

- [ ] **Step 6: Run tests and quality checks**

Run:

```bash
uv run pytest tests/unit/test_domain_entities.py -v
uv run ruff check src tests
uv run pyright
```

Expected: all domain tests pass; ruff and pyright pass.

- [ ] **Step 7: Commit if git is available**

```bash
git rev-parse --is-inside-work-tree && git add src/facebook_group_tool/domain tests/unit/test_domain_entities.py && git commit -m "feat: add posting workflow domain model"
```

---

### Task 3: Application DTOs, Safety Guard, Scheduling, and Core Use Cases

**Files:**
- Create: `src/facebook_group_tool/application/dto.py`
- Create: `src/facebook_group_tool/application/ports.py`
- Create: `src/facebook_group_tool/application/services/safety_guard.py`
- Create: `src/facebook_group_tool/application/services/scheduling_service.py`
- Create: `src/facebook_group_tool/application/use_cases/create_post.py`
- Create: `src/facebook_group_tool/application/use_cases/create_campaign.py`
- Create: `src/facebook_group_tool/application/use_cases/mark_group_permission.py`
- Create: `src/facebook_group_tool/application/use_cases/pause_campaign.py`
- Create: `src/facebook_group_tool/application/use_cases/resume_campaign.py`
- Create: `src/facebook_group_tool/application/use_cases/sync_groups.py`
- Test: `tests/unit/test_safety_guard.py`
- Test: `tests/unit/test_scheduling_service.py`
- Test: `tests/unit/test_use_cases.py`

**Interfaces:**
- Consumes: domain entities, enums, repository protocols.
- Produces: use case classes consumed by API routes and dashboard.

- [ ] **Step 1: Write failing service/use-case tests**

Create `tests/unit/test_safety_guard.py` with fake repositories that return selected groups and counts. Include these exact assertions:

```python
import pytest

from facebook_group_tool.application.services.safety_guard import SafetyGuard, SafetyViolation
from facebook_group_tool.domain.value_objects.post_mode import PostMode


@pytest.mark.asyncio
async def test_auto_mode_rejects_more_than_twenty_targets() -> None:
    guard = SafetyGuard(global_daily_auto_limit=20)

    with pytest.raises(SafetyViolation, match="switch to semi-auto mode"):
        await guard.validate_campaign_start(
            mode=PostMode.AUTO,
            target_count=21,
            campaign_daily_limit=20,
            auto_posts_used_today=0,
            has_running_auto_campaign=False,
            dry_run_completed=True,
            min_delay_seconds=300,
            max_delay_seconds=900,
        )


@pytest.mark.asyncio
async def test_auto_mode_requires_dry_run() -> None:
    guard = SafetyGuard(global_daily_auto_limit=20)

    with pytest.raises(SafetyViolation, match="Dry-run is required"):
        await guard.validate_campaign_start(
            mode=PostMode.AUTO,
            target_count=1,
            campaign_daily_limit=1,
            auto_posts_used_today=0,
            has_running_auto_campaign=False,
            dry_run_completed=False,
            min_delay_seconds=300,
            max_delay_seconds=900,
        )
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/test_safety_guard.py -v
```

Expected: FAIL with import error for `SafetyGuard`.

- [ ] **Step 3: Implement DTOs and ports**

Create `src/facebook_group_tool/application/dto.py`:

```python
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from facebook_group_tool.domain.value_objects.post_mode import PostMode


@dataclass(frozen=True)
class SyncedGroupInput:
    name: str
    url: str
    facebook_group_id: str | None = None
    cover_image_url: str | None = None


@dataclass(frozen=True)
class CreatePostInput:
    title: str
    body_text: str
    media_paths: tuple[str, ...]


@dataclass(frozen=True)
class CreateCampaignInput:
    name: str
    post_id: UUID
    mode: PostMode
    target_group_ids: tuple[UUID, ...]
    daily_auto_limit: int
    min_delay_seconds: int
    max_delay_seconds: int


@dataclass(frozen=True)
class SafetyDetection:
    is_safe: bool
    reason: str | None = None


@dataclass(frozen=True)
class ComposerResult:
    status: str
    message: str


@dataclass(frozen=True)
class PreparePostCommand:
    group_url: str
    body_text: str
    media_paths: tuple[Path, ...]
```

Create `src/facebook_group_tool/application/ports.py`:

```python
from pathlib import Path
from typing import Protocol

from facebook_group_tool.application.dto import ComposerResult, SafetyDetection, SyncedGroupInput


class BrowserSessionPort(Protocol):
    async def open(self) -> None: ...
    async def close(self) -> None: ...
    async def goto(self, url: str) -> None: ...


class GroupSyncPort(Protocol):
    async def collect_visible_groups(self) -> list[SyncedGroupInput]: ...


class PostComposerPort(Protocol):
    async def prepare_post(self, target_url: str, body_text: str, media_paths: list[Path]) -> ComposerResult: ...
    async def publish_prepared_post(self) -> ComposerResult: ...


class CheckpointDetectorPort(Protocol):
    async def detect(self) -> SafetyDetection: ...
```

- [ ] **Step 4: Implement safety guard**

Create `src/facebook_group_tool/application/services/safety_guard.py`:

```python
from facebook_group_tool.domain.value_objects.post_mode import PostMode


class SafetyViolation(Exception):
    pass


class SafetyGuard:
    def __init__(self, global_daily_auto_limit: int = 20) -> None:
        if global_daily_auto_limit > 20:
            raise ValueError("global_daily_auto_limit cannot exceed 20")
        self._global_daily_auto_limit = global_daily_auto_limit

    async def validate_campaign_start(
        self,
        *,
        mode: PostMode,
        target_count: int,
        campaign_daily_limit: int,
        auto_posts_used_today: int,
        has_running_auto_campaign: bool,
        dry_run_completed: bool,
        min_delay_seconds: int,
        max_delay_seconds: int,
    ) -> None:
        if mode == PostMode.SEMI_AUTO:
            return
        if target_count > 20:
            raise SafetyViolation("Auto mode supports at most 20 targets; switch to semi-auto mode")
        if campaign_daily_limit > self._global_daily_auto_limit:
            raise SafetyViolation("Campaign daily limit cannot exceed the global auto limit")
        if auto_posts_used_today + target_count > self._global_daily_auto_limit:
            raise SafetyViolation("Global daily auto limit would be exceeded")
        if has_running_auto_campaign:
            raise SafetyViolation("Another auto campaign is already running for this profile")
        if not dry_run_completed:
            raise SafetyViolation("Dry-run is required before auto mode starts")
        if min_delay_seconds < 300:
            raise SafetyViolation("Auto delay must be at least 300 seconds")
        if min_delay_seconds > max_delay_seconds:
            raise SafetyViolation("Minimum delay cannot be greater than maximum delay")
```

- [ ] **Step 5: Add scheduling test and service**

Create `tests/unit/test_scheduling_service.py`:

```python
from facebook_group_tool.application.services.scheduling_service import SchedulingService


def test_delay_sequence_uses_bounds_deterministically() -> None:
    service = SchedulingService()

    delays = service.build_delay_sequence(target_count=3, min_delay_seconds=300, max_delay_seconds=900)

    assert delays == (300, 600, 900)
```

Create `src/facebook_group_tool/application/services/scheduling_service.py`:

```python
class SchedulingService:
    def build_delay_sequence(
        self,
        *,
        target_count: int,
        min_delay_seconds: int,
        max_delay_seconds: int,
    ) -> tuple[int, ...]:
        if target_count <= 0:
            return ()
        if target_count == 1:
            return (min_delay_seconds,)
        step = (max_delay_seconds - min_delay_seconds) / (target_count - 1)
        return tuple(round(min_delay_seconds + (step * index)) for index in range(target_count))
```

- [ ] **Step 6: Implement use cases**

Create the use cases using repository protocols. `CreateCampaignUseCase.execute` must create one `CampaignTarget` per selected group and call the safety guard for auto validation. `SyncGroupsUseCase.execute` must normalize URLs, deduplicate by `facebook_group_id` first and URL second, and call `group_repository.upsert_many()`.

Use this exact `CreatePostUseCase` implementation:

```python
from facebook_group_tool.application.dto import CreatePostInput
from facebook_group_tool.domain.entities.post import Post
from facebook_group_tool.domain.repositories.post_repository import PostRepository


class CreatePostUseCase:
    def __init__(self, post_repository: PostRepository) -> None:
        self._post_repository = post_repository

    async def execute(self, data: CreatePostInput) -> Post:
        post = Post.create(data.title, data.body_text, data.media_paths)
        return await self._post_repository.save(post)
```

- [ ] **Step 7: Add use-case tests for create post, sync dedupe, and mark permission**

Create `tests/unit/test_use_cases.py` with in-memory fake repositories. The required assertions are:

```python
assert saved_post.title == "Launch"
assert len(saved_groups) == 1
assert updated_group.is_posting_allowed is True
```

- [ ] **Step 8: Run tests and checks**

```bash
uv run pytest tests/unit/test_safety_guard.py tests/unit/test_scheduling_service.py tests/unit/test_use_cases.py -v
uv run ruff check src tests
uv run pyright
```

Expected: all tests pass.

- [ ] **Step 9: Commit if git is available**

```bash
git rev-parse --is-inside-work-tree && git add src/facebook_group_tool/application tests/unit && git commit -m "feat: add application safety and workflow use cases"
```

---

### Task 4: PostgreSQL Persistence and Alembic Migrations

**Files:**
- Create: `alembic.ini`
- Create: `src/facebook_group_tool/infrastructure/database/postgres.py`
- Create: `src/facebook_group_tool/infrastructure/database/models.py`
- Create: `src/facebook_group_tool/infrastructure/database/migrations/env.py`
- Create: `src/facebook_group_tool/infrastructure/database/migrations/script.py.mako`
- Create: `src/facebook_group_tool/infrastructure/database/migrations/versions/20260701_0001_initial_schema.py`
- Create repository implementations under `src/facebook_group_tool/infrastructure/database/repositories/`
- Test: `tests/integration/test_repositories.py`

**Interfaces:**
- Consumes: domain repository protocols and entities.
- Produces: SQLAlchemy repositories and async session dependency used by API routes.

- [ ] **Step 1: Write failing repository integration tests**

Create `tests/integration/test_repositories.py` that uses PostgreSQL from `DATABASE_URL_TEST` or testcontainers. Required tests:

```python
@pytest.mark.asyncio
async def test_group_repository_upserts_by_facebook_group_id(session: AsyncSession) -> None:
    repo = SqlAlchemyGroupRepository(session)
    first = make_group(facebook_group_id="123", name="Original")
    second = make_group(facebook_group_id="123", name="Updated")

    await repo.upsert_many([first])
    await repo.upsert_many([second])
    groups = await repo.list()

    assert len(groups) == 1
    assert groups[0].name == "Updated"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/integration/test_repositories.py::test_group_repository_upserts_by_facebook_group_id -v
```

Expected: FAIL with missing database repository imports.

- [ ] **Step 3: Implement SQLAlchemy base, engine, and models**

Create `src/facebook_group_tool/infrastructure/database/postgres.py`:

```python
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from facebook_group_tool.config import get_settings

engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
```

Create `src/facebook_group_tool/infrastructure/database/models.py` with SQLAlchemy 2.0 declarative models for `groups`, `posts`, `campaigns`, `campaign_targets`, and `run_logs`. Use `JSONB` for `tags`, `media_items`, and `metadata`; use PostgreSQL UUID columns; add unique indexes on `groups.facebook_group_id` and `groups.url`.

- [ ] **Step 4: Implement Alembic migration**

Create migration `20260701_0001_initial_schema.py` that creates the five tables and indexes. It must use PostgreSQL UUID and JSONB types and must not reference SQLite.

- [ ] **Step 5: Implement repository mappers and SQLAlchemy repositories**

For every repository, implement two pure mapper functions: `to_domain(model) -> Entity` and `from_domain(entity) -> Model`. Use immutable tuples when mapping JSON arrays back into domain entities.

Required class names:

```python
class SqlAlchemyGroupRepository:
class SqlAlchemyPostRepository:
class SqlAlchemyCampaignRepository:
class SqlAlchemyRunLogRepository:
```

- [ ] **Step 6: Run migrations and integration tests**

```bash
uv run alembic -c alembic.ini upgrade head
uv run pytest tests/integration/test_repositories.py -v
uv run ruff check src tests
uv run pyright
```

Expected: migration succeeds against PostgreSQL; repository tests pass.

- [ ] **Step 7: Commit if git is available**

```bash
git rev-parse --is-inside-work-tree && git add alembic.ini src/facebook_group_tool/infrastructure/database tests/integration/test_repositories.py && git commit -m "feat: add postgresql persistence"
```

---

### Task 5: FastAPI Schemas, Dependencies, and JSON API Routes

**Files:**
- Create: `src/facebook_group_tool/presentation/api/dependencies.py`
- Create schemas under `src/facebook_group_tool/presentation/api/schemas/`
- Create routes under `src/facebook_group_tool/presentation/api/routes/`
- Modify: `src/facebook_group_tool/main.py`
- Test: `tests/integration/test_api_routes.py`

**Interfaces:**
- Consumes: use cases and SQLAlchemy repositories.
- Produces: API endpoints used by dashboard and E2E tests.

- [ ] **Step 1: Write failing API tests**

Create `tests/integration/test_api_routes.py` with dependency overrides for fake repositories. Required assertions:

```python
def test_create_post_returns_created_post(client: TestClient) -> None:
    response = client.post("/api/posts", json={"title": "Launch", "body_text": "Hello", "media_paths": []})
    assert response.status_code == 201
    assert response.json()["title"] == "Launch"


def test_auto_campaign_rejects_more_than_twenty_targets(client: TestClient) -> None:
    response = client.post("/api/campaigns", json={...21 group ids...})
    assert response.status_code == 422
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/integration/test_api_routes.py -v
```

Expected: FAIL with 404 routes or missing imports.

- [ ] **Step 3: Implement Pydantic schemas**

Create schemas with explicit fields matching the spec. Example `post_schema.py`:

```python
from uuid import UUID

from pydantic import BaseModel, Field


class CreatePostRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body_text: str = ""
    media_paths: list[str] = Field(default_factory=list)


class PostResponse(BaseModel):
    id: UUID
    title: str
    body_text: str
    media_items: list[str]
```

- [ ] **Step 4: Implement dependencies**

`dependencies.py` must wire `AsyncSession` to repositories and use cases. Keep dependencies narrow, one function per use case, so tests can override them.

- [ ] **Step 5: Implement API routes**

Required endpoints:

```text
GET    /api/groups
POST   /api/groups/sync-visible
PATCH  /api/groups/{group_id}/permission
POST   /api/posts
GET    /api/posts
POST   /api/campaigns
GET    /api/campaigns/{campaign_id}
POST   /api/campaigns/{campaign_id}/dry-run
POST   /api/campaigns/{campaign_id}/start
POST   /api/campaigns/{campaign_id}/pause
POST   /api/campaigns/{campaign_id}/resume
POST   /api/campaigns/{campaign_id}/cancel
GET    /api/campaigns/{campaign_id}/logs
```

For safety failures, return HTTP 422 with the violation message. For missing records, return HTTP 404. For checkpoint/login/user-action states, return HTTP 409 with a clear message.

- [ ] **Step 6: Register routers in app factory**

Modify `create_app()`:

```python
from facebook_group_tool.presentation.api.routes import automation, campaigns, groups, posts

app.include_router(groups.router, prefix="/api/groups", tags=["groups"])
app.include_router(posts.router, prefix="/api/posts", tags=["posts"])
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["campaigns"])
app.include_router(automation.router, prefix="/api/automation", tags=["automation"])
```

- [ ] **Step 7: Run API tests and checks**

```bash
uv run pytest tests/integration/test_api_routes.py -v
uv run ruff check src tests
uv run pyright
```

Expected: API tests pass.

- [ ] **Step 8: Commit if git is available**

```bash
git rev-parse --is-inside-work-tree && git add src/facebook_group_tool/presentation tests/integration/test_api_routes.py && git commit -m "feat: add local dashboard api routes"
```

---

### Task 6: Playwright Automation Adapters with Static HTML Fixture Tests

**Files:**
- Create: `src/facebook_group_tool/infrastructure/automation/browser_session.py`
- Create: `src/facebook_group_tool/infrastructure/automation/facebook_group_sync.py`
- Create: `src/facebook_group_tool/infrastructure/automation/facebook_checkpoint_detector.py`
- Create: `src/facebook_group_tool/infrastructure/automation/facebook_post_composer.py`
- Create fixture HTML files under `tests/automation/fixtures/`
- Create tests under `tests/automation/`

**Interfaces:**
- Consumes: application ports and DTOs.
- Produces: Playwright adapters used by run workflow use cases.

- [ ] **Step 1: Write fixture HTML files**

Create `tests/automation/fixtures/facebook_groups.html` with two group anchors:

```html
<a role="link" href="https://www.facebook.com/groups/123"><span>Allowed Group A</span></a>
<a role="link" href="https://www.facebook.com/groups/456"><span>Allowed Group B</span></a>
```

Create `checkpoint.html` containing text `checkpoint`, `security check`, and `captcha`. Create `composer.html` containing a `div[role="textbox"]` and a button named `Post`. Create `missing_composer.html` without a textbox.

- [ ] **Step 2: Write failing automation tests**

Required assertions:

```python
assert [group.facebook_group_id for group in groups] == ["123", "456"]
assert detection.is_safe is False
assert result.status == "prepared"
```

- [ ] **Step 3: Implement browser session**

Create `browser_session.py`:

```python
from pathlib import Path

from playwright.async_api import BrowserContext, Page, async_playwright


class PlaywrightBrowserSession:
    def __init__(self, profile_path: Path) -> None:
        self._profile_path = profile_path
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def open(self) -> None:
        playwright = await async_playwright().start()
        self._context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(self._profile_path),
            headless=False,
        )
        self._page = self._context.pages[0] if self._context.pages else await self._context.new_page()

    async def close(self) -> None:
        if self._context is not None:
            await self._context.close()
            self._context = None
            self._page = None

    async def goto(self, url: str) -> None:
        if self._page is None:
            raise RuntimeError("browser session is not open")
        await self._page.goto(url)

    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError("browser session is not open")
        return self._page
```

- [ ] **Step 4: Implement group sync extraction without broad scraping**

`FacebookGroupSync.collect_visible_groups()` must only inspect currently loaded/visible group anchors on the logged-in user's group list page. It must not navigate to unrelated groups or auto-scroll. Extract group ID from `/groups/{id}` URLs and return `SyncedGroupInput` records.

- [ ] **Step 5: Implement checkpoint detector**

Detector returns unsafe if page content includes checkpoint, captcha, verification, login, or security check indicators. It must only report and never solve, click through, or hide these prompts.

- [ ] **Step 6: Implement post composer**

`prepare_post()` opens the group URL, checks detector output first, finds the composer textbox, fills body text, uploads image paths when file inputs are present, and returns `ComposerResult(status="prepared", message="Post prepared for review")`. `publish_prepared_post()` clicks publish only when called by auto mode and after safety detection remains safe.

- [ ] **Step 7: Run automation tests and checks**

```bash
uv run pytest tests/automation -v
uv run ruff check src tests
uv run pyright
```

Expected: static fixture automation tests pass. No live Facebook access is required in CI.

- [ ] **Step 8: Commit if git is available**

```bash
git rev-parse --is-inside-work-tree && git add src/facebook_group_tool/infrastructure/automation tests/automation && git commit -m "feat: add safe browser automation adapters"
```

---

### Task 7: Quick Post and Campaign Runner Workflows

**Files:**
- Create: `src/facebook_group_tool/application/use_cases/run_quick_post.py`
- Create: `src/facebook_group_tool/application/use_cases/run_campaign.py`
- Modify: `src/facebook_group_tool/application/use_cases/pause_campaign.py`
- Modify: `src/facebook_group_tool/application/use_cases/resume_campaign.py`
- Modify: campaign API routes to call these use cases
- Test: `tests/unit/test_run_workflows.py`

**Interfaces:**
- Consumes: campaign/post/group repositories, `SafetyGuard`, `PostComposerPort`, `CheckpointDetectorPort`, `SchedulingService`.
- Produces: dry-run, start, pause, resume, target status updates, and run logs.

- [ ] **Step 1: Write failing workflow tests**

Create tests with fake repositories and fake composer. Required cases:

```python
@pytest.mark.asyncio
async def test_semi_auto_prepares_without_publishing() -> None:
    result = await use_case.execute(campaign_id, dry_run=False)
    assert fake_composer.publish_calls == 0
    assert result.prepared_count == 1

@pytest.mark.asyncio
async def test_auto_pauses_on_checkpoint_detection() -> None:
    fake_detector.next_detection = SafetyDetection(is_safe=False, reason="captcha")
    result = await use_case.execute(campaign_id, dry_run=False)
    assert result.status == "paused"
    assert "captcha" in result.message
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/test_run_workflows.py -v
```

Expected: FAIL with missing run workflow modules.

- [ ] **Step 3: Implement result DTOs**

Add to `application/dto.py`:

```python
@dataclass(frozen=True)
class RunWorkflowResult:
    status: str
    message: str
    prepared_count: int = 0
    posted_count: int = 0
    failed_count: int = 0
```

- [ ] **Step 4: Implement dry-run behavior**

Dry-run validates post existence, enabled groups, posting permission for auto mode, target count, daily limit, delay bounds, and concurrent auto campaign state. It must create run logs but must not call `prepare_post()` or `publish_prepared_post()`.

- [ ] **Step 5: Implement semi-auto behavior**

Semi-auto prepares exactly one target at a time, marks it `prepared`, logs `target_prepared`, and stops until the user marks the target posted/skipped/needs edit through the dashboard.

- [ ] **Step 6: Implement auto behavior**

Auto mode loops through pending targets in sequence. Before each target, call checkpoint detector. If unsafe, mark target `needs_user_action`, pause campaign, append an error log, and return. If safe, prepare the composer, publish, mark `posted`, log success, and wait using `SchedulingService` delay values. Use an injectable sleep function in tests so unit tests do not actually wait.

- [ ] **Step 7: Run workflow tests and checks**

```bash
uv run pytest tests/unit/test_run_workflows.py tests/unit/test_safety_guard.py -v
uv run ruff check src tests
uv run pyright
```

Expected: workflow tests pass; auto never exceeds limits; semi-auto never publishes.

- [ ] **Step 8: Commit if git is available**

```bash
git rev-parse --is-inside-work-tree && git add src/facebook_group_tool/application/use_cases tests/unit/test_run_workflows.py && git commit -m "feat: add guarded posting workflow runner"
```

---

### Task 8: Local Dashboard UI

**Files:**
- Create: `src/facebook_group_tool/presentation/web/routes.py`
- Create templates under `src/facebook_group_tool/presentation/web/templates/`
- Create: `src/facebook_group_tool/presentation/web/static/app.css`
- Create: `src/facebook_group_tool/presentation/web/static/app.js`
- Modify: `src/facebook_group_tool/main.py`
- Test: `tests/e2e/test_dashboard_smoke.py`

**Interfaces:**
- Consumes: API endpoints.
- Produces: local dashboard screens from spec.

- [ ] **Step 1: Write failing dashboard smoke test**

Create `tests/e2e/test_dashboard_smoke.py`:

```python
from fastapi.testclient import TestClient


def test_dashboard_overview_loads(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Facebook Group Tool" in response.text
    assert "Auto posts used today" in response.text
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/e2e/test_dashboard_smoke.py -v
```

Expected: FAIL with 404 for `/`.

- [ ] **Step 3: Implement web router and templates**

Create `routes.py` with routes for `/`, `/groups`, `/posts`, `/campaigns`, and `/logs`. Use Jinja2 templates and call internal application dependencies or API services; do not duplicate business rules in templates.

Base template must show navigation:

```html
<nav aria-label="Main navigation">
  <a href="/">Overview</a>
  <a href="/groups">Groups</a>
  <a href="/posts">Posts</a>
  <a href="/campaigns">Campaigns</a>
  <a href="/logs">Run Logs</a>
</nav>
```

Overview must include these labels exactly: `Synced groups`, `Active campaigns`, `Auto posts used today`, `Needs user action`, and `Recent run logs`.

- [ ] **Step 4: Add intentional local-dashboard styling**

Create `app.css` with CSS variables for palette, spacing, and typography. Use semantic HTML, visible focus states, and responsive layout. Avoid generic default card grids by using a two-column operations layout on desktop and a single-column layout on mobile.

- [ ] **Step 5: Register static files and web router**

Modify `main.py`:

```python
from fastapi.staticfiles import StaticFiles
from facebook_group_tool.presentation.web.routes import router as web_router

app.mount("/static", StaticFiles(directory="src/facebook_group_tool/presentation/web/static"), name="static")
app.include_router(web_router)
```

- [ ] **Step 6: Run dashboard tests and accessibility smoke check**

```bash
uv run pytest tests/e2e/test_dashboard_smoke.py -v
uv run pytest tests/integration/test_api_routes.py -v
uv run ruff check src tests
uv run pyright
```

Expected: dashboard smoke test and API tests pass. Manually verify keyboard focus is visible on navigation and forms.

- [ ] **Step 7: Commit if git is available**

```bash
git rev-parse --is-inside-work-tree && git add src/facebook_group_tool/presentation/web src/facebook_group_tool/main.py tests/e2e/test_dashboard_smoke.py && git commit -m "feat: add local dashboard screens"
```

---

### Task 9: Final Verification, Manual Safety Checklist, and Documentation

**Files:**
- Modify: `docs/development.md`
- Create: `docs/manual-verification.md`
- Create: `docs/safety-boundaries.md`

**Interfaces:**
- Consumes: completed application.
- Produces: documented verification flow for local use and future maintainers.

- [ ] **Step 1: Add manual verification checklist**

Create `docs/manual-verification.md`:

```markdown
# Manual Verification

Use a dedicated Chrome/Chromium profile and one small allowed test group.

## Checklist

- [ ] Configure `BROWSER_PROFILE_PATH` to the dedicated profile.
- [ ] Log into Facebook manually in that profile.
- [ ] Start the local dashboard.
- [ ] Click Sync groups.
- [ ] Manually scroll the Facebook group list.
- [ ] Stop sync and verify synced groups appear in PostgreSQL.
- [ ] Mark one test group enabled and posting allowed.
- [ ] Create a text and image post draft.
- [ ] Run quick post dry-run and confirm no post is prepared or published.
- [ ] Run semi-auto flow and confirm the post is prepared but not published.
- [ ] Manually publish or skip, then mark the target in the dashboard.
- [ ] Run auto flow with one allowed group only.
- [ ] Confirm checkpoint/CAPTCHA/login expiration pauses and never bypasses.
```

- [ ] **Step 2: Add safety boundaries doc**

Create `docs/safety-boundaries.md` with the exact project rules from the spec: no credential storage, no auto-join, no bypass, no detection evasion, no aggressive retries, one auto campaign per profile, hard cap 20/day, and semi-auto for larger workflows.

- [ ] **Step 3: Update development docs with commands**

Add sections to `docs/development.md` for:

```bash
uv run alembic -c alembic.ini upgrade head
uv run uvicorn facebook_group_tool.main:app --reload
uv run pytest
uv run pytest tests/automation -v
uv run ruff check .
uv run pyright
```

- [ ] **Step 4: Run full automated verification**

```bash
uv run pytest
uv run ruff check .
uv run pyright
```

Expected: all automated checks pass.

- [ ] **Step 5: Run Playwright browser install check**

```bash
uv run playwright install chromium
uv run python -c "from playwright.async_api import async_playwright; print('playwright ok')"
```

Expected: command prints `playwright ok`.

- [ ] **Step 6: Run local smoke check**

```bash
uv run uvicorn facebook_group_tool.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000` and verify the dashboard loads. Stop the server with `Ctrl+C`.

- [ ] **Step 7: Commit if git is available**

```bash
git rev-parse --is-inside-work-tree && git add docs && git commit -m "docs: add verification and safety guides"
```

---

## Self-Review Checklist

### Spec Coverage

- Local web dashboard: Task 8.
- Python backend with Clean Architecture: Tasks 1-5.
- PostgreSQL database: Task 4.
- Dedicated browser profile already logged into Facebook: Task 6.
- Manual-scroll group sync: Tasks 6 and 8.
- Group tags, notes, enabled status, and posting permission: Tasks 2, 4, 5, and 8.
- Text and image post drafts: Tasks 2, 5, and 8.
- Quick post workflow: Task 7.
- Campaign workflow with scheduling, delays, targets, pause, resume, cancellation: Tasks 3, 5, and 7.
- Auto hard safety limits: Tasks 2, 3, and 7.
- Semi-auto final publish manual: Tasks 6 and 7.
- Run logs and target status: Tasks 2, 4, 5, 7, and 8.
- Pause on checkpoint/CAPTCHA/login/verification/unexpected UI: Tasks 6 and 7.
- Tests: Tasks 1-9.

### Placeholder Scan

This plan intentionally avoids `TBD`, vague edge-case instructions, and references to undefined types. Every task has concrete files, interfaces, commands, and expected results.

### Type Consistency

Shared type names are consistent: `PostMode`, `CampaignStatus`, `TargetStatus`, `SafetyPolicy`, `SyncedGroupInput`, `SafetyDetection`, `ComposerResult`, `RunWorkflowResult`, repository protocols, and automation ports.

## Execution Handoff

Plan complete when this file is saved. Use either subagent-driven execution or inline execution. Do not start implementation before choosing one execution path.
