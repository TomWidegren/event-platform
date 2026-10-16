# Event Platform

Event Platform is a lightweight framework for monitoring changing data from external platforms and notifying subscribers when relevant changes occur.

Golf was the first use case, but the core architecture is designed to remain independent of golf-specific or other domain-specific logic.

The platform now also supports floorball monitoring through an implemented connector undergoing real-world validation.

## Current Status

**Current production release: v1.2.0**

The platform has been verified in real-world operation with both Live and Daily monitoring.

The current published release supports GolfBox, SGF Ranking and Tournytt.

An additional connector for Swedish floorball (iBIS) has been implemented and successfully used during its first real-world match validation on 15 October 2026.

A second floorball validation is prepared for 17 October 2026.

The floorball implementation has not yet been included in a published production release.

For the latest development status, see `PROJECT_CONTEXT.md`.

## Current Connectors

### GolfBox Leaderboard

`connectors/golfbox_leaderboard.py`

Monitors live GolfBox competition leaderboards.

Verified with:

- Haninge Golfklubb
- Strängnäs Golfklubb
- NSGK (Hylinge)
- GolfBox Tournament (`golfbox.dk`)
- Hole-by-hole live scoring
- Position changes
- Multi-round tournaments
- Transition between rounds
- Completed tournament results

### SGF Ranking

`connectors/sgf_ranking.py`

Monitors Swedish Golf Federation ranking data.

Verified with Daily monitoring and real ranking changes following completed competitions.

### Tournytt API

`connectors/tournytt_api.py`

Monitors Tournytt competitions through the Tournytt Server-Sent Events (SSE) API.

Verified with:

- SSE API communication
- Player lookup
- State persistence
- Change detection
- Notifications

### Swedish Floorball / iBIS

`connectors/ibis_floorball.py`

**Status: Implemented – Real-world validation ongoing**

Monitors individual floorball matches using the Swedish Floorball / iBIS API.

Implemented capabilities:

- Temporary API authentication
- Match data retrieval through HTTP/JSON
- Match status and score monitoring
- Registered match-event monitoring
- Goal and penalty notifications
- Period-start and period-end notifications
- Final-result notifications
- Empty-net goal handling
- Player-specific highlighting
- Permanent pre-match baseline
- Stable Watch IDs

The first real-world validation was successfully completed on 15 October 2026.

A second validation is prepared for 17 October 2026.

Automatic match discovery and multi-match monitoring remain future development opportunities.

Detailed implementation and validation information is available in `docs/design-floorball.md`.

## Architecture

High-level flow:

Watch configuration  
↓  
Connector  
↓  
External data source  
↓  
Normalized snapshot  
↓  
`watcher.py`  
↓  
State comparison and change detection  
↓  
Notification formatter  
↓  
ntfy  
↓  
Subscriber devices

Every connector exposes the common interface:

`fetch_snapshot(watch)`

Connectors own source-specific acquisition and normalization.

`watcher.py` remains independent of connector-specific acquisition technology and snapshot fields.

Notification formatting is handled separately from connector acquisition and core change-detection logic.

Execution is triggered externally by cron-job.org.

GitHub Actions runs Event Platform.

## Execution Modes

### Daily

Used for relatively slow-changing data.

Current example:

- SGF Ranking

Workflow:

`.github/workflows/daily.yml`

The Daily schedule normally remains enabled continuously.

### Live

Used during active events.

Current use cases:

- GolfBox Leaderboard
- Tournytt
- Floorball

Workflow:

`.github/workflows/live.yml`

Current polling interval:

**5 minutes**

The Live schedule is normally enabled during an event and disabled between events.

The workflow supports optional selection of an individual Watch through the `WATCH_ID` environment variable.

The current Live workflow is configured to execute one selected Watch per run.

### Floorball Baseline

Workflow:

`.github/workflows/floorball-baseline.yml`

Establishes a permanent pre-match baseline without generating notifications.

The workflow preserves existing Watch state.

### Floorball Testing

Workflow:

`.github/workflows/test-floorball.yml`

Supports technical verification of the floorball implementation.

## Project Structure

```text
event-platform/
├── .github/
│   └── workflows/
│       ├── daily.yml
│       ├── floorball-baseline.yml
│       ├── live.yml
│       └── test-floorball.yml
│
├── connectors/
│   ├── __init__.py
│   ├── golfbox_leaderboard.py
│   ├── ibis_floorball.py
│   ├── sgf_ranking.py
│   └── tournytt_api.py
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ROADMAP.md
│   ├── backlog.md
│   ├── decisions.md
│   ├── design-floorball.md
│   ├── design-v1.2.md
│   └── ways-of-working.md
│
├── tests/
│   └── test_floorball_formatting.py
│
├── PROJECT_CONTEXT.md
├── README.md
├── config.yml
├── notification_formatters.py
├── requirements.txt
├── state.json
└── watcher.py
```

`docs/ROADMAP.md` is a legacy document from the original Golf Watcher project. It is no longer the active source for development priorities.

Relevant future development ideas are maintained in `docs/backlog.md`.

## Project Documentation

The repository documentation is the source of truth.

**Start every new development session by reading `PROJECT_CONTEXT.md`.**

This file identifies the current production release, ongoing development, latest verified results and recommended next steps.

Additional documentation:

1. `docs/ARCHITECTURE.md` – how Event Platform works today.
2. `docs/decisions.md` – important decisions and their rationale.
3. `docs/ways-of-working.md` – development process, session management and ChatGPT conversation lifecycle.
4. `docs/backlog.md` – identified future work.
5. `docs/design-v1.2.md` – design history for the Unified Connector Interface.
6. `docs/design-floorball.md` – floorball investigation, implementation and validation.

ChatGPT conversation history is not considered the project's long-term memory.

Development should be resumable from the repository documentation without requiring access to earlier conversations.

## Core Design Principles

- Event Platform core should not depend on golf-specific or other domain-specific logic.
- Connectors own external data acquisition and normalization.
- Every connector exposes the common `fetch_snapshot(watch)` interface.
- Watches use stable IDs and separate generic Watch configuration from connector-specific `source` configuration.
- The core owns state persistence, snapshot comparison, change detection and notification triggering.
- Notification formatting is separate from both connector acquisition and core change-detection logic.
- Scheduling remains external to the platform.
- Prefer reusable platform-level connectors over website-specific connectors.
- Source-specific identifiers belong in `source` configuration rather than reusable connector code.
- Preserve existing Watch state when introducing new monitoring configuration.
- Verify behavior against real events where practical.

## Current Direction

v1.2 establishes the architectural foundation for adding and reusing connectors without introducing source-specific logic into the Event Platform core.

For a new monitoring need:

1. Identify the underlying external source.
2. Determine whether an existing connector can be reused.
3. Define the required `source` configuration.
4. If necessary, implement a new connector using `fetch_snapshot(watch)`.
5. Define the notification formatter for the connector.
6. Create the Watch with a stable Watch ID.
7. Establish or migrate state as required.
8. Verify change detection and notifications.
9. Enable the appropriate execution schedule.

The target is that a new event on an already-supported source should normally require Watch configuration changes only.

Current development focuses on validating and generalizing floorball monitoring.

Potential next improvements include:

- Automatic discovery of upcoming floorball matches
- Monitoring multiple teams and competitions
- Multiple simultaneous Live Watches
- Safer concurrent state persistence
- Improved notification presentation
- Configurable notification preferences

See `docs/backlog.md` for the complete list of identified future work.

## Releases

### v1.0.0

First production Live monitoring implementation.

### v1.1.0

Introduced:

- Multiple connectors
- Daily and Live execution modes
- SGF Ranking monitoring
- Reusable GolfBox leaderboard monitoring
- Separate Daily and Live workflows

### v1.2.0

Introduced the Unified Connector Interface architecture.

Key changes:

- Common connector interface: `fetch_snapshot(watch)`
- Connector-owned data acquisition lifecycle
- Structured Watches using `id`, `name`, `connector`, `mode` and `source`
- Stable Watch IDs for state persistence
- Connector-specific configuration under `source`
- Connector-defined normalized snapshots
- Separate notification formatting layer
- Generic Event Platform core without connector-specific acquisition or presentation logic
- SGF Ranking source configuration moved out of hard-coded connector values
- GolfBox source configuration moved out of event-specific connector values

Verified with:

- Daily SGF Ranking monitoring
- Live GolfBox monitoring
- Live Tournytt monitoring
- State persistence across executions
- Change detection
- Notification formatting and delivery through ntfy

### Development after v1.2.0

Floorball monitoring through iBIS has been implemented and is undergoing real-world validation.

This functionality is not yet part of a published production release.

Future releases will be created deliberately after the relevant capabilities have been verified.

## License

Private project.
