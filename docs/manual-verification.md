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
