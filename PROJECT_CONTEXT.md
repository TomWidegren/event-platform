
# Event Platform – Project Context

**Last updated:** 22 October 2026

**Last development checkpoint:** 22 October 2026

**Project:** Event Platform

**Last documented published release:** v1.2.0

**Current development:** Automatic Floorball Monitoring

**Deployment status:** Deployed and scheduled; real-world automatic match acceptance pending.

## 1. Purpose

Event Platform monitors changing data from external platforms, detects relevant changes, stores persistent state and sends notifications.

Golf was the first use case.

The architecture is designed to support additional event types through reusable connectors without introducing source-specific acquisition logic into the platform core.

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

The automatic Floorball implementation has not yet completed real-world acceptance or been included in a confirmed new published release.

## 3. Production execution

### Scheduling

cron-job.org triggers GitHub Actions.

The platform does not own its scheduler.

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

The next scheduled execution should be checked for operational confirmation.

### Live

Workflow:

`.github/workflows/live.yml`

Production entry point:

`event_platform_live.py`

Polling interval:

5 minutes.

The existing cron-job.org Live job is enabled.

Live Monitoring now runs continuously and selects eligible Floorball matches automatically.

The previous hard-coded `WATCH_ID` has been removed from the production workflow.

GolfBox and Tournytt remain configured Live Watches.

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

The platform monitors the configured teams regardless of whether Lukas participates in a particular match.

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
- Both upcoming acceptance matches present.
- Repeated execution detected zero changes.
- Manual Daily workflow integration successful.

Discovery owns scheduling information.

Live owns monitoring lifecycle and completion.

### Live match selection

Main components:

- `floorball_match_selection.py`
- `floorball_watch_merge.py`
- `floorball_live.py`
- `event_platform_live.py`

Eligible matches are selected from the persistent registry.

Monitoring begins 15 minutes before scheduled match start.

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

This behavior has passed automated tests.

Real-world automatic completion remains unverified.

## 5. Next real-world acceptance tests

### Friday 23 October 2026

Match:

Tyresö Trollbäcken IBK – FBI Tullinge

MatchID: `1750707`

Scheduled start: 19:45.

Expected automatic activation: 19:30.

### Sunday 25 October 2026

Match:

Tyresö Trollbäcken IBK (A) – Älta IF A

MatchID: `1703577`

Scheduled start: 15:45.

Expected automatic activation: 15:30.

All times are Europe/Stockholm.

### Acceptance criteria

For each match, verify:

- Automatic Watch selection.
- Pre-match baseline creation.
- Match-event detection.
- Notification delivery.
- Final-result notification.
- Final snapshot persistence.
- Registry status `completed`.
- Completed match excluded from later runs.
- No unexpected duplicate monitoring.
- Existing golf monitoring unaffected.

Player-specific highlighting can only be verified if a qualifying player event occurs.

## 6. Verified results

### Golf

SGF Ranking, GolfBox and Tournytt have previously been verified during real-world monitoring.

GolfBox has been validated across multiple deployments and multi-round tournaments.

### Floorball – Manual monitoring

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

Verified on 22 October:

**105 Floorball tests passed.**

Existing golf regression tests also passed.

Coverage includes:

- Discovery
- Registry handling
- Match selection
- Watch merging
- Notification formatting
- Git persistence
- Atomic completion
- Live integration

### Automatic Live execution

Verified on 22 October:

- Successful manual execution.
- Successful automatic execution through cron-job.org.
- GolfBox and Tournytt processed.
- No Floorball match selected prematurely.
- No unnecessary state persistence.
- GitHub Actions execution completed successfully.

The Live workflow was optimized after identifying excessive Playwright system-dependency installation time.

Measured execution times:

- Before optimization: 4 minutes 20 seconds.
- Optimized manual execution: approximately 37 seconds.
- Subsequent automatic execution: approximately 30 seconds.

The automatic Live schedule was re-enabled and verified.

## 7. Important limitations

### Notification delivery

Notifications are sent before Git persistence.

If notification delivery succeeds but persistence fails, the same event may be notified again.

Exactly-once delivery is not guaranteed.

### Late first observation

If the first Floorball observation already contains match activity, the current Live runner raises an error rather than silently discarding events.

Recovery remains future work.

### Git persistence

The Live implementation merges changed Watch entries against the latest repository state.

It includes optimistic concurrency protection.

Broader real-world concurrent execution remains an operational validation area.

### Match events

Corrected and deleted iBIS events require further evaluation.

### Player highlighting

Player-specific highlighting has passed technical tests but has not yet been observed during a qualifying real-world player event.

### Release status

The automatic Floorball implementation is deployed but not yet fully accepted.

Do not assume a new published release has been created.

Confirm release status from GitHub releases or tags before publishing or documenting a new version.

## 8. Current operational safeguards

Automatic Live Monitoring is active ahead of the matches on 23 and 25 October.

Until acceptance is complete:

- Avoid nonessential production code changes.
- Avoid modifying Live scheduling.
- Avoid deleting monitoring state.
- Avoid removing potentially useful workflows.
- Preserve GitHub Actions logs for failed executions.
- Investigate operational problems using actual evidence.

Documentation changes may continue without altering production behavior.

## 9. Repository cleanup

The development process created numerous standalone GitHub Actions test-workflows.

The consolidated regression workflow now covers the permanent automated test suite.

After real-world acceptance:

1. Inventory historical workflows.
2. Verify that none are externally scheduled.
3. Remove redundant standalone test-workflows.
4. Preserve Python regression tests.
5. Review unused implementation modules.
6. Remove obsolete manually configured Floorball Watches.
7. Preserve historical state and completed-match records.
8. Run consolidated regression tests.

Do not perform destructive cleanup during active match validation.

## 10. Documentation status

Updated on 22 October 2026:

- `docs/ARCHITECTURE.md`
- `docs/decisions.md`
- `docs/backlog.md`
- `docs/design-floorball-automation.md`
- `docs/ways-of-working.md`
- `README.md`
- `PROJECT_CONTEXT.md`

Historical documents retained:

- `docs/design-floorball.md`
- `docs/design-v1.2.md`

Legacy roadmap information is superseded by `docs/backlog.md`.

## 11. Development process

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

## 12. Starting the next session

The user should only need to say:

"Nu fortsätter vi med Event Platform."

The assistant should:

1. Read this file.
2. Read the project documentation.
3. Identify the current production and development status.
4. Review the latest operational verification.
5. Request only relevant source files if necessary.
6. Continue without repeating completed work.

### Recommended next goal

**Complete real-world acceptance of automatic Floorball Monitoring.**

Start by reviewing the automatic JAS match monitoring on 23 October.

Verify:

- Match activation.
- Baseline.
- Notifications.
- Final-result persistence.
- Registry completion.

Then review the men's match on 25 October.

After acceptance, proceed with repository cleanup and release planning.

## 13. Ending a session

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
