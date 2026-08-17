# Event Platform

Event Platform is a lightweight framework for monitoring changing data from external platforms and notifying subscribers when relevant changes occur.

Golf is the first use case, but the core architecture is designed to remain independent of golf-specific logic.

## Current Status

**Current production release: v1.1.0**

The platform has been verified in real-world operation with both live event monitoring and daily monitoring.

## Current Connectors

### GolfBox Leaderboard

`connectors/golfbox_leaderboard.py`

Monitors live GolfBox competition leaderboards.

Verified with:

- Haninge Golfklubb
- Strängnäs Golfklubb
- NSGK (Hylinge)
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

External data source  
↓  
Connector  
↓  
`watcher.py`  
↓  
`state.json`  
↓  
Change detection  
↓  
ntfy  
↓  
Subscriber devices

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
│   └── sgf_ranking.py  
│  
├── docs/  
│   ├── architecture.md  
│   ├── decisions.md  
│   ├── ways-of-working.md  
│   └── backlog.md  
│  
├── .github/  
│   └── workflows/  
│       ├── daily.yml  
│       └── live.yml  
│  
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

- Event Platform core should not depend on golf-specific logic.
- Connectors acquire and normalize external data.
- The core owns state, change detection and notifications.
- Scheduling remains external to the platform.
- Prefer reusable platform-level connectors over website-specific connectors.
- Source-specific identifiers should ultimately live in configuration rather than reusable connector code.
- Verify behavior against real events where practical.

## Current Direction

The next development focus is to make adding or reusing connectors predictable and fast.

Before creating a new connector:

1. Identify the underlying external platform.
2. Determine whether an existing connector can be reused.
3. Only create a new connector when necessary.

The long-term target is that a new event on an already-supported platform should normally require configuration rather than Python changes.

See [`docs/backlog.md`](docs/backlog.md) for planned improvements.

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
