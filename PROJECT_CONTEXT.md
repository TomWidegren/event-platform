
# Event Platform – Project Context

**Last updated:** 26 October 2026

**Last development checkpoint:** 26 October 2026

**Project:** Event Platform

**Last documented published release:** v1.2.0

**Current development:** Automatic Floorball Monitoring

**Deployment status:** Deployed and operational. Real-world monitoring verified during two automatic matches. Final notification delivery incident remains open.

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

Automatic Floorball Monitoring has also been observed working during real matches on 23 and 25 October 2026.

A notification delivery incident remains unresolved.

No new published release has been confirmed.

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

Independent verification of subsequent scheduled Daily executions remains to be documented.

### Live

Workflow:

`.github/workflows/live.yml`

Production entry point:

`event_platform_live.py`

Polling interval:

5 minutes.

The existing cron-job.org Live job remains enabled, as confirmed by the user on 26 October.

Live Monitoring runs continuously and selects eligible Floorball matches automatically.

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

However, the corresponding final-result notification was not received by the user.

## 5. Real-world automatic monitoring validation

### Friday 23 October 2026 – JAS

Match:

Tyresö Trollbäcken IBK – FBI Tullinge

MatchID: `1750707`

Scheduled start: 19:45.

Expected automatic activation: 19:30.

**Status: Successful automatic monitoring reported by user.**

Verified through user observation:

- Automatic match monitoring worked during the match.
- Event notifications were received.
- Lukas Widegren recorded an assist.
- The assist notification correctly highlighted Lukas with a star (⭐).

This is the first real-world verification of player-specific assist highlighting.

Previously, player-specific highlighting had only passed technical tests.

Not yet independently verified:

- Exact activation time.
- Complete event-notification history.
- Final snapshot and registry completion.
- Absence of duplicate notifications.

### Sunday 25 October 2026 – Herrar

Match:

Tyresö Trollbäcken IBK (A) – Älta IF A

MatchID: `1703577`

Scheduled start: 15:45.

Expected automatic activation: 15:30.

**Status: Monitoring and persistence successful; notification incident open.**

Verified through user observation:

- Automatic match monitoring worked.
- Event notifications were received during the match.
- The last received notification referred to score 10–4, a Ribbestad penalty and an opponent goal.
- No further Event Platform notifications were received.
- The final-result notification was not received.

Verified through the supplied `state.json`:

- Final score: 11–5.
- `match_status: 4`.
- `has_final_result: true`.
- Final snapshot contains the registered match events.
- Events after the last received notification include the goals making the score 11–4 and 11–5, followed by period end and goalkeeper exits.

Verified through `match_registry.json`:

- MatchID `1703577` has `monitoring_status: completed`.

This confirms that the final observation and completion status were persisted.

It does not establish whether the missing notifications were generated, published to ntfy or received by the notification service.

The cause remains unknown.

### Next registered match

The registry also contains:

MatchID: `1703581`

Ingarö IF (A) – Tyresö Trollbäcken IBK (A)

Scheduled start: 28 October 2026 at 20:00.

Monitoring status at the time of inspection:

`scheduled`

The match is registered for future automatic selection.

## 6. Open production incident

### Missing late-match notifications – 25 October 2026

**Priority: P0 investigation**

**Status: Open – Root cause unknown**

Affected Watch:

`floorball-match-1703577`

Observed symptoms:

- Event notifications worked earlier in the match.
- No notifications were received after the user's last message referring to 10–4.
- The remaining two goals and final result were not received as notifications.
- The final state and registry completion were successfully persisted.
- cron-job.org remained enabled when checked on 26 October.

Important distinction:

An enabled cron-job does not prove that every GitHub Actions execution succeeded.

The persisted final snapshot proves that final match data was stored, but does not prove successful notification delivery.

### Investigation plan

At the next development session:

1. Review GitHub Actions Live runs around the match ending.
2. Identify the execution that persisted the final snapshot.
3. Inspect logs and any notification delivery errors.
4. Review Git history for the affected Watch.
5. Compare notification formatting and Live execution behavior.
6. Inspect `floorball_match_selection.py` for any upper monitoring time boundary.
7. Verify how monitoring behaves after scheduled match start.
8. Review available ntfy delivery evidence.
9. Establish the root cause before changing production code.
10. Add focused regression coverage if a defect is identified.

Do not assume the problem was caused by time-window selection, notification formatting or ntfy without evidence.

### Operational safeguard

Keep the working automatic monitoring configuration unchanged until the incident is investigated.

Avoid unnecessary modifications to Live workflows, connectors and persistent state.

## 7. Verified technical results

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

Last confirmed run: 22 October 2026.

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

No new regression tests were run during the 26 October reporting session.

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

## 8. Important limitations

### Notification delivery

Notifications are sent before Git persistence.

Exactly-once delivery is not guaranteed.

The missing late-match notifications on 25 October are an additional operational incident requiring investigation.

Do not treat the known duplicate-notification risk as an explanation for this incident without evidence.

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

Goal and penalty highlighting for the configured player have not yet been independently observed in a qualifying real-world event.

### Release status

The automatic Floorball implementation is deployed but not yet fully accepted.

The last documented published release remains v1.2.0.

Confirm release status from GitHub releases or tags before publishing a new version.

## 9. Operational and maintenance priorities

### Immediate

- Investigate the missing late-match notifications.
- Preserve the working automatic monitoring configuration.
- Observe the next scheduled match on 28 October.
- Confirm the scheduled Daily Discovery workflow if not already verified.

### GitHub scheduler token

GitHub notified the user on 23 October that the personal access token used by cron-job.org would expire in approximately seven days.

The agreed plan was to renew it on Monday 26 October, after the weekend matches.

At this checkpoint, renewal has not been confirmed.

Required actions:

1. Regenerate or replace the `Event Platform Scheduler` token in GitHub.
2. Update the authorization configuration in both cron-job.org jobs.
3. Verify Daily and Live workflow triggering.
4. Do not expose the token in ChatGPT or repository files.

No Python or GitHub Actions workflow changes are expected for token renewal.

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

## 10. Documentation status

Updated on 22 October 2026:

- `docs/ARCHITECTURE.md`
- `docs/decisions.md`
- `docs/design-floorball-automation.md`
- `docs/ways-of-working.md`
- `README.md`

Updated on 26 October 2026:

- `docs/backlog.md`
- `PROJECT_CONTEXT.md`

Historical documents retained:

- `docs/design-floorball.md`
- `docs/design-v1.2.md`

Legacy roadmap information is superseded by `docs/backlog.md`.

The 26 October reporting session made no production code changes.

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
4. Review the open notification incident.
5. Request only relevant source files and logs.
6. Continue without repeating completed work.

### Recommended next development goal

**Investigate and resolve the missing late-match notifications from 25 October.**

Start with GitHub Actions logs and Git history.

Verify the monitoring time-window behavior and notification execution path.

Do not change production code before identifying the cause.

Once the incident is understood, continue with real-world acceptance, repository cleanup and release planning.

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
