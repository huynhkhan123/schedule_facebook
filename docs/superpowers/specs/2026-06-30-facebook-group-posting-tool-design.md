# Facebook Group Posting Tool Design

Date: 2026-06-30

## Goal

Build a local Python web dashboard that helps a user manage Facebook group posting workflows for groups where they are already a member and have permission to post promotional content.

The tool supports two operating modes:

1. **Auto mode** for small daily volume, capped at 1-20 groups per day.
2. **Semi-auto mode** for larger workflows, where the tool prepares the post and the user manually confirms publishing inside Facebook.

The design intentionally avoids spam, platform abuse, credential storage, CAPTCHA/checkpoint bypass, auto-joining groups, scraping unrelated groups, or evading Facebook safety systems.

## Scope

### MVP scope

- Local web dashboard.
- Python backend using Clean Architecture.
- PostgreSQL database.
- Browser automation using a dedicated Chrome/Chromium profile already logged into Facebook by the user.
- Group sync flow where the user manually scrolls their Facebook group list and the tool records visible groups.
- Group management with tags, notes, enabled status, and posting-permission status.
- Post drafts with text and images.
- Quick post workflow.
- Campaign workflow with scheduling, delay configuration, target status tracking, pause, resume, and cancellation.
- Auto mode with hard safety limits.
- Semi-auto mode where the final publish action is performed by the user.
- Run logs and status tracking.
- Pause on checkpoint, CAPTCHA, login expiration, verification prompts, browser crash, or unexpected UI.

### Deferred scope

- Link and video posting support.
- Multi-account support.
- Cloud deployment.
- Multi-user dashboard.
- Facebook Graph API integration.
- Advanced analytics.

## Safety Boundaries

The tool must follow these rules:

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

## Recommended Approach

Use a hybrid dashboard with safety guardrails.

- **Auto mode**: limited to 1-20 groups per day. Requires dry run, long delays, and automatic pause on suspicious or unexpected UI states.
- **Semi-auto mode**: supports larger workflows. The tool opens the group page and prepares the post composer, but the user manually reviews and clicks publish.

This approach balances automation with user control and provides a fallback when Facebook UI changes.

## Architecture Overview

```text
Local Web Dashboard
        |
        v
Python Backend API
        |
        +--> PostgreSQL
        |       - groups
        |       - posts
        |       - campaigns
        |       - campaign_targets
        |       - run_logs
        |
        +--> Automation Worker
                |
                +--> Dedicated browser profile
                +--> Facebook groups/pages
```

The application runs locally, for example at `http://localhost:8000`. The backend owns data and workflow state. The automation worker opens a dedicated browser profile that the user logged into manually.

## Clean Architecture

The backend is organized into four layers.

```text
app/
  domain/
    entities/
      group.py
      post.py
      campaign.py
      campaign_target.py
      run_log.py
    value_objects/
      post_mode.py
      target_status.py
      safety_policy.py
    repositories/
      group_repository.py
      post_repository.py
      campaign_repository.py
      run_log_repository.py

  application/
    use_cases/
      sync_groups.py
      create_post.py
      create_campaign.py
      run_quick_post.py
      run_campaign.py
      pause_campaign.py
      resume_campaign.py
      mark_group_permission.py
    services/
      safety_guard.py
      scheduling_service.py

  infrastructure/
    database/
      postgres.py
      models.py
      repositories/
        sqlalchemy_group_repository.py
        sqlalchemy_post_repository.py
        sqlalchemy_campaign_repository.py
        sqlalchemy_run_log_repository.py
      migrations/
    automation/
      browser_session.py
      facebook_group_sync.py
      facebook_post_composer.py
      facebook_checkpoint_detector.py
    storage/
      media_storage.py

  presentation/
    api/
      routes/
        groups.py
        posts.py
        campaigns.py
        automation.py
      schemas/
        group_schema.py
        post_schema.py
        campaign_schema.py
    web/
      templates_or_spa/
```

### Domain layer

Contains business entities and rules. It does not depend on FastAPI, Playwright, SQLAlchemy, or PostgreSQL.

Domain concepts include:

- Group metadata and posting permission.
- Post content and media references.
- Campaign mode and state.
- Campaign target state.
- Run log events.
- Safety policy values.

### Application layer

Contains use cases and application services. It depends on repository and automation interfaces, not concrete infrastructure.

Primary use cases:

- `SyncGroupsUseCase`
- `CreatePostUseCase`
- `CreateCampaignUseCase`
- `RunQuickPostUseCase`
- `RunCampaignUseCase`
- `PauseCampaignUseCase`
- `ResumeCampaignUseCase`
- `MarkGroupPermissionUseCase`

Application services:

- `SafetyGuard`
- `SchedulingService`

### Infrastructure layer

Contains implementation details:

- PostgreSQL connection and migrations.
- SQLAlchemy models and repositories.
- Browser automation with Playwright.
- Facebook group sync adapter.
- Facebook post composer adapter.
- Checkpoint/CAPTCHA detector that only pauses and reports; it never bypasses.
- Local media storage.

### Presentation layer

Contains FastAPI routes and the local dashboard UI. API routes call application use cases. Dashboard screens call the API.

## Data Model

### groups

Stores Facebook groups discovered during sync.

Fields:

- `id`
- `facebook_group_id`, nullable
- `name`
- `url`
- `cover_image_url`, nullable
- `tags`
- `note`
- `is_enabled`
- `is_posting_allowed`
- `last_synced_at`
- `created_at`
- `updated_at`

Deduplication order:

1. `facebook_group_id` if available.
2. Normalized `url`.
3. Potential duplicates by name are flagged for user review, not auto-merged.

### posts

Stores reusable post drafts.

Fields:

- `id`
- `title`
- `body_text`
- `link_url`, nullable and deferred for phase two
- `video_path`, nullable and deferred for phase two
- `media_items`
- `created_at`
- `updated_at`

MVP supports text and images. Link and video support are deferred.

### campaigns

Stores posting campaigns.

Fields:

- `id`
- `name`
- `post_id`
- `mode`: `auto` or `semi_auto`
- `status`: `draft`, `scheduled`, `running`, `paused`, `completed`, `failed`, `cancelled`
- `daily_auto_limit`
- `min_delay_seconds`
- `max_delay_seconds`
- `scheduled_at`
- `created_at`
- `updated_at`

### campaign_targets

Stores each group target in a campaign.

Fields:

- `id`
- `campaign_id`
- `group_id`
- `status`: `pending`, `running`, `prepared`, `posted`, `skipped`, `failed`, `needs_user_action`, `cancelled`
- `attempt_count`
- `last_error`
- `prepared_at`
- `posted_at`
- `next_run_at`

### run_logs

Stores audit events.

Fields:

- `id`
- `campaign_id`
- `campaign_target_id`
- `level`: `info`, `warning`, `error`
- `event_type`
- `message`
- `metadata`
- `created_at`

## Dashboard Screens

### Overview

Shows:

- Number of synced groups.
- Active campaign count.
- Auto posts used today.
- Campaigns or targets needing user action.
- Recent run logs.

### Groups

Supports:

- `Sync groups` action.
- Table of group name, URL, tags, enabled status, and posting permission status.
- Filtering by tag, status, and name.
- Bulk tag updates.
- Bulk posting-permission updates.

### Posts

Supports:

- Create text and image post drafts.
- Edit drafts.
- Preview body text and selected media.

### Quick Post

Supports:

- Select a post.
- Select target groups.
- Choose auto or semi-auto mode.
- Run dry-run.
- Start posting workflow.

### Campaigns

Supports:

- Create campaign.
- Select post.
- Select groups by filters and tags.
- Configure mode, schedule, delay, and daily limit.
- Start, pause, resume, and cancel.

### Run Logs

Supports:

- View logs by campaign and group.
- See target status.
- See errors requiring user action.

## Group Sync Flow

Sync is human-in-the-loop.

1. User opens dashboard and clicks `Sync groups`.
2. Backend opens the dedicated browser profile.
3. Browser navigates to the user's Facebook group list.
4. User manually scrolls the group list.
5. Worker reads group cards currently visible on the page.
6. Worker extracts group name, URL, group ID if available, and optional cover metadata.
7. Backend upserts groups through `SyncGroupsUseCase`.
8. Dashboard displays newly synced count.
9. User clicks `Stop sync` when finished.
10. User manages tags, enabled status, and posting permission in the Groups screen.

Sync statuses:

- `idle`
- `opening_browser`
- `waiting_for_user_scroll`
- `syncing_visible_groups`
- `needs_user_action`
- `stopped`
- `failed`

## Auto Mode Flow

Auto mode is for small daily volume.

1. User selects a post and group targets, or starts a campaign.
2. User runs dry-run.
3. Backend validates:
   - Post content exists.
   - Target groups are enabled.
   - Target groups are marked posting allowed.
   - Target count does not exceed campaign daily limit.
   - Global auto limit for the day is not exceeded.
   - Delay configuration is valid.
4. User starts auto mode.
5. Worker opens each group target in sequence.
6. Worker prepares the post composer by adding text and images.
7. Worker checks for login expiration, checkpoint, CAPTCHA, verification prompts, missing composer, or disabled post button.
8. If normal, worker publishes the post.
9. Backend records target status and run logs.
10. Worker waits a long delay before the next target.
11. If suspicious or unexpected UI appears, campaign pauses and waits for user action.

Auto mode guardrails:

- Default global hard limit: 20 groups per day.
- Campaign-specific limit can be lower.
- Dry-run is required before a real run.
- Default delay range should be long, such as 5-15 minutes between groups.
- No aggressive retries.
- One auto campaign at a time per profile.
- Serious target errors pause the campaign instead of blindly continuing.

## Semi-Auto Mode Flow

Semi-auto mode supports larger workflows while keeping the final publish action manual.

1. User selects a post and target groups, or starts a semi-auto campaign.
2. Worker opens the next group target.
3. Worker opens the composer.
4. Worker fills text and uploads images.
5. Worker does not click publish.
6. Target status becomes `prepared`.
7. User reviews the post in Facebook and manually publishes, skips, or edits.
8. User returns to the dashboard and chooses `Mark posted`, `Skip`, or `Needs edit`.
9. Worker proceeds to the next target only after user confirmation.

Semi-auto mode still pauses on checkpoint, CAPTCHA, login expiration, or unexpected UI.

## Error Handling

### Login expired

- Pause campaign.
- Mark relevant target as `needs_user_action`.
- Ask user to log in again in the browser.
- Resume only after user confirmation.

### Checkpoint, CAPTCHA, or verification prompt

- Pause campaign.
- Do not attempt to solve or bypass.
- User handles the prompt manually if they choose.
- Resume only after user confirmation.

### Composer not found

- Mark target failed or pause campaign depending on configuration.
- Log details for review.

### Media upload failed

- Mark target failed.
- Allow manual retry or semi-auto fallback.

### Post button disabled

- Pause target.
- Ask user to check content and posting permission.

### Network or browser crash

- Stop worker safely.
- Mark campaign paused.
- Allow resume later.

## Testing Strategy

### Unit tests

Cover:

- Domain entities.
- Safety guard.
- Campaign state transitions.
- Daily limit calculation.
- Scheduling calculations.
- Use cases with fake repositories and fake automation gateways.

### Integration tests

Cover:

- PostgreSQL test database.
- SQLAlchemy repositories.
- Alembic migrations.
- FastAPI routes.
- Campaign creation and filtering.

### Automation adapter tests

Use static HTML fixtures instead of live Facebook in CI.

Cover:

- Group card extraction.
- Composer detection.
- Checkpoint/CAPTCHA detection.
- Missing composer handling.

### Manual verification

Use a dedicated browser profile and a small allowed test group.

Verify:

- Group sync with manual scrolling.
- Post draft creation.
- Semi-auto flow.
- Auto flow with one allowed group only.
- Pause/resume behavior.

### Dashboard E2E tests

Use Playwright against the local dashboard.

Cover:

- Create post.
- Create groups.
- Create campaign.
- Start dry-run.
- Verify status and logs.

## Implementation Notes

Recommended backend stack:

- Python.
- FastAPI for HTTP API.
- SQLAlchemy for PostgreSQL persistence.
- Alembic for migrations.
- Playwright for browser automation.
- Pydantic for API schemas.
- Pytest for tests.

Use `uv` for project dependency management.

## Acceptance Criteria

The MVP is complete when:

- User can run a local dashboard.
- User can configure a dedicated browser profile path.
- User can sync groups by manually scrolling the Facebook group list.
- Synced groups are stored in PostgreSQL.
- User can tag, filter, enable, and mark groups as posting allowed.
- User can create text and image post drafts.
- User can run a quick post dry-run.
- User can create an auto campaign capped at 20 groups per day.
- User can create a semi-auto campaign for larger workflows.
- Auto mode pauses on checkpoint, CAPTCHA, login expiration, or unexpected UI.
- Semi-auto mode prepares posts but does not publish automatically.
- Run logs show campaign and target status.
- Unit and integration tests cover core business logic.
