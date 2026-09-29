# Event Platform

Event Platform is a lightweight framework for monitoring changing data from external platforms and notifying subscribers when relevant changes occur.

Golf is the first use case, but the core architecture is designed to remain independent of golf-specific logic.

## Current Status

**Current production release: v1.2.0**

The platform has been verified in real-world operation with both live event monitoring and daily monitoring.

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

Verified with daily monitoring and real ranking changes following completed competitions.

### Tournytt API

`connectors/tournytt_api.py`

Monitors Tournytt competitions through the Tournytt Server-Sent Events (SSE) API.

Verified with:

- SSE API communication
- Player lookup
- State persistence
- Change detection
- Notifications

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

Notification formatting is handled separately from both connector acquisition and core change-detection logic.

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

Current example:

- GolfBox Leaderboard

Workflow:

`.github/workflows/live.yml`

Current polling interval:

**5 minutes**

The Live schedule is normally enabled during an event and disabled between events.

## Project Structure

event-platform/
├── connectors/
│   ├── golfbox_leaderboard.py
│   ├── sgf_ranking.py
│   └── tournytt_api.py
│
├── docs/
│   ├── architecture.md
│   ├── backlog.md
│   ├── decisions.md
│   ├── design-v1.2.md
│   └── ways-of-working.md
│
├── .github/
│   └── workflows/
│       ├── daily.yml
│       └── live.yml
│
├── PROJECT_CONTEXT.md
├── notification_formatters.py
├── watcher.py
├── config.yml
├── state.json
└── README.md

## Project Documentation

The repository documentation is the source of truth for the project.

Before starting a development session, read:

1. [`docs/architecture.md`](docs/architecture.md) – how Event Platform works today
2. [`docs/decisions.md`](docs/decisions.md) – important decisions and why they were made
3. [`docs/ways-of-working.md`](docs/ways-of-working.md) – how development sessions should be conducted
4. [`docs/backlog.md`](docs/backlog.md) – identified future work

Conversation history or AI context should not be relied upon as the project's long-term memory.

## Core Design Principles

- Event Platform core should not depend on golf-specific or other domain-specific logic.
- Connectors own external data acquisition and normalization.
- Every connector exposes the common `fetch_snapshot(watch)` interface.
- Watches use stable IDs and separate generic Watch configuration from connector-specific `source` configuration.
- The core owns state persistence, snapshot comparison, change detection and deciding when notifications should be triggered.
- Notification formatting is separate from both connector acquisition logic and core change-detection logic.
- Scheduling remains external to the platform.
- Prefer reusable platform-level connectors over website-specific connectors.
- Source-specific identifiers belong in `source` configuration rather than reusable connector code.
- Verify behavior against real events where practical.

## Current Direction

v1.2 establishes the architectural foundation for adding and reusing connectors without introducing source-specific logic into the Event Platform core.

For a new monitoring need:

1. Identify the underlying external Source.
2. Determine whether an existing connector can be reused.
3. Define the required `source` configuration.
4. If necessary, implement a new connector using `fetch_snapshot(watch)`.
5. Define the notification formatter for the connector.
6. Create the Watch with a stable Watch ID.
7. Establish or migrate state as required.
8. Verify change detection and notifications.
9. Enable the appropriate execution schedule.

The target is that a new event on an already-supported Source should normally require Watch configuration changes only.

See [`docs/backlog.md`](docs/backlog.md) for identified future improvements.

## Releases

### v1.0.0

First production live-monitoring implementation.

### v1.1.0

Introduced:

- Multiple connectors
- Daily and Live execution modes
- SGF Ranking monitoring
- Reusable GolfBox leaderboard monitoring
- Separate Daily and Live workflows

## License

Private project.
