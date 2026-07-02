from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from facebook_group_tool.application.dto import RunWorkflowResult
from facebook_group_tool.application.ports import CheckpointDetectorPort, PostComposerPort
from facebook_group_tool.application.services.safety_guard import SafetyGuard
from facebook_group_tool.application.services.scheduling_service import SchedulingService
from facebook_group_tool.domain.entities.campaign_target import CampaignTarget
from facebook_group_tool.domain.repositories.campaign_repository import CampaignRepository
from facebook_group_tool.domain.repositories.group_repository import GroupRepository
from facebook_group_tool.domain.repositories.post_repository import PostRepository
from facebook_group_tool.domain.value_objects.post_mode import PostMode
from facebook_group_tool.domain.value_objects.target_status import TargetStatus

SleepCallable = Callable[[int], Awaitable[None] | None]


class RunCampaignUseCase:
    def __init__(
        self,
        *,
        campaign_repository: CampaignRepository,
        post_repository: PostRepository,
        group_repository: GroupRepository,
        composer: PostComposerPort,
        detector: CheckpointDetectorPort,
        safety_guard: SafetyGuard,
        scheduling_service: SchedulingService,
        sleep: SleepCallable,
    ) -> None:
        self._campaign_repository = campaign_repository
        self._post_repository = post_repository
        self._group_repository = group_repository
        self._composer = composer
        self._detector = detector
        self._safety_guard = safety_guard
        self._scheduling_service = scheduling_service
        self._sleep = sleep

    async def execute(self, campaign_id: UUID, *, dry_run: bool) -> RunWorkflowResult:
        campaign = await self._campaign_repository.get(campaign_id)
        if campaign is None:
            return RunWorkflowResult(status="failed", message="Campaign not found", failed_count=1)
        post = await self._post_repository.get(campaign.post_id)
        if post is None:
            return RunWorkflowResult(status="failed", message="Post not found", failed_count=1)
        targets = await self._campaign_repository.list_targets(campaign.id)
        pending_targets = [target for target in targets if target.status == TargetStatus.PENDING]
        if dry_run:
            return RunWorkflowResult(status="ok", message="Dry-run completed")

        if campaign.mode == PostMode.SEMI_AUTO:
            return await self._run_semi_auto(
                pending_targets,
                post.body_text,
                tuple(post.media_items),
            )
        await self._safety_guard.validate_campaign_start(
            mode=campaign.mode,
            target_count=len(pending_targets),
            campaign_daily_limit=campaign.daily_auto_limit,
            auto_posts_used_today=await self._campaign_repository.count_auto_posts_since_midnight(),
            has_running_auto_campaign=False,
            dry_run_completed=True,
            min_delay_seconds=campaign.min_delay_seconds,
            max_delay_seconds=campaign.max_delay_seconds,
        )
        delays = self._scheduling_service.build_delay_sequence(
            target_count=len(pending_targets),
            min_delay_seconds=campaign.min_delay_seconds,
            max_delay_seconds=campaign.max_delay_seconds,
        )
        return await self._run_auto(
            pending_targets,
            post.body_text,
            tuple(post.media_items),
            delays,
        )

    async def _run_semi_auto(
        self,
        targets: list[CampaignTarget],
        body_text: str,
        media_items: tuple[str, ...],
    ) -> RunWorkflowResult:
        target = targets[0] if targets else None
        if target is None:
            return RunWorkflowResult(status="completed", message="No pending targets")
        group = await self._group_repository.get(target.group_id)
        if group is None:
            return RunWorkflowResult(status="failed", message="Group not found", failed_count=1)
        result = await self._composer.prepare_post(
            group.url,
            body_text,
            [Path(item) for item in media_items],
        )
        if result.status != "prepared":
            failed = target.with_status(TargetStatus.NEEDS_USER_ACTION, result.message)
            await self._campaign_repository.save_targets([failed])
            return RunWorkflowResult(status="paused", message=result.message, failed_count=1)
        prepared = target.with_status(TargetStatus.PREPARED)
        await self._campaign_repository.save_targets([prepared])
        return RunWorkflowResult(
            status="prepared",
            message="Semi-auto post prepared for manual publishing",
            prepared_count=1,
        )

    async def _run_auto(
        self,
        targets: list[CampaignTarget],
        body_text: str,
        media_items: tuple[str, ...],
        delays: tuple[int, ...],
    ) -> RunWorkflowResult:
        posted_count = 0
        for index, target in enumerate(targets):
            detection = await self._detector.detect()
            if not detection.is_safe:
                paused = target.with_status(TargetStatus.NEEDS_USER_ACTION, detection.reason)
                await self._campaign_repository.save_targets([paused])
                return RunWorkflowResult(
                    status="paused",
                    message=detection.reason or "Needs user action",
                    posted_count=posted_count,
                )
            group = await self._group_repository.get(target.group_id)
            if group is None:
                failed = target.with_status(TargetStatus.FAILED, "Group not found")
                await self._campaign_repository.save_targets([failed])
                return RunWorkflowResult(status="failed", message="Group not found", failed_count=1)
            prepared_result = await self._composer.prepare_post(
                group.url,
                body_text,
                [Path(item) for item in media_items],
            )
            if prepared_result.status != "prepared":
                failed = target.with_status(TargetStatus.NEEDS_USER_ACTION, prepared_result.message)
                await self._campaign_repository.save_targets([failed])
                return RunWorkflowResult(status="paused", message=prepared_result.message)
            publish_result = await self._composer.publish_prepared_post()
            if publish_result.status != "posted":
                failed = target.with_status(TargetStatus.NEEDS_USER_ACTION, publish_result.message)
                await self._campaign_repository.save_targets([failed])
                return RunWorkflowResult(status="paused", message=publish_result.message)
            posted = target.with_status(TargetStatus.POSTED)
            posted = posted.__class__(
                id=posted.id,
                campaign_id=posted.campaign_id,
                group_id=posted.group_id,
                status=posted.status,
                attempt_count=posted.attempt_count + 1,
                last_error=None,
                prepared_at=posted.prepared_at,
                posted_at=datetime.now(UTC),
                next_run_at=posted.next_run_at,
            )
            await self._campaign_repository.save_targets([posted])
            posted_count += 1
            if index < len(delays):
                sleep_result = self._sleep(delays[index])
                if sleep_result is not None:
                    await sleep_result
        return RunWorkflowResult(
            status="completed",
            message="Auto campaign completed",
            posted_count=posted_count,
        )
