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
