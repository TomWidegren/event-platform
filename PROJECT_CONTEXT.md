# Event Platform – Project Context

**Last updated:** 11 November 2026
**Last development checkpoint:** 11 November 2026
**Last documented published release:** v1.2.0
**Current focus:** Operational acceptance after iBIS v2 recovery

## 1. Purpose and source of truth

Event Platform monitors external event data, detects changes,
maintains persistent state and sends notifications.

GitHub is the authoritative source of truth.

ChatGPT Project files and previous attachments are not
automatically synchronized with GitHub.

At session start, establish whether an available PROJECT_CONTEXT.md
is the current GitHub version. If its freshness is uncertain,
request the current version before determining project status.

Read docs/ways-of-working.md and relevant repository documentation
before proposing implementation changes.

## 2. Current implementation

The last documented published release remains v1.2.0.

Subsequent Floorball development and the November recovery have
not been included in a confirmed new published release.

Implemented connectors:

- sgf_ranking
- golfbox_leaderboard
- tournytt_api
- ibis_floorball

Connectors expose fetch_snapshot(watch).

Automatic Floorball monitoring includes:

- Daily match discovery.
- Persistent match registry.
- Dynamic Live Watch selection.
- Activation 15 minutes before scheduled start.
- Multiple simultaneous Watches.
- Coordinated state and completion persistence.
- Player-specific notification highlighting.

Core implementation files include:

- watcher.py
- event_platform_live.py
- ibis_client.py
- connectors/ibis_floorball.py
- floorball_discovery.py
- floorball_match_selection.py

Persistent files:

- config.yml
- state.json
- match_registry.json

Preserve existing state, Watch identities and historical records.

## 3. iBIS incident and recovery

### Original failure

The old endpoint:

https://api.innebandy.se/StatsAppApi/api/startkit

returned HTTP 503 and prevented Floorball acquisition.

Both external schedules were disabled during the incident.

### Verified v2 authentication

The public statistics client uses:

1. GET /v2/api/auth/startkit
2. POST /v2/api/auth/handshake
3. Signed requests to /v2/api/public/

The handshake returns a session secret, ss, and server time, st.
The same HTTP session retains the session cookie.

Requests use:

- Bearer authorization.
- X-Signature.
- X-Timestamp.
- X-Nonce.

The signature is HMAC-SHA256 using the UTF-8 session secret.
The signed message contains, separated by newlines:

- Uppercase HTTP method.
- URL pathname and query string, if present.
- Server-adjusted timestamp in milliseconds.
- Fresh UUID nonce.
- SHA-256 hexadecimal hash of the request body.

The implemented client currently supports GET requests for matches
and competition match lists. These requests have an empty body
and no query string.

No personal iBIS login or copied browser credentials are required
for the verified flow.

### Implemented recovery

ibis_client.py owns temporary sessions and request signing.

Both the Floorball connector and Discovery now use this client.

Existing snapshot normalization and Discovery filtering were
preserved.

The client rejects unexpected API roots, unsupported resources,
redirect responses and invalid handshake data.

No new production scheduler or monitoring architecture was added.

### Verified on 11 November

- Diagnostic match retrieval: HTTP 200 for MatchID 1750719.
- Competition 45004 retrieval: HTTP 200, 110 matches returned.
- Expected match found in the competition response.
- Production connector retrieved match 1750693 with 24 events.
- Six notification-formatting tests passed.
- Baseline test passed with temporary state and no notification.
- Consolidated suite: 112 Floorball tests passed after integration.
- Golf regression step also completed successfully.
- Standalone Discovery completed against real data.
- Production Daily workflow completed through Discovery.
- Registry contained 31 entries, with zero required changes.
- Production Live completed manually.
- Reactivated cron-job.org Live dispatch returned HTTP 204.
- Corresponding GitHub Actions Live execution succeeded in 30 seconds.

The verified production Live execution processed two golf Watches.
No Floorball match was eligible during that execution.

Active-match monitoring and notification delivery using the new
v2 client remain to be verified during a real match.

## 4. Current scheduling

Both cron-job.org jobs have been re-enabled by the user.

Timezone: Europe/Stockholm.

### Daily

Workflow: .github/workflows/daily.yml

Schedule: 08:00 every day.

Responsibilities:

- SGF Ranking monitoring.
- Golf state persistence when required.
- Floorball Discovery and registry persistence when required.

Manual production execution succeeded after recovery.

The next automatic Daily execution remains to be observed.
The next expected execution after this checkpoint is
12 November 2026 at 08:00.

The Chromium installation was changed to:

python -m playwright install chromium

The former --with-deps installation stalled while downloading
Ubuntu font packages. Daily completed after removing that option.

### Live

Workflow: .github/workflows/live.yml

Entry point: event_platform_live.py

Schedule: Every five minutes, 06:00–23:55.

Cron expression:

*/5 6-23 * * *

Automatic scheduler dispatch and GitHub Actions execution have
been verified after reactivation.

## 5. Missed match on 6 November

MatchID: 1750719
Watch ID: floorball-match-1750719

The registry still contained monitoring_status: scheduled.
No corresponding entry existed in state.json.

Selection has no upper time limit for overdue matches, so this
match would still be selected after the outage.

The Live runner rejects a first Floorball observation containing
match activity or a final result.

The user explicitly approved a minimal manual closure:

- Only monitoring_status was changed to completed.
- No final snapshot was added.
- Existing state was preserved.
- No historical notifications were sent.

This was an exceptional administrative closure of monitoring,
not successful monitoring or final-snapshot persistence.

Do not recreate a baseline or reactivate this match.

## 6. Next operational acceptance

Next match in the inspected registry:

- MatchID: 1703587
- Tyresö Trollbäcken IBK (A) – Hammarbyhöjden IBK
- Scheduled start: 14 November 2026, 15:00
- Monitoring activation: 14:45

All times are Europe/Stockholm.

Verify:

1. Automatic Daily execution after reactivation.
2. Automatic match selection and pre-match baseline.
3. Successful v2 acquisition throughout the match.
4. Match notifications and player highlighting when applicable.
5. Final-result notification.
6. Final snapshot and registry completion.
7. Absence of unexpected duplicate notifications.

Protect working monitoring during the event.

## 7. Other unresolved issues

### Missing late-match notifications

MatchID 1703577, 25 October 2026.

Final result 11–5 and completed status were persisted, but the
last two goal notifications and final-result notification were
not received.

Root cause remains unresolved.

This incident is separate from the November authentication issue.

### Reliability limitations

- One connector failure can fail an entire workflow.
- Late first-observation recovery is not implemented.
- Overdue matches have no automatic expiration rule.
- Corrected or deleted events require further evaluation.
- Notification delivery and Git persistence are not transactional.
- Exactly-once notification delivery is not guaranteed.

Future changes require evidence and an agreed implementation scope.

### Scheduler token

The GitHub token used by cron-job.org expires on 28 November 2026.

Renew it before expiration and update both jobs.

Do not store tokens in repository documentation.

## 8. Documentation and remaining maintenance

The recovery, scheduling changes and manual match closure have
been documented in the following repository files.

The user confirmed committing updates to:

- PROJECT_CONTEXT.md
- README.md
- docs/ARCHITECTURE.md
- docs/decisions.md
- docs/ways-of-working.md
- docs/backlog.md

This revised handover corrects status wording left over from
the beginning of the documentation update.

Detailed design documents remain available:

- docs/design-floorball.md
- docs/design-floorball-automation.md
- docs/design-v1.2.md

Historical design assumptions must be distinguished from current
implementation. Review those documents when relevant to later work.

### Implemented process updates

- Verify Project-source freshness at session start.
- Request the current GitHub handover when freshness is uncertain.
- Request required source files incrementally.
- Provide complete files for substantial changes.
- Reuse consolidated regression testing.
- Refresh ChatGPT Project sources after committing handover updates.

The Project sources were replaced and their contents inspected
during this session.

After subsequent handover edits, refresh the corresponding
Project source again from the committed GitHub version.

### Cleanup after operational acceptance

The repository contains numerous historical test workflows.

Planned maintenance includes:

- Inventory and consolidate redundant workflows.
- Review overlapping tests while preserving useful coverage.
- Reuse the consolidated regression workflow.
- Review obsolete manual Watches.
- Review unused modules before deletion.
- Preserve historical state and completed-match records.
- Agree on release scope and publish only after explicit approval.

Cleanup must not disrupt the upcoming match acceptance.

## 9. Session handover

Continue from verified repository documentation.

Request current files one at a time when direct repository
access is unavailable.

Do not repeat successful authentication diagnostics without
new evidence that justifies repetition.

Provide complete replacement files for substantial changes.

At session closure, update relevant documentation and confirm
which changes have been committed.

Refresh ChatGPT Project sources after committing handover updates.

### Recommended next goal

Confirm automatic Daily execution, then observe the
14 November match from monitoring activation at 14:45.

The authentication recovery is implemented and verified against
real data. Active-match acceptance remains outstanding.

No new release has been published during this recovery session.

Prefer a completely new project conversation for the next
development or acceptance phase, using current GitHub context.

## Core principle

One agreed goal.
One coherent change.
One appropriate verification.
Then the next increment.
