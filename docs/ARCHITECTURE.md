# Event Platform Architecture

## Purpose

Event Platform monitors external event data, detects relevant changes, stores the latest known state, and sends notifications when something changes.

Golf is the first use case, but the platform should not depend on golf-specific logic.

## Current version

Current production release: v1.1.0

The platform currently supports two types of monitoring:

- Live event monitoring
- Daily data monitoring

Current connectors:

- `golfbox_leaderboard` – live GolfBox competition leaderboards
- `sgf_ranking` – Swedish Golf Federation ranking data

## High-level flow

External data source
→ Connector
→ `watcher.py`
→ Compare with `state.json`
→ Detect change
→ ntfy
→ Subscriber devices

GitHub Actions executes the platform.

cron-job.org triggers the GitHub Actions workflows.

## Components

### Connectors

Connectors are responsible for acquiring and normalizing data from an external platform.

Current connectors are stored in:

`connectors/`

Current implementations:

- `golfbox_leaderboard.py`
- `sgf_ranking.py`
- - tournytt_api.py (validation in progress)

A connector should return structured data to the platform.

A connector should not own:

- State
- Change detection
- Notification delivery
- Scheduling

The long-term design principle is one connector per external platform or data model where practical, rather than one connector per individual website.

Example:

`golfbox_leaderboard`

rather than:

`haninge`
`strangnas`

The GolfBox connector has been successfully tested against leaderboards hosted by both Haninge Golfklubb and Strängnäs Golfklubb.

### Watcher

`watcher.py` is the core execution engine.

Its responsibilities are:

- Load configuration
- Select the correct connector
- Fetch the current state
- Compare current state with previous state
- Detect changes
- Send notifications
- Update persistent state

Golf-specific data acquisition should remain inside connectors rather than the watcher.

### Configuration

`config.yml` defines watches.

A watch currently specifies information such as:

- `name`
- `connector`
- `mode`
- `player`
- connector-specific parameters such as competition identifiers

Connectors may require different parameters.

The platform should not require every connector to use the same source-specific configuration.

### State

`state.json` stores the latest known state for each watch.

State allows separate executions of the platform to determine whether something has changed.

Live and daily watches use separate state keys.

GitHub Actions commits updated `state.json` back to the repository when state changes.

### Change detection

The platform compares the current connector snapshot with the previously stored snapshot.

If the snapshots differ, the platform can send a notification and store the new state.

For live watches, the first real result is considered an event and should generate a notification.

For daily monitoring, the first observation establishes a baseline without generating a notification.

### Notifications

ntfy is currently the notification provider.

The platform publishes once to an ntfy topic.

Multiple devices can subscribe to the same topic and receive the same notifications.

Future notification providers may be added without changing connector logic.

## Execution modes

### Daily

Daily monitoring is intended for sources that change relatively infrequently.

Current example:

- SGF Ranking

Workflow:

`.github/workflows/daily.yml`

External schedule:

`Event Platform - Daily`

The Daily schedule remains enabled continuously.

### Live

Live monitoring is intended for data that changes frequently during an event.

Current example:

- GolfBox leaderboard

Workflow:

`.github/workflows/live.yml`

External schedule:

`Event Platform - Live`

Current polling interval:

5 minutes

The Live schedule should normally be enabled only while an event is active and disabled between events.

## Scheduling

Scheduling is external to Event Platform.

cron-job.org currently triggers the GitHub Actions workflows.

This separation is intentional.

Event Platform owns monitoring logic.

The scheduler owns when that logic is executed.

This allows the scheduling technology to be replaced later without redesigning the platform.

## GolfBox lessons learned

GolfBox competitions may contain multiple leaderboard classes.

A competition identifier alone may therefore not uniquely identify the desired leaderboard.

The leaderboard identifier is also relevant.

GolfBox player names may appear in different formats, for example:

`Lukas Widegren`

or:

`WIDEGREN, Lukas`

The connector should handle these variations.

The GolfBox leaderboard changes structure during the lifecycle of an event.

The current connector has successfully handled:

- Empty leaderboard before play
- First live result
- Hole-by-hole live scoring
- Position changes caused by other players
- Completion of round 1
- Transition into round 2
- Hole-by-hole scoring in round 2
- Completed two-round tournament

## Design principles

1. Event Platform core should not depend on golf-specific logic.
2. Connectors own external data acquisition and normalization.
3. The core owns state, change detection and notifications.
4. Scheduling remains external to the platform.
5. Prefer platform-level connectors over website-specific connectors where the underlying technology is shared.
6. Different monitoring needs may use different execution modes and schedules.
7. Configuration should contain source-specific identifiers rather than hard-coding them inside reusable connectors.

## Future direction

The next architectural goal is to make adding a new connector predictable and fast.

A future connector should ideally require:

1. Identify the underlying external platform.
2. Determine whether an existing connector can be reused.
3. If necessary, implement a new connector using a standard interface.
4. Add configuration.
5. Establish a baseline.
6. Verify change detection.
7. Enable the appropriate schedule.

The target is for future connectors to require configuration rather than platform-core changes whenever possible.
