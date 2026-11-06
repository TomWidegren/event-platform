
# Event Platform – Project Context

**Last updated:** 6 November 2026

**Last development checkpoint:** 6 November 2026

**Project:** Event Platform

**Last documented published release:** v1.2.0

**Current development:** Automatic Floorball Monitoring

**Deployment status:** Automatic Live Monitoring operational. Daily Floorball Discovery experiencing recurring iBIS HTTP 503 failures. Real-world acceptance and reliability verification ongoing.

## 1. Purpose

Event Platform monitors changing data from external platforms, detects relevant changes, stores persistent state and sends notifications.

Golf was the first use case.

The architecture supports additional event types through reusable connectors without introducing source-specific acquisition logic into the platform core.

The GitHub repository is the authoritative source of truth.

ChatGPT conversations and Project files must not be assumed to reflect the latest GitHub contents.

## 2. Current capabilities

### Published release

The last documented published release is v1.2.0.

It established the Unified Connector Interface architecture.

Published connectors:

- `sgf_ranking`
- `golfbox_leaderboard`
- `tournytt_api`

All connectors expose:

`fetch_snapshot(watch)`

### Implemented after v1.2.0

- Swedish Floorball / iBIS connector
- Floorball notification formatting
- Automatic Floorball Discovery
- Persistent match registry
- Automatic match selection
- Runtime Watch generation
- Multiple Live Watches
- Git persistence with conflict protection
- Automatic match-completion logic
- Consolidated regression testing

These capabilities have been implemented and technically verified.

Automatic Floorball Monitoring has also been observed working during real matches.

The current implementation is deployed but has not yet completed all operational acceptance criteria.

No new published release has been confirmed.

## 3. Production execution

### Scheduling

cron-job.org triggers GitHub Actions.

The platform does not own its scheduler.

Two production schedules are used:

- Event Platform – Daily
- Event Platform – Live

### Daily

Workflow:

`.github/workflows/daily.yml`

Normal schedule:

08:00 Europe/Stockholm.

Responsibilities:

1. SGF Ranking monitoring.
2. Automatic Floorball Discovery.

The existing Daily schedule is reused.

Daily Discovery was successfully tested manually on 22 October.

On 5 and 6 November, the Daily workflow failed during Floorball Discovery.

The golf monitoring portion completed successfully in the inspected runs.

The overall workflow was marked failed because Discovery encountered an iBIS HTTP 503 error.

A manual retry on 6 November reproduced the error.

**Current status: Discovery operational incident open.**

### Live

Workflow:

`.github/workflows/live.yml`

Production entry point:

`event_platform_live.py`

Polling interval:

5 minutes.

The existing cron-job.org Live schedule is enabled.

Live Monitoring runs continuously and selects eligible Floorball matches automatically.

The previous hard-coded `WATCH_ID` has been removed from the production workflow.

GolfBox and Tournytt remain configured Live Watches.

Recent Live workflow executions were reported successful on 6 November.

Successful execution without an eligible Floorball match does not independently verify iBIS availability.

### Workflow concurrency

Participating Daily and Live workflows use:

`event-platform-state`

With:

`cancel-in-progress: false`

This reduces overlapping executions that could update shared repository state.

Git persistence also includes conflict protection and retries.

## 4. Automatic Floorball Monitoring

### Configured teams

Season: 2026/27.

| Team | TeamID | CompetitionID |
|---|---|---|
| Tyresö Trollbäcken IBK – JAS | 20872 | 45004 |
| Tyresö Trollbäcken IBK – Herrar | 4194 | 44356 |

Highlighted player:

Lukas Widegren – PlayerID `585280`.

The platform monitors configured teams regardless of whether Lukas participates in a particular match.

### Discovery

Main components:

- `floorball_discovery.py`
- `floorball_discovery_changes.py`
- `floorball_registry.py`
- `floorball_registry_merge.py`
- `floorball_git_persistence.py`

Discovery retrieves competition match lists from iBIS and identifies relevant matches.

Persistent registry:

`match_registry.json`

Verified on 22 October:

- 31 relevant matches discovered.
- Registry persisted in GitHub.
- Both initial acceptance matches present.
- Repeated execution detected zero changes.
- Manual Daily workflow integration successful.

Discovery owns scheduling information.

Live owns monitoring lifecycle and completion.

### Current Discovery limitation

The recurring iBIS HTTP 503 error prevents successful Discovery execution.

Existing registered matches remain available for Live selection.

However, new matches and schedule changes cannot be reliably discovered while the issue persists.

The cause of the HTTP 503 response remains unknown.

### Live match selection

Main components:

- `floorball_match_selection.py`
- `floorball_watch_merge.py`
- `floorball_live.py`
- `event_platform_live.py`

Eligible matches are selected from the persistent registry.

Monitoring is designed to begin 15 minutes before scheduled match start.

Automatic Watch IDs use:

`floorball-match-{match_id}`

Manually configured Floorball Watches are excluded from automatic Live execution.

Existing GolfBox and Tournytt Watches are preserved.

### Match completion

The Live process is designed to:

1. Detect the final result.
2. Send the final-result notification.
3. Persist the final snapshot.
4. Mark the match `completed`.
5. Exclude completed matches from subsequent monitoring.

Final snapshot and completion status are committed together in Git.

Automatic completion and final-state persistence were confirmed for the match on 25 October.

The corresponding final-result notification was not received by the user.

## 5. Real-world automatic monitoring validation

### 23 October 2026 – JAS

Match:

Tyresö Trollbäcken IBK – FBI Tullinge

MatchID: `1750707`

**Status: Successful automatic monitoring reported by user.**

Verified:

- Automatic match monitoring worked.
- Event notifications were received.
- Lukas Widegren recorded an assist.
- The assist notification correctly highlighted Lukas with ⭐.

This was the first real-world verification of player-specific assist highlighting.

The registry inspected on 6 November confirms:

`monitoring_status: completed`

Not yet independently verified:

- Exact activation time.
- Complete event-notification history.
- Final snapshot details.
- Absence of duplicate notifications.

### 25 October 2026 – Herrar

Match:

Tyresö Trollbäcken IBK (A) – Älta IF A

MatchID: `1703577`

**Status: Monitoring and persistence successful; notification incident open.**

Verified through user observation:

- Automatic monitoring worked.
- Event notifications were received.
- The last received notification referred to score 10–4, a Ribbestad penalty and an opponent goal.
- No further Event Platform notifications were received.
- No final-result notification was received.

Verified through `state.json`:

- Final score: 11–5.
- `match_status: 4`.
- `has_final_result: true`.
- Final snapshot contains the remaining match events.

Verified through `match_registry.json`:

`monitoring_status: completed`

The final observation and completion status were persisted successfully.

The cause of the missing notifications remains unknown.

### 28 October 2026 – Herrar

Match:

Ingarö IF (A) – Tyresö Trollbäcken IBK (A)

MatchID: `1703581`

The user reported successful automatic monitoring.

The registry inspected on 6 November confirms:

`monitoring_status: completed`

Complete notification history and final snapshot have not been independently inspected.

### 30 October 2026 – JAS

Match:

Onyx IBS – Tyresö Trollbäcken IBK

MatchID: `1750712`

The registry inspected on 6 November confirms:

`monitoring_status: completed`

Complete notification history and final snapshot have not been independently verified.

### 6 November 2026 – JAS

Match:

Tyresö Trollbäcken IBK – IFK Gnesta/FBC Nyköping

MatchID: `1750719`

Scheduled start:

19:45 Europe/Stockholm.

Expected automatic activation:

19:30.

Verified in `match_registry.json` on 6 November:

- Correct MatchID.
- Correct scheduled start.
- `monitoring_status: scheduled`.
- `cancelled: false`.
- `postponed: false`.

The match is already registered despite the current Discovery failures.

Live Monitoring should select the match automatically, provided the schedule has not changed and the required iBIS acquisition remains available.

**Real-world monitoring for this match remains pending verification.**

## 6. Open production incidents

### Incident 1 – Recurring iBIS Discovery HTTP 503

**Priority: P0**

**Status: Open – Root cause unknown**

First reported:

6 November 2026.

Observed failures:

- Scheduled Daily executions on 5 and 6 November.
- Manual Daily execution on 6 November.

Error:

`503 Server Error: Service Unavailable`

Affected operation:

Floorball Discovery authentication through the iBIS `startkit` endpoint.

Verified:

- GitHub Actions started.
- Python dependencies installed.
- Daily golf monitoring completed.
- Golf state persistence completed.
- Floorball Discovery failed during iBIS authentication.
- The overall Daily workflow was marked failed.
- Manual retry reproduced the same failure.

Recent Live workflow executions were successful.

However, this does not prove that the iBIS connector works during an active match.

Investigation:

1. Check iBIS startkit availability.
2. Compare Discovery and Live authentication behavior.
3. Inspect API responses and relevant headers.
4. Determine whether the issue is temporary or caused by API changes.
5. Evaluate bounded retries and backoff.
6. Preserve existing registry state during failures.
7. Improve operational diagnostics if needed.
8. Add focused regression tests for confirmed defects.
9. Verify successful scheduled Discovery execution.

Do not change production code before reviewing evidence.

### Incident 2 – Missing late-match notifications

**Priority: P0 investigation**

**Status: Open – Root cause unknown**

Affected match:

25 October 2026.

MatchID:

`1703577`

Observed:

- Event notifications worked earlier in the match.
- Notifications stopped after the user's last received message referring to 10–4.
- Later goals and the final-result notification were not received.
- Final state and registry completion were persisted.

Investigation:

1. Review GitHub Actions Live runs around match completion.
2. Identify the execution that persisted the final snapshot.
3. Inspect notification-related logs and errors.
4. Review Git history for the affected Watch.
5. Inspect `notification_formatters.py`.
6. Inspect `event_platform_live.py`.
7. Inspect `floorball_match_selection.py` for any upper time boundary.
8. Review available ntfy delivery evidence.
9. Establish root cause before modifying production code.
10. Add regression coverage for any confirmed defect.

Do not assume that notification delivery, formatting or match-selection timing caused the issue without evidence.

## 7. Scheduling authentication maintenance

### GitHub token renewal – 29 October 2026

**Status: Completed and verified**

The GitHub personal access token used by cron-job.org was approaching expiration.

cron-job.org disabled jobs after repeated failed executions.

The token was renewed.

Both production jobs were updated:

- Event Platform – Daily
- Event Platform – Live

The HTTP Authorization header was corrected to use:

`Bearer <token>`

Both jobs returned successful GitHub API responses.

Both GitHub Actions workflows were reported successful.

No Python or workflow code changes were required.

**New token expiration: 28 November 2026**

Renewal must be completed before this date.

Never store token values in GitHub documentation or ChatGPT.

## 8. Verified technical results

### Golf

SGF Ranking, GolfBox and Tournytt have previously been verified during real-world monitoring.

GolfBox has been validated across multiple deployments and multi-round tournaments.

### Floorball – Earlier manual monitoring

Two successful real-world validations:

**15 October 2026**

Huddinge IBS – Tyresö Trollbäcken IBK.

MatchID: `1750693`.

Verified goals, penalties, period events, final results and ntfy delivery.

**17 October 2026**

IFK Haninge (B) – Tyresö Trollbäcken IBK (A).

MatchID: `1703572`.

Verified five-minute polling, notifications, final result 5–4 and final state persistence.

These validations used the earlier manually selected Watch approach.

### Automated regression tests

Permanent workflow:

`.github/workflows/test-regression.yml`

Last confirmed run:

22 October 2026.

**105 Floorball tests passed.**

Existing golf regression tests also passed.

Coverage includes:

- Discovery.
- Registry handling.
- Match selection.
- Watch merging.
- Notification formatting.
- Git persistence.
- Atomic completion.
- Live integration.

### Automatic Live execution

Verified on 22 October:

- Successful manual execution.
- Successful automatic execution through cron-job.org.
- GolfBox and Tournytt processed.
- No Floorball match selected prematurely.
- No unnecessary state persistence.
- GitHub Actions execution completed successfully.

Measured execution times:

- Before optimization: 4 minutes 20 seconds.
- Optimized manual execution: approximately 37 seconds.
- Subsequent automatic execution: approximately 30 seconds.

## 9. Important limitations

### External API availability

The iBIS startkit endpoint returned repeated HTTP 503 errors during Discovery.

The root cause remains unknown.

The platform currently depends on successful external API acquisition.

### Notification delivery

Notifications are sent before Git persistence.

Exactly-once delivery is not guaranteed.

The missing late-match notifications from 25 October are a separate unresolved incident.

### Late first observation

If the first Floorball observation already contains match activity, the Live runner raises an error rather than silently discarding events.

Recovery remains future work.

### Git persistence

The Live implementation merges changed Watch entries against the latest repository state.

It includes optimistic concurrency protection.

Broader real-world concurrent execution remains an operational validation area.

### Match events

Corrected and deleted iBIS events require further evaluation.

### Player highlighting

Assist highlighting was verified in real-world operation on 23 October.

Goal and penalty highlighting have not yet been independently observed during qualifying player events.

### Release status

The automatic Floorball implementation is deployed but not yet fully accepted.

The last documented published release remains v1.2.0.

Confirm release status from GitHub releases or tags before publishing a new version.

## 10. Operational and maintenance priorities

### Immediate

1. Protect Live Monitoring for the JAS match on 6 November.
2. Investigate the recurring iBIS Discovery HTTP 503 failure.
3. Investigate the missing late-match notifications from 25 October.
4. Confirm successful scheduled Daily Discovery after recovery.

### Token maintenance

The renewed GitHub token expires on 28 November 2026.

Renew it before expiration and verify both cron-job.org workflows.

### Repository cleanup

After operational acceptance and incident investigation:

1. Inventory historical workflows.
2. Verify that none are externally scheduled.
3. Remove redundant standalone test-workflows.
4. Preserve Python regression tests.
5. Review unused implementation modules.
6. Remove obsolete manually configured Floorball Watches.
7. Preserve historical state and completed-match records.
8. Run consolidated regression tests.

Do not perform destructive cleanup during active match validation.

## 11. Documentation status

Updated on 22 October 2026:

- `docs/ARCHITECTURE.md`
- `docs/decisions.md`
- `docs/design-floorball-automation.md`
- `docs/ways-of-working.md`
- `README.md`

Updated on 26 October 2026:

- `docs/backlog.md`
- `PROJECT_CONTEXT.md`

Documentation update prepared on 6 November 2026:

- `docs/backlog.md`
- `PROJECT_CONTEXT.md`

The 6 November session has not introduced production code changes.

Historical documents retained:

- `docs/design-floorball.md`
- `docs/design-v1.2.md`

Legacy roadmap information is superseded by `docs/backlog.md`.

## 12. Development process

Follow:

`docs/ways-of-working.md`

Key principles:

- One agreed goal.
- Inspect existing files.
- Deliver coherent implementation increments.
- Provide complete copyable files for substantial changes.
- Avoid unnecessary approval rounds.
- Prefer consolidated regression testing.
- Verify according to risk.
- Protect working Live Monitoring.
- Document verified facts separately from plans.

Do not assume ChatGPT has direct access to the latest GitHub repository.

Request current files when necessary.

## 13. Starting the next session

The user should only need to say:

"Nu fortsätter vi med Event Platform."

The assistant should:

1. Read this file.
2. Read the project documentation.
3. Identify the current production and development status.
4. Review open production incidents.
5. Request only relevant source files and logs.
6. Continue without repeating completed work.

### Recommended next development goal

**Investigate and resolve the recurring iBIS Discovery HTTP 503 failure.**

Start by reviewing the startkit authentication behavior and comparing it with the Live connector.

Do not change production code before establishing the likely cause.

After that:

1. Investigate missing late-match notifications.
2. Complete operational acceptance.
3. Clean up redundant repository files.
4. Review release readiness.

## 14. Ending a session

Before ending:

1. Summarize completed work.
2. Distinguish verified and unverified functionality.
3. Update relevant repository documentation.
4. Confirm documentation commits.
5. Record outstanding issues.
6. Identify the next goal.

The repository must contain sufficient context to resume development without relying on earlier conversations.

## Context rule

GitHub is authoritative.

Conversation memory is not a substitute for current repository documentation.

When the latest repository state is unavailable, request the necessary files rather than assuming previous attachments are synchronized.
