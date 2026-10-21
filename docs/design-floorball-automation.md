
# Event Platform – Floorball Automation Design

Status: Draft – Pending review and approval

Created: 21 October 2026

Current production release: v1.3.0

## 1. Purpose

Automatically discover and monitor floorball matches for selected teams and competitions without manually configuring individual matches or activating Live monitoring for each event.

The initial use case is monitoring the two Tyresö Trollbäcken IBK teams in which Lukas Widegren participates.

The solution must reuse the existing Event Platform architecture and the verified iBIS connector wherever possible.

The design separates daily match discovery from five-minute Live monitoring.

No implementation changes are authorized until the design has been reviewed and approved.

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

The initial implementation uses the verified iBIS endpoint:

GET /competitions/{competition_id}/matches

The endpoint returns the competition's match list.

The initial investigation confirmed that relevant matches can be identified using TeamID and MatchID.

### Live Match Monitoring

Triggered by cron-job.org every five minutes.

Responsibilities:

1. Load the persistent match registry.
2. Identify matches within the active monitoring window.
3. Exclude completed matches.
4. Create runtime Watch objects for relevant matches.
5. Invoke the existing ibis_floorball connector.
6. Compare normalized snapshots with persisted state.
7. Generate notifications for relevant changes.
8. Persist updated match state.
9. Stop monitoring matches after the final result has been saved.

The Live process does not retrieve full competition schedules during normal execution.

## 5. Persistent match registry

A separate persistent registry is proposed.

Suggested file:

match_registry.json

The registry contains discovered matches and their scheduling information.

Example structure:

    {
      "1750707": {
        "competition_id": 45004,
        "team_id": 20872,
        "match_id": 1750707,
        "scheduled_start": "2026-10-23T19:45:00",
        "home_team": "Tyresö Trollbäcken IBK",
        "away_team": "FBI Tullinge",
        "status": "scheduled"
      }
    }

The registry is separate from state.json.

Responsibilities are separated:

- match_registry.json stores match discovery and scheduling information.
- state.json stores the latest observed normalized snapshots for change detection.

Discovered matches retain stable MatchIDs.

Runtime Watch IDs use the format:

floorball-match-{match_id}

Existing Watch IDs remain unchanged.

### Registry lifecycle

A match may be:

- scheduled
- active
- completed
- postponed
- cancelled

The registry must distinguish between source-reported match status and internal monitoring lifecycle.

A completed match should remain recorded to avoid accidental reactivation.

The exact registry schema and status mapping must be verified before implementation.

## 6. Match activation

A match becomes eligible for Live monitoring 15 minutes before its scheduled start.

Example:

Scheduled start: 19:45

Monitoring eligibility begins: 19:30

The first Live execution after 19:30 selects the match.

### Pre-match baseline

A baseline must exist before the first meaningful match event.

The automation should establish a baseline when the match first becomes eligible, provided the match has not started and no events or goals have been registered.

The existing baseline principles must be preserved.

If the first observation occurs after the match has started, the system must not silently discard already registered events.

Late discovery and late baseline creation require explicit handling.

## 7. Match completion

The existing iBIS connector returns:

has_final_result

When this becomes true:

1. The final snapshot is processed.
2. The final-result notification is generated.
3. The final snapshot is persisted successfully.
4. The match becomes completed in the registry.
5. Future Live executions exclude the completed match.

A match must not be marked completed before its final state has been successfully persisted.

If execution fails, the match remains eligible for retry.

## 8. Postponed and cancelled matches

Daily Discovery detects changes to match schedules and statuses.

### Postponed matches

When a match is rescheduled:

- Preserve its stable MatchID where the source retains it.
- Update the scheduled start time.
- Recalculate the monitoring window.
- Preserve existing state.

If iBIS assigns a new MatchID, the relationship between old and new matches requires investigation.

### Cancelled matches

Cancelled matches should not enter normal Live monitoring.

The original match record should remain in the registry.

The exact iBIS status codes for postponed and cancelled matches must be verified against real API data.

## 9. Multiple matches

Each discovered match uses an independent runtime Watch.

Example:

    floorball-match-1750707
    floorball-match-1703577

The Live process must support multiple eligible matches in one execution.

The existing ibis_floorball connector is called separately for each match.

The generic Event Platform core must remain independent of floorball-specific scheduling logic.

The implementation must determine how runtime Watches are provided to the existing execution engine without changing the Unified Connector Interface.

## 10. State persistence and concurrency

The existing state.json file remains the authoritative monitoring state.

The current Live workflow can overwrite concurrent changes because it restores an entire saved state file after synchronizing with main.

This must be corrected before broader automatic monitoring is enabled.

### Proposed approach

1. Track which Watch entries changed during an execution.
2. Retrieve the latest repository state before committing.
3. Merge only changed Watch entries.
4. Preserve unrelated entries.
5. Retry safely if the repository changes during the commit process.

The merge must not overwrite a newer update for the same Watch with an older snapshot.

### Overlapping executions

GitHub Actions concurrency controls should prevent overlapping Live executions.

The implementation must also consider interactions between:

- Daily ranking monitoring.
- Daily match discovery.
- Live match monitoring.

Concurrency controls alone do not eliminate all possible conflicts between different workflows.

Both state.json and match_registry.json require safe persistence strategies.

## 11. Scheduling

### Daily Discovery

Frequency: once per day.

The discovery schedule is separate from existing SGF Ranking monitoring.

A new GitHub Actions workflow is preferred over adding floorball-specific discovery logic to the existing Daily workflow.

### Live Monitoring

Frequency: every five minutes.

cron-job.org continues triggering the Live workflow.

When no match is eligible:

- No match connector is called.
- No notification is sent.
- No monitoring state changes are required.
- The execution exits quickly.

The Live workflow should avoid unnecessary Playwright and Chromium installation when running only HTTP-based floorball monitoring.

Any optimization must preserve the ability to monitor existing GolfBox and Tournytt Watches when required.

## 12. Notification behavior

Existing floorball notification formatting remains unchanged for the initial implementation.

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

## 13. Failure handling

### Discovery failure

If daily match discovery fails:

- Preserve the existing registry.
- Do not remove previously discovered matches.
- Report the execution failure.
- Allow the next scheduled discovery to retry.

### Live acquisition failure

If an individual match cannot be retrieved:

- Preserve its previous state.
- Do not mark the match completed.
- Retry on a subsequent Live execution.
- Avoid preventing other eligible matches from being monitored.

### State persistence failure

If state cannot be persisted:

- Do not treat the match as safely completed.
- Preserve sufficient information to retry.
- Avoid silently losing updates.

The relationship between notification delivery and state persistence requires further design because notifications may be repeated if an execution fails after delivery.

## 14. Validation plan

### Phase A – Discovery

Verify that Daily Discovery automatically identifies:

- Match 1750707 for JAS.
- Match 1703577 for Herrar.

Confirm correct:

- CompetitionID.
- TeamID.
- MatchID.
- Match date and time.
- Home and away teams.

No Live monitoring or notifications during this phase.

### Phase B – Monitoring selection

Verify that the correct matches become eligible 15 minutes before their scheduled starts.

Verify that unrelated and completed matches are excluded.

Use simulated times and mocked data where practical.

### Phase C – State persistence

Verify:

- Preservation of existing Watch state.
- Independent state entries for multiple matches.
- Safe merging of concurrent changes.
- Prevention of overlapping Live executions.
- Retry behavior following failures.

### Phase D – Real-world acceptance

Friday 23 October 2026:

JAS – MatchID 1750707.

Sunday 25 October 2026:

Herrar – MatchID 1703577.

Acceptance criteria:

- Match discovered automatically.
- Monitoring begins without manual MatchID configuration.
- Existing floorball notifications work.
- Final result is received.
- Final state is saved.
- Completed match is no longer monitored.
- No existing Golf monitoring is disrupted.

The Friday match should only be used for full automatic monitoring if the implementation and safety tests have been completed successfully.

Otherwise, use the verified manual monitoring approach.

## 15. Implementation principles

- Design before implementation.
- One change at a time.
- Verify each change before proceeding.
- Do not modify working production connectors unnecessarily.
- Preserve existing state.
- Do not introduce floorball-specific logic into the generic Event Platform core.
- Do not enable automatic Live monitoring before state persistence and failure handling are verified.
- Keep the existing v1.3.0 implementation available as a fallback.
- Document only verified capabilities as implemented.

## 16. Open questions before implementation

The following details still require resolution:

1. Exact persistent registry schema.
2. Registry update and merge behavior.
3. Runtime Watch injection into the generic execution engine.
4. Safe handling of first observations after match start.
5. Exact mapping of iBIS match-status values.
6. Behavior when final-result notification succeeds but state persistence fails.
7. Coordination between Daily Discovery and Live state updates.
8. Handling of match schedule changes occurring after daily discovery.
9. GitHub Actions execution cost and startup time for continuous five-minute scheduling.

These questions should be resolved before enabling unattended automatic monitoring.

## 17. Recommended next step

Review and approve this design direction.

Then resolve the remaining technical questions in priority order.

Begin with a read-only Daily Discovery implementation that identifies upcoming matches and produces diagnostic output without changing config.yml, state.json, match_registry.json or notification behavior.

Verify the discovery results against the two known matches.

Only then proceed to persistent registry updates and automatic Live monitoring.

The initial goal is safe, incremental automation without compromising the verified v1.3.0 release.
