# Safety Boundaries

This project is a local, human-in-the-loop dashboard for groups where the user is already a member and has permission to post promotional content.

Rules:

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
- Semi-auto mode prepares posts but does not click publish.
- Link and video posting remain deferred for the MVP.

If Facebook shows checkpoint, CAPTCHA, login expiration, verification, unavailable composer, disabled post button, browser crash, or unexpected UI, the app pauses and waits for user action.
