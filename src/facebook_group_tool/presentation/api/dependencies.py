from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from facebook_group_tool.application.services.safety_guard import SafetyGuard
from facebook_group_tool.application.use_cases.create_campaign import CreateCampaignUseCase
from facebook_group_tool.application.use_cases.create_post import CreatePostUseCase
from facebook_group_tool.application.use_cases.dispatch_connector_job import (
    DispatchConnectorJobUseCase,
)
from facebook_group_tool.application.use_cases.mark_group_permission import (
    MarkGroupPermissionUseCase,
)
from facebook_group_tool.application.use_cases.pause_campaign import PauseCampaignUseCase
from facebook_group_tool.application.use_cases.register_connector import RegisterConnectorUseCase
from facebook_group_tool.application.use_cases.resume_campaign import ResumeCampaignUseCase
from facebook_group_tool.application.use_cases.sync_groups import SyncGroupsUseCase
from facebook_group_tool.config import get_settings
from facebook_group_tool.domain.entities.campaign import Campaign
from facebook_group_tool.domain.entities.campaign_target import CampaignTarget
from facebook_group_tool.domain.entities.connector import Connector
from facebook_group_tool.domain.entities.connector_job import ConnectorJob
from facebook_group_tool.domain.entities.group import Group
from facebook_group_tool.domain.entities.post import Post
from facebook_group_tool.infrastructure.automation.group_sync_session import GroupSyncSessionService


class InMemoryPostRepository:
    def __init__(self) -> None:
        self.posts: dict[UUID, Post] = {}

    async def get(self, post_id: UUID) -> Post | None:
        return self.posts.get(post_id)

    async def list(self) -> list[Post]:
        return list(self.posts.values())

    async def save(self, post: Post) -> Post:
        self.posts = {**self.posts, post.id: post}
        return post


class InMemoryGroupRepository:
    def __init__(self) -> None:
        self.groups: dict[UUID, Group] = {}

    async def get(self, group_id: UUID) -> Group | None:
        return self.groups.get(group_id)

    async def list(self, *, enabled_only: bool = False) -> list[Group]:
        groups = list(self.groups.values())
        if enabled_only:
            return [group for group in groups if group.is_enabled]
        return groups

    async def save(self, group: Group) -> Group:
        self.groups = {**self.groups, group.id: group}
        return group

    async def upsert_many(self, groups: list[Group]) -> list[Group]:
        merged = dict(self.groups)
        for group in groups:
            existing = next(
                (
                    current
                    for current in merged.values()
                    if group.facebook_group_id
                    and current.facebook_group_id == group.facebook_group_id
                ),
                None,
            )
            merged = {**merged, existing.id: group} if existing else {**merged, group.id: group}
        self.groups = merged
        return groups


class InMemoryConnectorRepository:
    def __init__(self) -> None:
        self.connectors: dict[UUID, Connector] = {}

    async def get(self, connector_id: UUID) -> Connector | None:
        return self.connectors.get(connector_id)

    async def get_by_token(self, token: str) -> Connector | None:
        return next(
            (connector for connector in self.connectors.values() if connector.token == token),
            None,
        )

    async def list(self) -> list[Connector]:
        return list(self.connectors.values())

    async def save(self, connector: Connector) -> Connector:
        self.connectors = {**self.connectors, connector.id: connector}
        return connector


class InMemoryConnectorJobRepository:
    def __init__(self) -> None:
        self.jobs: dict[UUID, ConnectorJob] = {}

    async def get(self, job_id: UUID) -> ConnectorJob | None:
        return self.jobs.get(job_id)

    async def list_pending(self, connector_id: UUID) -> list[ConnectorJob]:
        return [
            job
            for job in self.jobs.values()
            if job.connector_id == connector_id and job.status == "pending"
        ]

    async def save(self, job: ConnectorJob) -> ConnectorJob:
        self.jobs = {**self.jobs, job.id: job}
        return job


class InMemoryPairingCodeRepository:
    def __init__(self) -> None:
        self.codes: set[str] = set()

    def create(self) -> str:
        code = uuid4().hex[:8].upper()
        self.codes = {*self.codes, code}
        return code

    def consume(self, code: str) -> bool:
        if code not in self.codes:
            return False
        self.codes = {item for item in self.codes if item != code}
        return True


class InMemoryCampaignRepository:
    def __init__(self) -> None:
        self.campaigns: dict[UUID, Campaign] = {}
        self.targets: dict[UUID, list[CampaignTarget]] = {}

    async def get(self, campaign_id: UUID) -> Campaign | None:
        return self.campaigns.get(campaign_id)

    async def save(self, campaign: Campaign) -> Campaign:
        self.campaigns = {**self.campaigns, campaign.id: campaign}
        return campaign

    async def save_targets(self, targets: list[CampaignTarget]) -> list[CampaignTarget]:
        grouped = dict(self.targets)
        for target in targets:
            current = grouped.get(target.campaign_id, [])
            without_target = [item for item in current if item.id != target.id]
            grouped[target.campaign_id] = [*without_target, target]
        self.targets = grouped
        return targets

    async def list_targets(self, campaign_id: UUID) -> list[CampaignTarget]:
        return self.targets.get(campaign_id, [])

    async def count_auto_posts_since_midnight(self) -> int:
        today = datetime.now(UTC).date()
        return sum(
            1
            for targets in self.targets.values()
            for target in targets
            if target.posted_at and target.posted_at.date() == today
        )

    async def has_running_auto_campaign(self) -> bool:
        return any(campaign.status == "running" for campaign in self.campaigns.values())


post_repository = InMemoryPostRepository()
group_repository = InMemoryGroupRepository()
campaign_repository = InMemoryCampaignRepository()
connector_repository = InMemoryConnectorRepository()
connector_job_repository = InMemoryConnectorJobRepository()
pairing_code_repository = InMemoryPairingCodeRepository()
group_sync_session = GroupSyncSessionService(
    get_settings().browser_profile_path,
    test_mode=get_settings().app_env == "test",
)


def get_group_sync_session() -> GroupSyncSessionService:
    return group_sync_session


def get_register_connector_use_case() -> RegisterConnectorUseCase:
    return RegisterConnectorUseCase(connector_repository)


def get_dispatch_connector_job_use_case() -> DispatchConnectorJobUseCase:
    return DispatchConnectorJobUseCase(connector_repository, connector_job_repository)


def get_create_post_use_case() -> CreatePostUseCase:
    return CreatePostUseCase(post_repository)


def get_sync_groups_use_case() -> SyncGroupsUseCase:
    return SyncGroupsUseCase(group_repository)


def get_mark_group_permission_use_case() -> MarkGroupPermissionUseCase:
    return MarkGroupPermissionUseCase(group_repository)


def get_create_campaign_use_case() -> CreateCampaignUseCase:
    return CreateCampaignUseCase(campaign_repository, SafetyGuard())


def get_pause_campaign_use_case() -> PauseCampaignUseCase:
    return PauseCampaignUseCase(campaign_repository)


def get_resume_campaign_use_case() -> ResumeCampaignUseCase:
    return ResumeCampaignUseCase(campaign_repository)
