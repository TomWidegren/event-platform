
# Event Platform – Floorball Automation Design

Status: Draft – Architecture direction agreed, implementation details under review

Created: 21 October 2026

Last updated: 21 October 2026

Current production release: v1.3.0

## 1. Purpose

Automatically discover and monitor floorball matches for selected teams and competitions without manually configuring individual matches or activating Live monitoring for each event.

The initial use case is monitoring the two Tyresö Trollbäcken IBK teams in which Lukas Widegren participates.

The solution must reuse the existing Event Platform architecture and the verified iBIS connector wherever possible.

The design separates daily match discovery from five-minute Live monitoring.

The overall design direction has been agreed. Remaining technical questions must be resolved and verified before unattended automatic monitoring is enabled.

## 2. Scope

### Included

- Automatic discovery of matches for configured teams and competitions.
- Daily identification of new matches and schedule changes.
- Persistent storage of discovered matches.
- Automatic selection of matches requiring Live monitoring.
- Automatic monitoring starting 15 minutes before scheduled match time.
- Automatic completion after the final result is saved.
- Multiple matches and teams.
- Existing floorball notifications and player-specific highlighting.
- Safe state persistence.
- Protection against overlapping Live executions.

### Excluded from initial implementation

- Automatic discovery of which teams a player belongs to.
- Monitoring competitions that have not been configured.
- User interfaces for managing teams.
- Configurable notification preferences.
- Replacing ntfy.
- Replacing GitHub-based persistence.
- Changes to existing GolfBox, SGF Ranking or Tournytt connectors.

## 3. Initial configuration

Season: 2026/27

Highlighted player:

- Lukas Widegren
- PlayerID: 585280

Configured teams:

| Team | TeamID | CompetitionID |
|---|---|---|
| Tyresö Trollbäcken IBK – JAS | 20872 | 45004 |
| Tyresö Trollbäcken IBK – Herrar | 4194 | 44356 |

The configuration identifies teams and competitions, not individual matches.

The platform monitors all relevant matches for these teams regardless of whether Lukas participates.

### Initial acceptance-test matches

| Date | Team | MatchID | Start |
|---|---|---|---|
| 23 October 2026 | JAS | 1750707 | 19:45 |
| 25 October 2026 | Herrar | 1703577 | 15:45 |

These matches were identified and verified through the iBIS website and API responses on 21 October 2026.

### Discovery verification – 21 October 2026

A read-only GitHub Actions workflow was created:

`.github/workflows/test-floorball-discovery.yml`

The workflow successfully authenticated with iBIS and retrieved competition match lists.

Verified results:

| | JAS | Herrar |
|---|---|---|
| CompetitionID | 45004 | 44356 |
| TeamID | 20872 | 4194 |
| Competition matches | 110 | 90 |
| Team matches | 20 | 18 |
| Upcoming matches | 17 | 14 |
| Expected MatchID | 1750707 | 1703577 |
| Result | PASS | PASS |

The test confirmed that both upcoming matches can be identified without supplying their MatchIDs to the API request.

The workflow did not modify production configuration or state and did not send notifications.

### Registry verification – 21 October 2026

The pure registry function was implemented in:

`floorball_registry.py`

Automated tests:

`tests/test_floorball_registry.py`

Workflow:

`.github/workflows/test-floorball-registry.yml`

All eight registry tests passed.

Verified behavior:

- New relevant matches are added.
- Existing matches are preserved.
- Changed match start times are updated.
- Completed matches are not reactivated.
- Temporarily missing matches are preserved.
- Unrelated teams are excluded.
- Invalid input does not mutate the original registry.
- Registry updates do not mutate their input objects.

An additional integration workflow was introduced:

`.github/workflows/test-floorball-discovery-registry.yml`

It successfully retrieved real iBIS match lists and passed the discovered matches through `update_registry()`.

Verified:

- JAS: 17 upcoming matches.
- Herrar: 14 upcoming matches.
- Total: 31 registered matches.
- Both expected acceptance-test matches were present.
- No persistent files were modified.
- No notifications were sent.

These tests verify in-memory registry behavior, not persistent GitHub storage or automatic Live monitoring.

## 4. Architecture

The solution introduces two separate processes:

1. Daily Match Discovery.
2. Live Match Monitoring.

Both reuse the existing Event Platform execution environment.

### Daily Match Discovery

Runs once per day.

Responsibilities:

1. Load configured teams and competitions.
2. Authenticate with iBIS.
3. Retrieve competition match lists.
4. Filter matches using HomeTeamID and AwayTeamID.
5. Identify new matches.
6. Detect schedule changes.
7. Update the persistent match registry.
8. Preserve existing match identities and monitoring state.

Verified iBIS endpoint:

GET /competitions/{competition_id}/matches

The endpoint returns the competition's match list.

The initial investigation confirmed that relevant matches can be identified using TeamID and MatchID.

Daily Discovery must not directly modify monitoring snapshots in `state.json`.

### Live Match Monitoring

Triggered by cron-job.org every five minutes.

Responsibilities:

1. Load the persistent match registry.
2. Identify matches within the active monitoring window.
3. Exclude completed matches.
4. Create runtime Watch objects for relevant matches.
5. Invoke the existing `ibis_floorball` connector.
6. Compare normalized snapshots with persisted state.
7. Generate notifications for relevant changes.
8. Persist updated match state.
9. Stop monitoring matches after the final result has been saved.

The Live process does not retrieve full competition schedules during normal execution.

When no match is eligible, the execution should finish quickly without sending notifications.

## 5. Persistent match registry

### Design decision

A separate persistent match registry will be introduced.

Proposed file:

`match_registry.json`

The registry will contain:

- Upcoming matches.
- Matches currently eligible for monitoring.
- Matches that Event Platform has actually monitored and completed.

It will not retain the entire historical competition schedule.

This keeps the registry focused on operationally relevant matches while preserving the monitoring history required to prevent accidental reactivation.

### Responsibility separation

| Component | Responsibility |
|---|---|
| `config.yml` | Selected teams, competitions and highlighted players |
| `match_registry.json` | Discovered matches and scheduling information |
| `state.json` | Latest normalized snapshots used for change detection |

Discovery owns match discovery and scheduling information.

Live Monitoring owns match observation and notification processing.

The two processes must not overwrite each other's updates.

### Proposed schema

Schema version: 1

Example:

    {
      "schema_version": 1,
      "matches": {
        "1750707": {
          "match_id": 1750707,
          "competition_id": 45004,
          "team_id": 20872,
          "highlight_player_id": 585280,
          "home_team": "Tyresö Trollbäcken IBK",
          "away_team": "FBI Tullinge",
          "scheduled_start": "2026-10-23T19:45:00",
          "source_status": 1,
          "cancelled": false,
          "postponed": false,
          "monitoring_status": "scheduled"
        },
        "1703577": {
          "match_id": 1703577,
          "competition_id": 44356,
          "team_id": 4194,
          "highlight_player_id": 585280,
          "home_team": "Tyresö Trollbäcken IBK (A)",
          "away_team": "Älta IF A",
          "scheduled_start": "2026-10-25T15:45:00",
          "source_status": 1,
          "cancelled": false,
          "postponed": false,
          "monitoring_status": "scheduled"
        }
      }
    }

This schema is a design proposal and has not yet been persisted in production.

The exact meaning of iBIS status values and cancellation fields must be verified before those fields control monitoring.

### Stable identity

Each match uses its MatchID as the registry key.

Runtime Watch IDs use:

`floorball-match-{match_id}`

Examples:

- `floorball-match-1750707`
- `floorball-match-1703577`

The Watch ID must remain stable across executions.

Existing Watch IDs and monitoring state must not be changed.

If a match is relevant to multiple configured teams, the design must avoid duplicate monitoring and notifications.

## 6. Registry update rules

Daily Discovery compares newly retrieved match data with the existing registry.

### New match

When a new relevant upcoming match is discovered:

- Create a registry entry.
- Preserve its MatchID.
- Store the selected team and competition identifiers.
- Store its scheduled start and available match information.
- Set the initial monitoring status to `scheduled`.

### Existing match

When a match already exists:

- Update source-derived scheduling information when it changes.
- Preserve the stable MatchID.
- Preserve monitoring history.
- Do not reset completed monitoring state.

### Rescheduled match

When the source reports a new start time:

- Update the scheduled start.
- Recalculate future monitoring eligibility.
- Preserve existing monitoring state.

If iBIS assigns a new MatchID, the relationship between the old and new match requires further investigation.

### Cancelled or postponed match

Preserve the match entry.

Update its source-derived status when verified.

Do not activate normal Live monitoring for a confirmed cancelled match.

Postponed matches should remain eligible for future scheduling updates.

Exact iBIS status mappings require verification.

### Match temporarily missing from the API

Do not immediately delete the registry entry.

Preserve existing information and flag the discrepancy for investigation.

### Completed match

A match already completed by Event Platform must not be returned to `scheduled` by a later Discovery execution.

Its history remains in the registry.

### Discovery failure

If API acquisition or processing fails:

- Preserve the existing registry.
- Do not remove previously discovered matches.
- Report the failure.
- Allow a subsequent execution to retry.

The registry must not be partially replaced with incomplete discovery results.

## 7. Match lifecycle

### Monitoring statuses

The proposed persistent monitoring statuses are:

- `scheduled`
- `completed`

The following states are primarily calculated at runtime:

- `eligible`
- `monitoring`

This avoids unnecessary state writes and GitHub commits during ordinary polling.

### Scheduled

The match has been discovered and stored.

It is not yet eligible for Live monitoring.

### Eligible

The match becomes eligible 15 minutes before its scheduled start.

Eligibility is calculated using the current time and scheduled match start.

### Monitoring

An eligible match is selected by the Live process.

The existing connector retrieves match data and the Event Platform core performs change detection.

Monitoring continues while the match has not been safely completed.

### Completed

A match may be marked completed only after:

1. The final match snapshot has been processed.
2. The final-result notification has been handled.
3. The final snapshot has been successfully persisted.

The completion marker must not be committed before the required monitoring state is safely stored.

A failure must leave the match eligible for retry.

### Avoiding unnecessary persistent states

The registry should not be updated on every five-minute polling cycle merely to record that monitoring is active.

Only meaningful lifecycle changes should require persistence.

## 8. Match activation

Monitoring eligibility begins 15 minutes before the scheduled start.

Example:

Scheduled start: 19:45

Eligibility begins: 19:30

The first Live execution at or after 19:30 selects the match.

### Pre-match baseline

A baseline must exist before the first meaningful match event.

The existing Floorball baseline principles must be preserved.

If the match has not started and no goals or registered events exist, a baseline may be established without sending a notification.

### Late activation

If the first successful observation occurs after the match has started, the system must not silently discard registered match events.

The exact late-activation behavior must be defined and tested before automatic Live monitoring is enabled.

### Delayed matches

A match must not be permanently skipped merely because its scheduled start time has passed.

A suitable eligibility window or source-status rule must be defined.

## 9. Match completion

The existing iBIS connector returns:

`has_final_result`

When this becomes true:

1. The final snapshot is processed.
2. The final-result notification is generated.
3. The final snapshot is persisted successfully.
4. The registry is updated to `completed`.
5. Future Live executions exclude the match.

If execution or persistence fails, the match remains eligible for retry.

The interaction between notification delivery, snapshot persistence and registry completion must be designed carefully to avoid missed or duplicate notifications.

## 10. Multiple matches

Each discovered match uses an independent runtime Watch.

Example:

- `floorball-match-1750707`
- `floorball-match-1703577`

The Live process must support multiple eligible matches during one execution.

The existing `ibis_floorball` connector is called separately for each match.

The generic Event Platform core must remain independent of floorball-specific scheduling logic.

Runtime Watch generation should occur outside the generic connector interface.

The exact mechanism for supplying runtime Watches to the execution engine remains an implementation design question.

## 11. State persistence and concurrency

### Agreed design direction

Event Platform will continue using GitHub-based JSON persistence for the initial automated Floorball implementation.

The design uses:

- `match_registry.json` for match discovery, scheduling and monitoring lifecycle.
- `state.json` for normalized monitoring snapshots.
- A shared GitHub Actions concurrency group for the workflows that update these files.
- Safe merging of changed entries before committing.
- Conflict detection and controlled retries.

The goal is to preserve independent changes made by Daily Discovery, Live Monitoring and existing Daily monitoring.

These mechanisms have not yet been implemented or verified.

### 11.1 Data ownership

Each process owns a defined subset of persistent information.

| Process | Owned information |
|---|---|
| Daily Discovery | Match identity, scheduling, teams, competitions and source status |
| Live Monitoring | Monitoring lifecycle and completion status |
| Event Platform core | Normalized snapshots and change detection state |

Daily Discovery may update source-derived fields in `match_registry.json`.

Live Monitoring may update monitoring lifecycle fields in `match_registry.json` and the relevant Watch entries in `state.json`.

Existing Daily monitoring continues updating its own Watch entries in `state.json`.

A process must not overwrite fields owned by another process using stale information.

In particular, Discovery must never reset a completed match to `scheduled`.

### 11.2 Shared concurrency group

Daily Discovery and Live Monitoring will use the same GitHub Actions concurrency group.

Proposed configuration:

    concurrency:
      group: event-platform-state
      cancel-in-progress: false

The concurrency group should be applied consistently to workflows that may modify the shared persistent files.

The existing SGF Ranking Daily workflow must also be considered because it modifies `state.json`.

A shared concurrency group prevents overlapping execution of workflows using that group within the same repository.

However, GitHub Actions concurrency does not guarantee that every queued execution will run. Pending runs may be replaced by newer pending runs.

Therefore, concurrency is a protection against simultaneous writes, not a guarantee of processing every scheduled run.

The design must tolerate skipped or delayed polling executions.

### 11.3 Safe registry updates

The registry update mechanism must not replace the latest repository file with an entire stale copy.

Proposed sequence:

1. Determine the changes produced by the current execution.
2. Retrieve the latest committed registry.
3. Reapply only the changes owned by the current process.
4. Preserve unrelated match entries.
5. Preserve fields owned by other processes.
6. Validate the resulting registry.
7. Commit and push the merged result.
8. If the push fails because the repository changed, retrieve the latest version and repeat the merge.

A retry must reapply the intended changes to the newest registry rather than restoring an old complete file.

### 11.4 Same-match conflicts

Merging changes by MatchID is not sufficient when two processes update different fields of the same match.

Example:

- Discovery changes `scheduled_start`.
- Live changes `monitoring_status` to `completed`.

Both updates must survive.

The merge mechanism must therefore respect field ownership, not merely replace entire match entries.

The `completed` monitoring status must be preserved when applying Discovery updates.

A stale Live update must not silently overwrite a newer schedule change.

### 11.5 State persistence

The same preservation principle applies to `state.json`.

Only the Watch entries modified by the current execution should be merged into the latest committed state.

Unrelated Watch entries must be preserved.

This protects interactions between:

- SGF Ranking Daily monitoring.
- GolfBox or Tournytt Live monitoring.
- Floorball Live monitoring.

A merge must not overwrite a newer snapshot for the same Watch with an older snapshot.

If the system cannot safely determine which snapshot is newer, it should report a conflict rather than silently overwrite data.

### 11.6 Match completion and snapshot persistence

A match must not be marked `completed` unless its final monitoring snapshot has been successfully persisted.

The proposed persistence operation should coordinate changes to:

- The relevant Watch entry in `state.json`.
- The relevant match entry in `match_registry.json`.

Where possible, both file updates should be included in the same Git commit.

This reduces the risk of storing a completed registry status without the corresponding final snapshot.

Notification delivery cannot be made atomic with a Git commit.

The implementation must therefore explicitly define retry behavior when notification delivery succeeds but persistence subsequently fails.

Exactly-once notification delivery is not guaranteed by the current architecture.

### 11.7 Failure handling

If a registry commit fails:

- Preserve the intended changes.
- Retrieve the latest repository version.
- Reapply the changes safely.
- Retry within a defined limit.
- Report failure if the changes cannot be persisted.

If the final match snapshot cannot be persisted:

- Do not mark the match completed.
- Preserve the ability to retry.
- Do not silently discard monitoring changes.

If a notification has already been delivered but persistence fails, duplicate notification risk must be handled explicitly.

### 11.8 Existing production workflow compatibility

The current Live workflow restores an entire saved `state.json` after synchronizing with `main`.

This behavior must be replaced before unattended multi-match monitoring is enabled.

The existing Daily workflow also commits state directly and must be included in the concurrency and conflict-handling design.

Changes to production workflows should be introduced incrementally and regression-tested.

The verified v1.3.0 monitoring behavior must remain available until the replacement persistence mechanism is proven safe.

## 12. Scheduling

### Daily Discovery

Frequency: once per day.

The discovery schedule is separate from existing SGF Ranking monitoring.

A dedicated GitHub Actions workflow is preferred.

### Live Monitoring

Frequency: every five minutes.

cron-job.org continues triggering the Live workflow.

When no match is eligible:

- No match connector is called.
- No notification is sent.
- No monitoring state changes are required.
- The execution exits quickly.

The Live workflow should avoid unnecessary Playwright and Chromium installation when only HTTP-based Floorball monitoring is required.

Any optimization must preserve support for existing GolfBox and Tournytt monitoring.

### Schedule changes

Daily Discovery is the primary mechanism for identifying schedule changes.

A separate mechanism may be needed to detect late changes on match days.

The exact approach remains open.

## 13. Notification behavior

Existing Floorball notification formatting remains unchanged for the initial implementation.

Supported notifications include:

- Goals.
- Empty-net goals.
- Assists associated with goals.
- Penalties.
- Period starts and ends.
- Other registered match events.
- Final results.

Lukas-specific highlighting remains based on PlayerID 585280.

The automation must not introduce duplicate initial notifications or suppress events that occurred before the first successful Live execution.

The existing notification formatter should be reused.

## 14. Failure handling

### Discovery failure

Preserve the existing registry and retry later.

### Live acquisition failure

If an individual match cannot be retrieved:

- Preserve its previous state.
- Do not mark the match completed.
- Retry during a subsequent Live execution.
- Avoid preventing other eligible matches from being monitored.

### State persistence failure

Do not treat the match as completed.

Preserve the ability to retry.

### Notification delivery failure

Notification delivery and state persistence must be coordinated.

The design must explicitly address the possibility of a notification being delivered before a later persistence failure.

Exactly-once notification delivery is not guaranteed by the current implementation.

## 15. Validation plan

### Phase A – Discovery

**Status: Completed – 21 October 2026**

Verified:

- Successful iBIS authentication.
- Retrieval of both competition match lists.
- Filtering by TeamID.
- Identification of the expected upcoming matches.
- Execution through GitHub Actions.
- No production state changes or notifications.

### Phase B – Registry logic

**Status: Completed for in-memory behavior – 21 October 2026**

Verified:

- New matches are added.
- Existing matches are preserved.
- Changed start times are updated.
- Completed matches are not reactivated.
- Temporarily missing matches are preserved.
- Discovery failures do not mutate the existing registry.
- Only relevant team matches are included in the tested input.

The registry has also been verified with real iBIS discovery results.

Persistent storage and concurrency remain unverified.

### Phase C – Monitoring selection

**Status: Not started**

Verify:

- Eligibility begins 15 minutes before scheduled start.
- Unrelated matches are excluded.
- Completed matches are excluded.
- Multiple eligible matches can be selected.
- Delayed matches are not permanently skipped.
- Late activation does not silently discard registered events.

Use simulated times and mocked data where practical.

### Phase D – State persistence

**Status: Design agreed – Implementation and verification pending**

Verify:

1. Discovery can add new matches without removing existing entries.
2. Discovery can update a scheduled start without changing monitoring status.
3. Live can mark a match completed without overwriting its scheduling information.
4. A schedule update and completion update for the same match are both preserved.
5. Changes to different matches are merged without loss.
6. Changes to unrelated `state.json` Watch entries are preserved.
7. A stale snapshot cannot silently overwrite a newer snapshot for the same Watch.
8. Git push conflicts trigger a controlled refresh and retry.
9. A failed persistence operation does not mark a match completed.
10. Shared concurrency controls prevent overlapping execution.
11. Delayed or skipped queued executions do not permanently lose matches.
12. Final snapshot and completed registry status are persisted consistently.

The initial tests should use temporary files and simulated concurrent updates.

No production GitHub writes should occur during the isolated tests.

### Phase E – Real-world acceptance

Friday 23 October 2026:

JAS – MatchID 1750707.

Sunday 25 October 2026:

Herrar – MatchID 1703577.

Acceptance criteria:

- Match discovered automatically.
- Monitoring begins without manual MatchID configuration.
- Existing Floorball notifications work.
- Final result is received.
- Final state is saved.
- Completed match is no longer monitored.
- No existing Golf monitoring is disrupted.

Full automatic monitoring must only be enabled after the required safety tests have passed.

Otherwise, use the verified manual monitoring approach.

## 16. Implementation principles

- Design before implementation.
- One change at a time.
- Verify each change before proceeding.
- Do not modify working production connectors unnecessarily.
- Preserve existing state.
- Do not introduce Floorball-specific logic into the generic Event Platform core.
- Do not enable automatic Live monitoring before state persistence and failure handling are verified.
- Keep the existing v1.3.0 implementation available as a fallback.
- Document only verified capabilities as implemented.

## 17. Open questions before automatic Live implementation

The following details still require resolution:

1. Final registry schema and source-status mapping.
2. Safe registry persistence implementation and retry limits.
3. Runtime Watch injection into the generic execution engine.
4. First observation after match start.
5. Handling postponed and cancelled matches.
6. Notification delivery followed by persistence failure.
7. Coordination between Daily Discovery and Live state updates.
8. Schedule changes occurring after daily discovery.
9. Timezone interpretation of iBIS match start values.
10. GitHub Actions execution cost and startup time under continuous five-minute scheduling.
11. Handling replaced or skipped pending runs under GitHub Actions concurrency.
12. Safe detection of conflicting updates to the same Watch.

These questions must be resolved before unattended automatic Live monitoring is enabled.

## 18. Recommended next step

Implement and verify isolated safe registry merge logic.

Begin with simulated updates:

1. Discovery changes a match's scheduled start.
2. Live marks the same or another match completed.
3. Both updates are applied to the latest registry.
4. Neither change is lost.
5. Completed matches are not reactivated.

Then extend testing to independent Watch entries in `state.json` and conflict handling.

Only after successful isolated verification should persistent GitHub commits be introduced.

Do not modify production `state.json`, `config.yml` or Live monitoring during this initial persistence test.

The objective remains safe, incremental automation without compromising the verified v1.3.0 release.
