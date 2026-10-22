
# Event Platform Architecture

## Purpose

Event Platform monitors external event data, detects relevant changes, stores the latest known state, and sends notifications when something changes.

Golf was the first use case, but the platform is designed to remain independent of golf-specific or other domain-specific logic.

The architecture supports different external platforms through reusable connectors, generic Watches, persistent state, and independent monitoring modes.

## Current version and status

Current published production release: **v1.2.0**

The floorball implementation extends the existing architecture but has not yet been included in a new published release.

As of 22 October 2026:

- Daily golf monitoring is operational.
- Live golf monitoring is operational.
- Automatic floorball Discovery is operational.
- Automatic floorball Live Monitoring is deployed and scheduled.
- Automatic floorball Live Monitoring has passed technical regression tests.
- Automatic floorball monitoring has not yet been validated during a real match.

The platform supports two execution modes:

- Daily monitoring
- Live monitoring

Implemented connectors:

- `sgf_ranking` – Swedish Golf Federation ranking
- `golfbox_leaderboard` – GolfBox competition leaderboards
- `tournytt_api` – Tournytt leaderboard API
- `ibis_floorball` – Swedish floorball match monitoring

The first three connectors belong to the published v1.2.0 release. The floorball connector is implemented and undergoing production validation.

## High-level architecture

Event Platform separates external data acquisition, monitoring logic, notification formatting, persistence, and scheduling.

### General monitoring flow

Watch configuration
→ Connector
→ External data source
→ Normalized snapshot
→ Change detection
→ Notification formatting
→ ntfy
→ Subscriber devices

Monitoring state is stored in `state.json`.

GitHub Actions executes the platform.

cron-job.org triggers the production workflows.

### Daily execution

cron-job.org
→ GitHub Actions `daily.yml`
→ `watcher.py` with `RUN_MODE=daily`
→ Daily connectors
→ Snapshot comparison
→ Notification when applicable
→ Persist `state.json`
→ Floorball Discovery
→ iBIS competition data
→ Update `match_registry.json` when necessary

Daily execution combines existing golf monitoring with automatic floorball match discovery.

### Live execution

cron-job.org
→ GitHub Actions `live.yml`
→ `event_platform_live.py`
→ Load `config.yml`
→ Load `match_registry.json`
→ Select eligible floorball matches
→ Merge automatic and configured Live Watches
→ Execute connectors
→ Compare observations
→ Generate notifications when applicable
→ Persist changed Watch state
→ Update completed floorball matches

The Live process can monitor multiple Watches in the same execution.

## Architecture principles

1. The Event Platform core remains independent of golf-specific and floorball-specific acquisition logic.
2. Connectors own external data acquisition and normalization.
3. Connectors expose a common `fetch_snapshot(watch)` interface.
4. Watches have stable technical identities.
5. Connector-specific configuration belongs in `watch["source"]`.
6. Notification formatting is separate from data acquisition.
7. Scheduling remains external to the platform.
8. Persistent state must preserve unrelated Watches.
9. Discovery and Live have separate responsibilities.
10. Changes to monitoring lifecycle must not overwrite scheduling information.
11. Existing production monitoring must be protected during development.
12. Automated tests and real-world verification serve different purposes.

## Components

### Connectors

Connector implementations are stored in `connectors/`.

Each connector exposes:

`fetch_snapshot(watch)`

The connector:

- Reads source-specific configuration.
- Acquires data from the external platform.
- Identifies the requested entity.
- Normalizes the observation.
- Returns a snapshot or `None`.

Connectors do not own scheduling, Git persistence, or notification delivery.

Acquisition technologies such as Playwright, HTTP, JSON APIs, and SSE remain connector implementation details.

### GolfBox

Implementation:

`connectors/golfbox_leaderboard.py`

Uses Playwright and Chromium to access GolfBox leaderboards.

The connector supports:

- Different player-name formats.
- Multiple leaderboard classes.
- Pre-start observations.
- Hole-by-hole scoring.
- Position changes.
- Multi-round competitions.
- Final tournament results.

Validated against:

- Haninge Golfklubb
- Strängnäs Golfklubb
- NSGK / Hylinge
- GolfBox Tournament (`golfbox.dk`)

The GolfBox connector requires Chromium during GitHub Actions execution.

### Tournytt

Implementation:

`connectors/tournytt_api.py`

Uses structured leaderboard data from the Tournytt SSE API.

Verified capabilities include:

- API communication
- Player lookup
- State persistence
- Change detection
- Notifications

Tournytt-specific notification formatting remains an improvement opportunity.

### SGF Ranking

Implementation:

`connectors/sgf_ranking.py`

Supports Daily monitoring of Swedish Golf Federation ranking information.

The existing Daily workflow continues to use `watcher.py`.

### iBIS Floorball

Implementation:

`connectors/ibis_floorball.py`

Uses the Swedish Floorball / iBIS API.

The connector:

1. Obtains a temporary access token.
2. Validates the returned API root.
3. Retrieves the requested match.
4. Verifies MatchID.
5. Normalizes match information.
6. Normalizes and sorts registered match events.
7. Returns a structured snapshot.

Snapshots include:

- MatchID and competition
- Home and away teams
- TeamIDs and MatchTeamIDs
- Match date and time
- Match status
- Final-result indicator
- Home and away goals
- Registered match events

Events can include:

- Event ID and event type
- Period and match time
- Current score
- Player identity
- Assist identity
- Penalty description

The connector does not format notifications.

## Watch configuration

`config.yml` contains configured Watches.

A Watch uses:

- `id`
- `name`
- `connector`
- `mode`
- `source`

Example:

```yaml
id: "lukas-tournytt"
name: "Lukas Widegren - Tournytt"
connector: tournytt_api
mode: live
source:
  player: "Lukas Widegren"
  competition: 5406076
```

The Watch ID is its stable technical identity.

The human-readable name may change without changing the identity.

The platform core does not interpret connector-specific `source` values.

### Automatic floorball Watches

Floorball Live Watches are now generated dynamically from `match_registry.json`.

The permanent match identity is the iBIS MatchID.

Generated Watch IDs use:

`floorball-match-{match_id}`

For example:

`floorball-match-1750707`

The existing manually configured floorball Watches are excluded from automatic Live execution.

They are superseded by the dynamically selected Watches.

GolfBox and Tournytt Watches are preserved.

## Automatic floorball Discovery

### Purpose

Discovery identifies upcoming matches for configured teams without requiring manual MatchID configuration.

The implementation supports both currently configured Tyresö Trollbäcken teams.

### Components

- `floorball_discovery.py`
- `floorball_discovery_changes.py`
- `floorball_registry.py`
- `floorball_registry_merge.py`
- `floorball_git_persistence.py`

### Process

1. Read Discovery configuration.
2. Retrieve upcoming matches from iBIS.
3. Identify relevant matches for the configured teams.
4. Exclude unrelated, cancelled, and completed source matches.
5. Compare discovered matches against the persistent registry.
6. Calculate required changes.
7. Merge changes without overwriting Live-owned fields.
8. Persist registry changes through Git.

### Scheduling

Discovery executes as part of the existing Daily workflow.

The external Daily schedule remains managed through cron-job.org.

The Daily workflow runs golf monitoring first and Floorball Discovery afterwards.

### Verified behavior

On 22 October 2026:

- Discovery identified 31 matches.
- The matches were persisted in GitHub.
- A subsequent execution detected zero changes.
- Integration with the existing Daily workflow passed.
- Both upcoming October matches were verified in the registry.

The first automatically scheduled execution of the updated Daily workflow remains subject to operational observation.

## Match registry

Persistent file:

`match_registry.json`

The registry stores discovered matches independently of monitoring snapshots.

Its structure includes:

```json
{
  "schema_version": 1,
  "matches": {}
}
```

Match entries are keyed by MatchID.

The registry contains scheduling information, match identities, team information, and monitoring lifecycle information.

### Ownership

Discovery owns:

- Match discovery
- Match identity and scheduling
- Team and competition information
- Source scheduling status

Live owns:

- Monitoring lifecycle
- Completion status

The ownership model prevents Discovery from reactivating completed matches or overwriting Live-owned lifecycle information.

### Persistence

Registry changes are persisted through Git.

The implementation:

- Refreshes the latest repository state.
- Merges permitted changes.
- Preserves unrelated matches.
- Retries rejected Git pushes.
- Avoids unnecessary commits when no changes exist.

## Automatic Live match selection

Implementation:

`floorball_match_selection.py`

The selection logic reads the match registry and identifies eligible matches.

The activation window begins 15 minutes before scheduled match start.

The selection logic handles:

- Multiple eligible matches
- Delayed matches
- Postponed matches
- Cancelled matches
- Completed matches
- Swedish daylight-saving and winter time

Completed matches are excluded from subsequent automatic selection.

### Verified examples

- JAS match 1750707: activation 23 October 2026 at 19:30.
- Men's match 1703577: activation 25 October 2026 at 15:30.

Both activation times were verified through simulated-time tests using the real registry.

Actual automatic activation during a live match remains to be verified.

## Live configuration preparation

Components:

- `floorball_live.py`
- `floorball_watch_merge.py`

`floorball_live.py` loads the registry and prepares the runtime configuration.

`floorball_watch_merge.py` combines configured Live Watches with automatically selected floorball Watches.

The merge process:

- Preserves non-floorball Live Watches.
- Excludes Daily Watches.
- Excludes manually configured floorball Watches.
- Includes automatically selected floorball Watches.
- Prevents duplicate Watch IDs.
- Does not modify its inputs.

This enables multiple simultaneous Live Watches without manually changing `live.yml`.

## Monitoring engine

### Generic watcher

`watcher.py` remains the generic monitoring engine.

It supports:

- Configured connectors
- Daily and Live execution modes
- Optional `WATCH_ID` filtering
- Snapshot comparison
- Notification formatting and delivery
- State persistence

It can also receive a prepared configuration through:

`main(config=None)`

Existing Daily execution remains backward compatible.

### Automatic Live runner

Implementation:

`event_platform_live.py`

This is the production entry point for automatic Live Monitoring.

It:

1. Loads the configured Watches.
2. Prepares the automatic Live configuration.
3. Reads existing Watch state.
4. Retrieves current observations.
5. Detects changed snapshots.
6. Sends notifications when applicable.
7. Collects changed state entries.
8. Persists changes through Git.
9. Marks completed floorball matches.

The runner does not require a hard-coded MatchID.

It retains GolfBox and Tournytt monitoring.

### Late baseline protection

For a newly selected floorball match, the first observation normally establishes a baseline without notification.

If the first observation already contains match activity, the current runner raises an error rather than silently discarding earlier events.

This is a deliberate safety limitation.

Recovery from late first observations remains future work.

## Persistent monitoring state

Persistent file:

`state.json`

Each Watch is stored under its stable Watch ID.

State entries contain:

- Serialized normalized snapshot
- Normalized snapshot fields

State allows independent executions to detect changes.

### Live Git persistence

The automatic Live runner persists changed Watch entries against the latest Git repository state.

It uses optimistic concurrency checking to detect when the same Watch has changed since the observation was collected.

Unrelated Watch state is preserved.

A detected same-Watch conflict causes the update to be rejected rather than silently overwriting newer state.

### Completed matches

Components include:

- `floorball_atomic_persistence.py`
- `floorball_registry_merge.py`
- `event_platform_live.py`

When a final result is observed, the Live process is designed to persist:

- Final snapshot in `state.json`
- `completed` status in `match_registry.json`

Both changes are included in the same Git commit.

The underlying atomic persistence functionality has passed automated tests.

Its operation during an automatically monitored real match remains unverified.

### Important operational limitation

Git-based persistence is not a transactional notification system.

Notifications are currently sent before the corresponding Git update is committed.

If notification delivery succeeds but Git persistence fails, the same change may be notified again.

Exactly-once notification delivery is not guaranteed.

The implementation also uses `git reset --hard` during persistence and therefore requires a dedicated disposable GitHub Actions working directory.

## Change detection

The monitoring engine compares the current normalized snapshot with the previous snapshot for the Watch.

A changed snapshot can trigger notification and state persistence.

For Daily monitoring, the first observation establishes a baseline without notification.

For existing golf Live monitoring, the first valid observation may generate a notification.

For floorball, the first pre-match observation establishes a baseline without notification.

### Floorball event detection

The iBIS connector returns the currently available match events.

The notification formatter compares current events against previously recorded event IDs.

Previously unseen events are treated as new.

Multiple new events can be included in one notification.

Corrected and deleted source events remain a future improvement.

## Notifications

Notification formatting is implemented in:

`notification_formatters.py`

ntfy is the current notification provider.

Multiple subscriber devices may subscribe to the same ntfy topic.

The formatter is responsible for connector-specific presentation.

### Floorball notifications

Supported information includes:

- Match identification
- Current score
- Match-status changes
- Period start and end
- Goals
- Penalties
- Final result

Regular goals use iBIS MatchEventTypeID 1.

Empty-net goals use MatchEventTypeID 12 and are identified as `(tom bur)`.

For followed-team events, player and assist information can be included.

Events involving the highlighted player can be marked with a star.

Player highlighting covers:

- Goals
- Assists
- Penalties

Real-world monitoring has verified goals, penalties, period events, and final results.

Highlighted-player events have passed technical tests but have not yet been observed in a qualifying real-world event.

## Execution and scheduling

### Daily workflow

File:

`.github/workflows/daily.yml`

Triggered externally by cron-job.org.

Normal schedule:

08:00 Europe/Stockholm.

Responsibilities:

- Daily golf monitoring
- Persist changed golf state
- Floorball Discovery
- Persist discovered match changes

### Live workflow

File:

`.github/workflows/live.yml`

Triggered externally by cron-job.org.

Polling interval:

5 minutes.

Production entry point:

`event_platform_live.py`

Live Monitoring now uses automatic match selection.

The previous hard-coded `WATCH_ID` has been removed from the production workflow.

### Concurrency

Daily and Live use the GitHub Actions concurrency group:

`event-platform-state`

With:

`cancel-in-progress: false`

This reduces overlapping executions within the participating workflows.

Git persistence additionally provides conflict detection and retry mechanisms.

### Runtime dependencies

The Live workflow uses:

- Python 3.11
- Project Python requirements
- Playwright
- Chromium

Chromium is required by the GolfBox connector.

The workflow installs Chromium without repeatedly installing the full operating-system dependency set.

This optimization reduced a verified Live workflow execution from 4 minutes 20 seconds to approximately 37 seconds.

A subsequent automatically triggered run completed in approximately 30 seconds.

### Operational verification

On 22 October 2026:

- Automatic Live workflow execution succeeded.
- GolfBox and Tournytt were processed.
- No floorball match was eligible before its activation window.
- No unnecessary state persistence was performed.
- cron-job.org successfully triggered the updated Live workflow.
- The complete automatic workflow finished successfully.

Real-world floorball match activation and completion remain pending verification.

## Testing

The permanent regression workflow is:

`.github/workflows/test-regression.yml`

It covers:

- Existing golf connectors and notification behavior
- Floorball Discovery
- Match registry handling
- Registry merge rules
- Match selection
- Watch merging
- Notification formatting
- Git persistence
- Atomic completion persistence
- Live integration

As of 22 October 2026:

**105 Floorball automated tests passed.**

Existing golf regression tests also passed.

The separate historical test-workflows remain in the repository pending cleanup.

The Python test files should be retained as regression coverage.

## Historical floorball validation

### 15 October 2026

The first real-world floorball monitoring validation confirmed:

- Live iBIS data acquisition
- Goal notifications
- Penalty notifications
- Period events
- Final-result notifications
- ntfy delivery

### 17 October 2026

A second match was monitored using the earlier manually configured Live approach.

Match events and final results were verified.

Player-specific highlighting remained unverified because the highlighted player did not generate a qualifying event.

### 22 October 2026

Automatic Discovery, persistent match registry, runtime Watch selection, and automatic Live execution were integrated.

The automated monitoring architecture replaced manual MatchID selection in the production Live workflow.

The first full real-world acceptance test of the automatic process is planned for the JAS match on 23 October.

## Operational safeguards

During active events:

- Avoid changing working production connectors.
- Avoid unnecessary workflow changes.
- Do not delete active monitoring state.
- Do not manually create duplicate monitoring Watches.
- Verify GitHub Actions status after operational changes.
- Preserve historical state and completed-match records.
- Distinguish successful technical tests from real-world acceptance.

The existing Live schedule should remain active during the planned production validation unless a verified operational issue requires intervention.

## Lessons learned

### GolfBox

A competition can contain multiple leaderboard classes.

The leaderboard identifier may therefore be required in addition to the competition identifier.

Player names can appear as:

- Lukas Widegren
- WIDEGREN, Lukas

GolfBox changes presentation across the tournament lifecycle.

The `hole` field may represent a start time, current hole, or final completion marker.

Multi-round data includes round-specific scores, total strokes, and relative-to-par information.

### Tournytt

Tournytt exposes structured leaderboard information through SSE.

Player entries can appear before play begins.

Baseline handling therefore differs from GolfBox.

### Floorball

iBIS exposes structured match and event data.

MatchTeamID and TeamID serve different purposes.

Empty-net goals use a distinct event type.

Persistent match identity enables monitoring across independent GitHub Actions executions.

Separating Discovery-owned and Live-owned fields prevents scheduling updates from accidentally reactivating completed matches.

### GitHub Actions

External scheduling through cron-job.org has been more reliable for this deployment than the previously attempted internal scheduling.

Installing full Playwright operating-system dependencies on every Live execution caused excessive runtime.

Separating Python dependencies and Chromium installation substantially reduced execution time.

## Future development

### Immediate operational validation

- Verify automatic JAS match activation on 23 October.
- Verify match notifications during live play.
- Verify final-result persistence.
- Verify automatic `completed` status.
- Verify automatic men's match activation on 25 October.
- Verify no duplicate match monitoring.

### Reliability improvements

- Improve notification delivery and persistence coordination.
- Support recovery from late first observations.
- Handle corrected or deleted match events.
- Improve observability of Git conflicts.
- Validate simultaneous updates under real-world conditions.

### Maintenance

- Consolidate historical GitHub Actions test-workflows.
- Retain permanent Python regression tests.
- Remove obsolete manual floorball configuration when operational validation is complete.
- Review unused implementation modules before deletion.

### Future capabilities

- Configurable notification preferences
- Additional teams and competitions
- Additional external event sources
- Improved notification providers
- Operational monitoring and diagnostics

Future improvements should be driven by demonstrated needs rather than unnecessary expansion of the platform core.

## Related documentation

- `README.md` – project overview and usage
- `PROJECT_CONTEXT.md` – current project status and handover
- `docs/decisions.md` – architectural decisions
- `docs/backlog.md` – outstanding work
- `docs/ways-of-working.md` – development procedures
- `docs/design-floorball.md` – original floorball implementation
- `docs/design-floorball-automation.md` – automatic floorball design
- `docs/design-v1.2.md` – v1.2 design history

GitHub remains the authoritative source of truth.
