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
