
# Event Platform

Event Platform is a lightweight framework for monitoring changing data from external platforms and notifying subscribers when relevant changes occur.

Golf was the first use case, but the architecture is designed to remain independent of golf-specific or other domain-specific logic.

The platform supports golf and Swedish floorball monitoring through reusable connectors, persistent state and externally scheduled execution.

## Current Status

**Last documented published production release: v1.2.0**

**Current deployed functionality: Automatic Floorball Discovery and Live Monitoring**

**Last updated: 22 October 2026**

The published v1.2.0 release established the Unified Connector Interface architecture.

Subsequent development introduced Swedish floorball monitoring through iBIS and automated match discovery and selection.

As of 22 October 2026:

- GolfBox, SGF Ranking and Tournytt monitoring are operational.
- The iBIS floorball connector has been validated during two real matches.
- Automatic Floorball Discovery is implemented and operational.
- A persistent registry contains discovered matches.
- Automatic Live Monitoring is deployed and scheduled.
- Existing golf Live Watches are preserved.
- 105 Floorball automated tests have passed.
- The existing golf regression tests have passed.
- Automatic Live execution through cron-job.org has been verified.

**Important:** Automatic floorball monitoring has not yet been fully validated during a real match.

The first real-world automatic acceptance tests are planned for 23 and 25 October 2026.

The floorball implementation has not yet been included in a confirmed new published release.

For the latest status and handover, see `PROJECT_CONTEXT.md`.

## Current Connectors

Every connector exposes the same public interface:

`fetch_snapshot(watch)`

### GolfBox Leaderboard

`connectors/golfbox_leaderboard.py`

Monitors live GolfBox competition leaderboards.

Verified with:

- Haninge Golfklubb
- Strängnäs Golfklubb
- NSGK / Hylinge
- GolfBox Tournament (`golfbox.dk`)
- Hole-by-hole live scoring
- Position changes
- Multi-round tournaments
- Round transitions
- Completed tournament results

The connector uses Playwright and Chromium.

### SGF Ranking

`connectors/sgf_ranking.py`

Monitors Swedish Golf Federation ranking data.

Verified with Daily monitoring and real ranking changes following completed competitions.

### Tournytt API

`connectors/tournytt_api.py`

Monitors Tournytt competitions through the Tournytt Server-Sent Events API.

Verified capabilities include:

- API communication
- Player lookup
- State persistence
- Change detection
- Notifications

### Swedish Floorball / iBIS

`connectors/ibis_floorball.py`

**Status: Implemented and validated – Automatic operation undergoing real-world acceptance**

Uses the Swedish Floorball / iBIS API.

Implemented capabilities include:

- Temporary API authentication
- Match retrieval through HTTP/JSON
- Match status and score monitoring
- Registered match-event monitoring
- Goals and penalties
- Period events
- Final-result notifications
- Empty-net goal handling
- Player-specific highlighting
- Stable Watch identities

Real-world match monitoring was successfully verified on 15 and 17 October 2026 using manually configured Watches.

The automatic monitoring process has been deployed but awaits full real-world match validation.

## Architecture

Event Platform separates:

- External data acquisition
- Monitoring configuration
- Snapshot comparison
- Change detection
- Notification formatting
- Notification delivery
- Persistent state
- Scheduling

Connectors own source-specific acquisition and normalization.

Notification formatting is handled separately.

Scheduling is external to the platform.

GitHub Actions executes the workflows.

cron-job.org triggers them.

### General monitoring flow

Watch configuration
→ Connector
→ External data source
→ Normalized snapshot
→ Change detection
→ Notification formatting
→ ntfy
→ Subscriber devices

Monitoring snapshots are stored in `state.json`.

### Automatic Floorball Discovery

Daily workflow
→ iBIS competition match lists
→ Team and competition filtering
→ Match discovery
→ Registry change detection
→ Git persistence

Discovered matches are stored in:

`match_registry.json`

### Automatic Live Monitoring

Live workflow
→ Load match registry
→ Select eligible matches
→ Generate runtime Watches
→ Merge with existing golf Watches
→ Retrieve connector snapshots
→ Detect changes
→ Send notifications
→ Persist changed state
→ Mark completed matches

Automatic floorball monitoring starts 15 minutes before the scheduled match time.

Completed matches are excluded from subsequent selection.

## Execution Modes

### Daily

Workflow:

`.github/workflows/daily.yml`

External scheduler:

cron-job.org

Normal schedule:

**08:00 Europe/Stockholm**

Responsibilities:

- SGF Ranking monitoring
- Automatic Floorball Discovery

The existing Daily workflow runs golf monitoring first and Floorball Discovery afterwards.

### Live

Workflow:

`.github/workflows/live.yml`

Production entry point:

`event_platform_live.py`

External scheduler:

cron-job.org

Polling interval:

**5 minutes**

The Live schedule remains enabled between events.

Runtime Watch selection determines which floorball matches are eligible.

The production Live workflow no longer uses a hard-coded MatchID.

GolfBox and Tournytt continue to be monitored through their configured Watches.

### Manual Floorball Tools

Historical manual workflows remain available during the initial automatic acceptance period.

Examples include:

- `floorball-baseline.yml`
- `floorball-daily-discovery.yml`

These are not the primary automatic production entry points.

### Regression Testing

Permanent consolidated workflow:

`.github/workflows/test-regression.yml`

The workflow verifies existing golf monitoring and runs the Floorball automated test suite.

As of 22 October 2026:

- 105 Floorball tests passed.
- Existing golf regression tests passed.

Historical standalone test-workflows remain pending cleanup.

## Automatic Floorball Monitoring

### Configured teams

Initial season: 2026/27.

| Team | TeamID | CompetitionID |
|---|---|---|
| Tyresö Trollbäcken IBK – JAS | 20872 | 45004 |
| Tyresö Trollbäcken IBK – Herrar | 4194 | 44356 |

Highlighted player:

Lukas Widegren – PlayerID `585280`.

The platform monitors the configured teams regardless of whether Lukas participates in a particular match.

### Match discovery

Discovery retrieves upcoming matches from iBIS and updates the persistent registry.

On 22 October 2026:

- 31 relevant matches were discovered.
- The registry was persisted in GitHub.
- A repeated execution detected zero changes.
- Both upcoming acceptance matches were present.

### Match selection

The Live process selects eligible matches automatically.

The initial acceptance matches are:

| Date | MatchID | Match start | Monitoring activation |
|---|---|---|---|
| 23 October 2026 | 1750707 | 19:45 | 19:30 |
| 25 October 2026 | 1703577 | 15:45 | 15:30 |

All times are Europe/Stockholm.

### Match completion

When a final result is detected, the automatic Live process is designed to:

1. Process the final observation.
2. Generate the final-result notification.
3. Persist the final snapshot.
4. Mark the match `completed`.
5. Exclude it from future monitoring.

The final snapshot and registry completion status are persisted in the same Git commit.

This functionality has passed automated tests.

Real-world automatic completion remains pending verification.

## Persistent State

Event Platform uses two persistent JSON files.

### `state.json`

Stores the latest normalized monitoring snapshot for each Watch.

Each Watch uses a stable ID.

### `match_registry.json`

Stores discovered floorball matches and monitoring lifecycle information.

Discovery owns match scheduling information.

Live owns monitoring completion status.

Git persistence merges permitted changes against the latest repository state and preserves unrelated Watches and matches.

The Live implementation includes optimistic concurrency checking.

### Known limitations

- Notification delivery is not guaranteed exactly once.
- A successful notification followed by failed Git persistence can result in a repeated notification.
- A late first floorball observation containing match activity currently causes the automatic runner to stop rather than silently discard events.
- Corrected or deleted iBIS events require further evaluation.

These limitations are tracked in `docs/backlog.md`.

## Project Structure

The following shows the main implementation and documentation files. Historical standalone test-workflows are omitted for readability.

```text
event-platform/
├── .github/
│   └── workflows/
│       ├── daily.yml
│       ├── live.yml
│       ├── floorball-daily-discovery.yml
│       ├── floorball-baseline.yml
│       └── test-regression.yml
├── connectors/
│   ├── __init__.py
│   ├── golfbox_leaderboard.py
│   ├── ibis_floorball.py
│   ├── sgf_ranking.py
│   └── tournytt_api.py
├── docs/
│   ├── ARCHITECTURE.md
│   ├── backlog.md
│   ├── decisions.md
│   ├── design-floorball.md
│   ├── design-floorball-automation.md
│   ├── design-v1.2.md
│   └── ways-of-working.md
├── tests/
│   └── test_floorball_*.py
├── PROJECT_CONTEXT.md
├── README.md
├── config.yml
├── event_platform_live.py
├── floorball_atomic_persistence.py
├── floorball_discovery.py
├── floorball_discovery_changes.py
├── floorball_git_persistence.py
├── floorball_live.py
├── floorball_match_selection.py
├── floorball_registry.py
├── floorball_registry_merge.py
├── floorball_watch_merge.py
├── match_registry.json
├── notification_formatters.py
├── requirements.txt
├── state.json
└── watcher.py
```

## Project Documentation

GitHub is the authoritative source of truth.

Start each development session by reading:

1. `PROJECT_CONTEXT.md`
2. `README.md`
3. `docs/ARCHITECTURE.md`
4. `docs/decisions.md`
5. `docs/ways-of-working.md`
6. `docs/backlog.md`

Read relevant design and implementation files as needed.

### Documentation responsibilities

- `PROJECT_CONTEXT.md` – current status and handover.
- `docs/ARCHITECTURE.md` – current architecture.
- `docs/decisions.md` – important decisions and rationale.
- `docs/backlog.md` – remaining work.
- `docs/ways-of-working.md` – development process.
- `docs/design-v1.2.md` – Unified Connector Interface design history.
- `docs/design-floorball.md` – initial Floorball investigation and validation.
- `docs/design-floorball-automation.md` – automatic Floorball design and implementation.

ChatGPT conversation history is not the project's long-term memory.

Project files or ChatGPT attachments should not be assumed to be synchronized automatically with GitHub.

## Core Design Principles

- Event Platform core remains independent of source-specific acquisition logic.
- Connectors expose `fetch_snapshot(watch)`.
- Connectors own acquisition and normalization.
- Watches use stable IDs.
- Source-specific parameters belong in `source`.
- Notification formatting is separate from acquisition.
- Scheduling remains external.
- Discovery and Live have separate responsibilities.
- Registry fields have explicit ownership.
- Unrelated Watch state must be preserved.
- Real-world acceptance remains separate from automated verification.
- Working Live Monitoring must be protected during active events.

## Development and Verification

Development follows the procedures in:

`docs/ways-of-working.md`

The preferred approach is:

1. Agree on one goal.
2. Inspect existing implementation.
3. Deliver coherent, complete changes.
4. Run appropriate verification.
5. Record the result.
6. Continue to the next increment.

For substantial changes, complete copyable files are preferred over multiple manual edits.

The permanent regression workflow should be reused rather than creating separate workflows for every test.

## Current Priorities

### Immediate

- Verify automatic Floorball Monitoring during the JAS match on 23 October.
- Verify automatic monitoring during the men's match on 25 October.
- Confirm final-result persistence and registry completion.
- Confirm the next scheduled Daily Discovery execution.

### After real-world acceptance

- Consolidate historical test-workflows.
- Preserve Python regression tests.
- Remove obsolete manual Floorball Watches.
- Review unused implementation modules.
- Confirm the scope and approval of the next release.

### Future improvements

- Notification delivery and persistence coordination.
- Late first-observation recovery.
- Corrected or deleted match events.
- Improved notification presentation.
- Configurable notification preferences.
- Additional teams, competitions and external sources.

See `docs/backlog.md` for detailed priorities.

## Releases

### v1.0.0

First production Live monitoring implementation.

### v1.1.0

Introduced:

- Multiple connectors
- Daily and Live execution modes
- SGF Ranking monitoring
- Reusable GolfBox monitoring
- Separate Daily and Live workflows

### v1.2.0

Introduced the Unified Connector Interface architecture.

Key changes:

- Common `fetch_snapshot(watch)` interface
- Connector-owned data acquisition lifecycle
- Structured Watches
- Stable Watch IDs
- Connector-specific `source` configuration
- Connector-defined normalized snapshots
- Separate notification formatting
- Generic monitoring architecture

Verified with Daily SGF Ranking, Live GolfBox and Live Tournytt.

### Development after v1.2.0

Implemented:

- Swedish Floorball / iBIS connector
- Floorball notification formatting
- Automatic match discovery
- Persistent match registry
- Automatic Live Watch selection
- Multiple Live Watches
- Coordinated Git persistence
- Automatic match completion logic
- Consolidated regression testing
- Optimized Live workflow runtime

Automatic Floorball Monitoring is deployed and undergoing real-world acceptance.

No new published release is assumed until explicitly verified and approved.

## License

Private project.
