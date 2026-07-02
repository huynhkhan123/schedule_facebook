from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from facebook_group_tool.application.dto import ComposerResult, SafetyDetection
from facebook_group_tool.application.services.safety_guard import SafetyGuard
from facebook_group_tool.application.services.scheduling_service import SchedulingService
from facebook_group_tool.application.use_cases.run_campaign import RunCampaignUseCase
from facebook_group_tool.domain.entities.campaign import Campaign
from facebook_group_tool.domain.entities.campaign_target import CampaignTarget
from facebook_group_tool.domain.entities.group import Group
from facebook_group_tool.domain.entities.post import Post
from facebook_group_tool.domain.value_objects.campaign_status import CampaignStatus
from facebook_group_tool.domain.value_objects.post_mode import PostMode
from facebook_group_tool.domain.value_objects.target_status import TargetStatus


class FakePostRepository:
    def __init__(self, post: Post) -> None:
        self.post = post

    async def get(self, post_id: UUID) -> Post | None:
        return self.post if self.post.id == post_id else None

    async def list(self) -> list[Post]:
        return [self.post]

    async def save(self, post: Post) -> Post:
        self.post = post
        return post


class FakeGroupRepository:
    def __init__(self, group: Group) -> None:
        self.group = group

    async def get(self, group_id: UUID) -> Group | None:
        return self.group if self.group.id == group_id else None

    async def list(self, *, enabled_only: bool = False) -> list[Group]:
        return [self.group]

    async def save(self, group: Group) -> Group:
        self.group = group
        return group

    async def upsert_many(self, groups: list[Group]) -> list[Group]:
        self.group = groups[0]
        return groups


class FakeCampaignRepository:
    def __init__(self, campaign: Campaign, target: CampaignTarget) -> None:
        self.campaign = campaign
        self.targets = [target]

    async def get(self, campaign_id: UUID) -> Campaign | None:
        return self.campaign if self.campaign.id == campaign_id else None

    async def save(self, campaign: Campaign) -> Campaign:
        self.campaign = campaign
        return campaign

    async def save_targets(self, targets: list[CampaignTarget]) -> list[CampaignTarget]:
        self.targets = targets
        return targets

    async def list_targets(self, campaign_id: UUID) -> list[CampaignTarget]:
        return self.targets if self.campaign.id == campaign_id else []

    async def count_auto_posts_since_midnight(self) -> int:
        return 0

    async def has_running_auto_campaign(self) -> bool:
        return False


class FakeComposer:
    def __init__(self) -> None:
        self.prepare_calls = 0
        self.publish_calls = 0

    async def prepare_post(
        self,
        target_url: str,
        body_text: str,
        media_paths: list[Path],
    ) -> ComposerResult:
        self.prepare_calls += 1
        return ComposerResult(status="prepared", message="prepared")

    async def publish_prepared_post(self) -> ComposerResult:
        self.publish_calls += 1
        return ComposerResult(status="posted", message="posted")


class FakeDetector:
    def __init__(self) -> None:
        self.next_detection = SafetyDetection(is_safe=True)

    async def detect(self) -> SafetyDetection:
        return self.next_detection


def make_post() -> Post:
    return Post.create(title="Launch", body_text="Hello", media_items=())


def make_group() -> Group:
    now = datetime.now(UTC)
    return Group(
        id=uuid4(),
        facebook_group_id="123",
        name="Allowed Group",
        url="https://facebook.com/groups/123",
        cover_image_url=None,
        tags=(),
        note="",
        is_enabled=True,
        is_posting_allowed=True,
        last_synced_at=now,
        created_at=now,
        updated_at=now,
    )


def make_campaign(post_id: UUID, mode: PostMode) -> Campaign:
    return Campaign(
        id=uuid4(),
        name="Campaign",
        post_id=post_id,
        mode=mode,
        status=CampaignStatus.DRAFT,
        daily_auto_limit=1,
        min_delay_seconds=300,
        max_delay_seconds=900,
        scheduled_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def make_target(campaign_id: UUID, group_id: UUID) -> CampaignTarget:
    return CampaignTarget(
        id=uuid4(),
        campaign_id=campaign_id,
        group_id=group_id,
        status=TargetStatus.PENDING,
        attempt_count=0,
        last_error=None,
        prepared_at=None,
        posted_at=None,
        next_run_at=None,
    )


@pytest.mark.asyncio
async def test_semi_auto_prepares_without_publishing() -> None:
    post = make_post()
    group = make_group()
    campaign = make_campaign(post.id, PostMode.SEMI_AUTO)
    target = make_target(campaign.id, group.id)
    fake_composer = FakeComposer()
    use_case = RunCampaignUseCase(
        campaign_repository=FakeCampaignRepository(campaign, target),
        post_repository=FakePostRepository(post),
        group_repository=FakeGroupRepository(group),
        composer=fake_composer,
        detector=FakeDetector(),
        safety_guard=SafetyGuard(),
        scheduling_service=SchedulingService(),
        sleep=lambda _: None,
    )

    result = await use_case.execute(campaign.id, dry_run=False)

    assert fake_composer.publish_calls == 0
    assert result.prepared_count == 1


@pytest.mark.asyncio
async def test_auto_pauses_on_checkpoint_detection() -> None:
    post = make_post()
    group = make_group()
    campaign = make_campaign(post.id, PostMode.AUTO)
    target = make_target(campaign.id, group.id)
    fake_detector = FakeDetector()
    fake_detector.next_detection = SafetyDetection(is_safe=False, reason="captcha")
    use_case = RunCampaignUseCase(
        campaign_repository=FakeCampaignRepository(campaign, target),
        post_repository=FakePostRepository(post),
        group_repository=FakeGroupRepository(group),
        composer=FakeComposer(),
        detector=fake_detector,
        safety_guard=SafetyGuard(),
        scheduling_service=SchedulingService(),
        sleep=lambda _: None,
    )

    result = await use_case.execute(campaign.id, dry_run=False)

    assert result.status == "paused"
    assert "captcha" in result.message
