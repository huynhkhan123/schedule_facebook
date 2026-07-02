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
