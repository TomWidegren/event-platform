
# Event Platform – Floorball Automation Design

**Status:** Implemented and deployed – real-world automatic match acceptance pending

**Created:** 21 October 2026  
**Last updated:** 22 October 2026

**Last documented published release:** v1.2.0  
**Automatic Floorball implementation:** Deployed, not yet included in a confirmed new release.

## 1. Purpose

Automatically discover and monitor floorball matches for selected teams and competitions without manually configuring individual matches or activating monitoring for each event.

The initial use case covers two Tyresö Trollbäcken IBK teams associated with Lukas Widegren.

The platform monitors relevant team matches regardless of whether Lukas participates.

The solution extends Event Platform's generic connector architecture while preserving existing golf monitoring.

## 2. Scope and implementation status

| Capability | Status |
|---|---|
| Automatic match discovery | Implemented and verified |
| Persistent match registry | Implemented and verified |
| Daily Discovery execution | Manually verified in production workflow |
| Automatic Live match selection | Implemented and tested |
| Multiple Live Watches | Implemented and tested |
| Pre-match activation | Simulated-time verified |
| Match notifications | Previously verified in manual live monitoring |
| Coordinated Git persistence | Automated tests passed |
| Automatic match completion | Implemented, real-world verification pending |
| External five-minute scheduling | Operational |
| Automatic real-match acceptance | Pending |

Excluded from the initial implementation:

- Automatic discovery of a player's team memberships.
- Unconfigured competitions.
- User interfaces for team management.
- Configurable notification preferences.
- Replacement of ntfy.
- Replacement of GitHub persistence.
- Changes to existing golf connectors.

## 3. Configuration

Season: 2026/27

Highlighted player:

- Lukas Widegren
- PlayerID: `585280`

Configured teams:

| Team | TeamID | CompetitionID |
|---|---|---|
| Tyresö Trollbäcken IBK – JAS | 20872 | 45004 |
| Tyresö Trollbäcken IBK – Herrar | 4194 | 44356 |

The configuration identifies teams and competitions rather than individual matches.

### Initial acceptance matches

| Date | MatchID | Scheduled start | Activation |
|---|---|---|---|
| 23 October 2026 | 1750707 | 19:45 | 19:30 |
| 25 October 2026 | 1703577 | 15:45 | 15:30 |

All times use Europe/Stockholm.

The matches were identified through iBIS Discovery and verified in the persistent registry.

## 4. Architecture

The solution separates two processes:

1. Daily Match Discovery.
2. Automatic Live Monitoring.

Both use the existing GitHub Actions environment and external scheduling through cron-job.org.

### 4.1 Daily Discovery

Execution:

`cron-job.org → daily.yml → watcher.py → Floorball Discovery`

The existing SGF Ranking monitoring runs first.

Floorball Discovery then:

1. Loads configured teams and competitions.
2. Authenticates with iBIS.
3. Retrieves competition match lists.
4. Identifies relevant matches using TeamIDs.
5. Detects new matches and schedule changes.
6. Calculates registry changes.
7. Merges changes according to field ownership.
8. Persists changes in GitHub.

The verified iBIS endpoint is:

`GET /competitions/{competition_id}/matches`

Discovery does not modify monitoring snapshots in `state.json`.

### 4.2 Automatic Live Monitoring

Execution:

`cron-job.org → live.yml → event_platform_live.py`

The Live runner:

1. Loads `config.yml`.
2. Loads `match_registry.json`.
3. Selects eligible matches.
4. Generates runtime Watches.
5. Combines them with configured non-floorball Live Watches.
6. Retrieves normalized connector observations.
7. Compares observations with persistent state.
8. Sends notifications when applicable.
9. Persists changed Watch entries.
10. Updates completed matches.

The Live runner does not retrieve full competition schedules during normal execution.

The implementation supports multiple eligible matches in one run.

## 5. Implemented components

### Discovery and registry

- `floorball_discovery.py`
- `floorball_discovery_changes.py`
- `floorball_registry.py`
- `floorball_registry_merge.py`
- `floorball_git_persistence.py`

### Live selection and execution

- `floorball_match_selection.py`
- `floorball_watch_merge.py`
- `floorball_live.py`
- `event_platform_live.py`

### Persistence

- `floorball_atomic_persistence.py`
- `floorball_git_persistence.py`
- `floorball_registry_merge.py`

### Existing shared components

- `watcher.py`
- `notification_formatters.py`
- `connectors/ibis_floorball.py`
- Existing golf connectors

The generic connector interface remains:

`fetch_snapshot(watch)`

The automatic Live runner uses existing connector and notification functionality rather than introducing a new connector interface.

## 6. Persistent match registry

File:

`match_registry.json`

Schema version: 1

Example:

```json
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
    }
  }
}
```

The registry stores discovered matches and monitoring lifecycle information.

It is separate from `state.json`, which stores normalized monitoring snapshots.

### Stable identity

Each match uses its iBIS MatchID as the registry key.

Runtime Watch IDs use:

`floorball-match-{match_id}`

This identity remains stable across independent executions.

### Field ownership

| Component | Owned information |
|---|---|
| Discovery | Match identity, scheduling, teams, competitions and source status |
| Live | Monitoring lifecycle and completion |
| Monitoring layer | Normalized snapshots in `state.json` |

Discovery cannot reset completed matches to scheduled.

Live cannot modify Discovery-owned scheduling information.

Field-level merging preserves independent changes.

## 7. Discovery verification

### 21 October 2026 – Initial API verification

A read-only GitHub Actions workflow authenticated with iBIS and retrieved competition match lists.

| Result | JAS | Herrar |
|---|---:|---:|
| Competition matches | 110 | 90 |
| Relevant team matches | 20 | 18 |
| Upcoming matches | 17 | 14 |
| Expected MatchID found | Yes | Yes |

Both acceptance matches were identified without supplying individual MatchIDs to the API request.

### 21 October – Registry tests

Eight initial registry tests passed.

Verified behavior included:

- New matches added.
- Existing matches preserved.
- Schedule changes updated.
- Completed matches not reactivated.
- Temporarily missing matches preserved.
- Unrelated teams excluded.
- Invalid updates did not mutate original data.

### 22 October – Permanent Discovery

The full Discovery chain was tested against real iBIS data.

Results:

- 31 relevant matches discovered.
- 31 matches persisted in GitHub.
- Both acceptance matches verified in the registry.
- A repeated execution detected zero changes.
- No unnecessary Git commit was required.

The updated Daily workflow was also tested manually with SGF Ranking and Floorball Discovery together.

The first scheduled execution of the updated Daily workflow remained pending operational confirmation at the end of this development session.

## 8. Match lifecycle

The persistent lifecycle uses:

- `scheduled`
- `completed`

Eligibility and active monitoring are primarily calculated at runtime rather than persisted on every polling cycle.

### Scheduled

A match exists in the registry but is not yet eligible for Live Monitoring.

### Eligible

Eligibility begins 15 minutes before scheduled match start.

The selection logic also handles delayed matches and excludes cancelled, postponed and completed matches according to the implemented rules.

### Monitoring

The Live runner selects an eligible match and retrieves observations through `ibis_floorball`.

The first valid pre-match observation establishes a baseline without notification.

Subsequent changes can generate notifications.

### Completed

When `has_final_result` becomes true, the runner is designed to:

1. Process the final snapshot.
2. Generate the final-result notification.
3. Persist the final Watch snapshot.
4. Mark the registry entry `completed`.
5. Exclude the match from subsequent monitoring.

The final snapshot and completion marker are committed together.

The automatic completion sequence has passed technical tests but remains unverified during a real automatically selected match.

## 9. Automatic Watch selection

Implementation:

`floorball_match_selection.py`

The selection logic supports:

- Fifteen-minute pre-match activation.
- Multiple eligible matches.
- Delayed matches.
- Cancelled and postponed match exclusion.
- Completed match exclusion.
- Swedish summer and winter time.

Simulated-time verification passed for both acceptance matches.

### Runtime Watch generation

`floorball_live.py` prepares the runtime configuration.

`floorball_watch_merge.py`:

- Preserves GolfBox and Tournytt Watches.
- Excludes Daily Watches.
- Excludes obsolete manually configured floorball Watches.
- Adds automatically selected floorball Watches.
- Prevents duplicate Watch IDs.
- Preserves the original input data.

The original manually configured floorball Watches remain in `config.yml` temporarily.

They are excluded during automatic Live execution.

Their removal is planned after real-world acceptance.

## 10. Baseline handling

A pre-match baseline prevents existing source events from being interpreted as new notifications.

For floorball, the first observation normally establishes a baseline without notification.

### Late first observation

If the first observation already contains match activity, the current automatic Live runner raises an error instead of silently discarding earlier events.

This protects against unnoticed data loss.

However, it also means a late start can interrupt monitoring.

A safe recovery mechanism remains future work.

## 11. Notifications

The existing floorball notification formatter is reused.

Supported information includes:

- Match identification.
- Score changes.
- Goals.
- Empty-net goals.
- Assists.
- Penalties.
- Period events.
- Match status.
- Final results.

Player-specific highlighting uses PlayerID `585280`.

Regular goals use MatchEventTypeID 1.

Empty-net goals use MatchEventTypeID 12.

New match events are identified by comparing event IDs against the previous snapshot.

Multiple new events may be included in one notification.

### Notification delivery limitation

The current Live runner sends notifications before committing corresponding state changes.

If ntfy delivery succeeds but Git persistence fails, the same event may be notified again.

Exactly-once notification delivery is not guaranteed.

This limitation is documented and accepted for the current implementation, subject to operational experience.

## 12. Git persistence and concurrency

Persistent files:

- `state.json`
- `match_registry.json`

The automatic Live runner uses Git-based persistence with controlled retries.

### Registry protection

Registry updates respect Discovery and Live field ownership.

Unrelated matches are preserved.

### State protection

Only changed Watch entries are merged into the latest repository state.

Unrelated Watch entries are preserved.

Optimistic concurrency checking detects when another execution has changed the same Watch since the observation was collected.

A conflicting stale update is rejected rather than silently overwriting newer state.

### Completed match persistence

The final Watch snapshot and registry completion status are included in the same Git commit.

The underlying atomic persistence module has passed automated tests.

### Shared concurrency group

Daily and Live workflows use:

```yaml
concurrency:
  group: event-platform-state
  cancel-in-progress: false
```

This prevents overlapping execution among participating workflows.

It does not guarantee execution of every queued run; newer pending runs can replace earlier pending runs.

The system must therefore tolerate delayed or skipped polling cycles.

### Dedicated working directory

The Git persistence implementation uses:

`git reset --hard`

It must run only in a dedicated disposable Git working directory.

GitHub Actions provides such a working directory for the production workflows.

## 13. Scheduling and operations

### Daily

Workflow:

`.github/workflows/daily.yml`

External scheduler:

cron-job.org

Normal schedule:

08:00 Europe/Stockholm.

Daily combines SGF Ranking monitoring with Floorball Discovery.

### Live

Workflow:

`.github/workflows/live.yml`

Entry point:

`event_platform_live.py`

External scheduler:

cron-job.org

Polling interval:

Five minutes.

The scheduler remains active between matches.

The runtime selection logic determines whether a floorball match is eligible.

This replaces manual activation and MatchID selection.

### Runtime optimization

The original Live workflow installed the full Playwright operating-system dependency set during each run.

This caused a measured execution time of 4 minutes 20 seconds.

GolfBox requires Playwright and Chromium, so browser support was retained.

The workflow was optimized to install Chromium without repeatedly installing the full system dependency set.

Measured results:

- Optimized manual run: approximately 37 seconds.
- Automatic scheduled run: approximately 30 seconds.

Both completed successfully.

## 14. Validation results

### Automated tests

As of 22 October 2026:

**105 Floorball regression tests passed.**

The existing golf regression tests also passed.

The consolidated test workflow is:

`.github/workflows/test-regression.yml`

Coverage includes:

- Discovery.
- Registry updates.
- Match selection.
- Watch merging.
- Notification formatting.
- State handling.
- Git persistence.
- Atomic completion.
- Live integration.

### Production workflow verification

The following were verified:

- Manual Daily integration.
- Permanent Discovery registry storage.
- Repeated Discovery without unnecessary updates.
- Manual automatic Live execution.
- Automatic Live execution triggered by cron-job.org.
- Preservation of GolfBox and Tournytt monitoring.
- No eligible floorball matches selected prematurely.
- Successful execution without unnecessary persistence.
- Optimized runtime.

### Real-world automatic monitoring

Not yet verified as of 22 October 2026:

- Automatic pre-match activation during an actual match.
- Automatic baseline creation in the production Live runner.
- Event notifications during automatically selected matches.
- Automatic final-result persistence.
- Automatic registry completion.
- Exclusion of a completed real match.

These are the remaining acceptance criteria.

## 15. Historical floorball validation

### 15 October 2026

MatchID: `1750693`

Huddinge IBS – Tyresö Trollbäcken IBK

Verified:

- iBIS acquisition.
- Goal notifications.
- Penalty notifications.
- Period events.
- Final-result notification.
- ntfy delivery.

The match also revealed the distinct iBIS event type for empty-net goals.

### 17 October 2026

MatchID: `1703572`

IFK Haninge (B) – Tyresö Trollbäcken IBK (A)

Verified:

- Five-minute Live monitoring.
- Notifications.
- Final result of 5–4.
- Final state persistence.
- Preservation of unrelated Watch state.

Both matches used the earlier manually configured monitoring approach.

These validations establish confidence in the connector and notification formatter but do not constitute acceptance of the new automatic match-selection process.

## 16. Real-world acceptance plan

### 23 October 2026 – JAS

MatchID: `1750707`

Expected activation: 19:30.

### 25 October 2026 – Herrar

MatchID: `1703577`

Expected activation: 15:30.

Acceptance criteria:

1. Match selected automatically.
2. Pre-match baseline established.
3. Match events detected.
4. Notifications delivered correctly.
5. Final-result notification delivered.
6. Final state persisted.
7. Match marked `completed`.
8. Completed match excluded from subsequent selection.
9. No duplicate monitoring.
10. Existing golf monitoring unaffected.

Player highlighting is verified only if a qualifying player event occurs.

## 17. Known limitations and future improvements

### Operational reliability

- Late first-observation recovery.
- Notification delivery and persistence coordination.
- Broader concurrent execution validation.
- Diagnostics for Git conflicts.
- Recovery after failed or skipped runs.

### Match data

- Corrected and deleted source events.
- Replaced MatchIDs.
- Late match-day schedule changes.
- Additional source-status interpretation.
- Verification of empty-net goal formatting during a real event.

### Notifications

- Configurable notification preferences.
- Improved match-start wording.
- Additional event presentation.
- Real-world player-specific highlighting.

### Maintenance

- Remove redundant historical test-workflows.
- Preserve Python regression tests.
- Review unused implementation modules.
- Remove obsolete manual floorball Watches after acceptance.
- Maintain architecture, decisions, backlog and project context.

## 18. Design decisions and deviations

The implemented solution follows the agreed separation of Discovery and Live.

The following design decisions were refined during implementation.

### Reuse the existing Daily schedule

The original design preferred a separate Discovery workflow.

The implemented solution instead executes Discovery after SGF Ranking in the existing Daily workflow.

This avoids introducing another external scheduler.

The Python implementations remain separate.

### Continuous Live scheduling

The earlier manual approach enabled Live monitoring only around specific events.

The new Live schedule remains active continuously.

Automatic match selection determines when floorball monitoring is required.

### Dedicated Live runner

Rather than adding floorball-specific scheduling logic to the generic watcher, the implementation uses `event_platform_live.py`.

The existing connector interface remains unchanged.

### Git persistence retained

GitHub-based JSON persistence was retained rather than introducing a database.

Conflict detection, merge rules and coordinated commits address the principal identified risks.

Exactly-once notification delivery remains outside the guarantees of this architecture.

### Regression consolidation

Numerous standalone test-workflows were created during development.

The permanent consolidated regression workflow now provides the primary test entry point.

Historical test-workflow cleanup is planned after real-world acceptance.

## 19. Current conclusion

The automatic Floorball implementation has reached operational deployment.

Discovery, persistent registry storage, dynamic Watch selection and automatic GitHub Actions execution have been technically verified.

The system has also passed 105 Floorball regression tests while preserving existing golf regression behavior.

The implementation is not yet fully accepted for real-world automatic match monitoring.

The next milestone is successful monitoring and completion of the matches on 23 and 25 October 2026.

Until those validations are complete, avoid nonessential changes to the working production workflows and connectors.

## Related documentation

- `docs/ARCHITECTURE.md`
- `docs/decisions.md`
- `docs/backlog.md`
- `docs/design-floorball.md`
- `docs/design-v1.2.md`
- `docs/ways-of-working.md`
- `README.md`
- `PROJECT_CONTEXT.md`

GitHub remains the authoritative source of truth.
