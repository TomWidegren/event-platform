# Event Platform Architecture

## Purpose

Event Platform monitors external event data, detects relevant changes, stores the latest known state, and sends notifications when something changes.

Golf is the first use case, but the platform should not depend on golf-specific logic.

## Current version

Current production release: v1.2.0

The platform currently supports two types of monitoring:

- Live event monitoring
- Daily data monitoring

Current connectors:

- `golfbox_leaderboard` – live GolfBox competition leaderboards
- `tournytt_api` – Tournytt SSE leaderboard API
- `sgf_ranking` – Swedish Golf Federation ranking data

## High-level flow

Watch configuration
→ Connector
→ External data source
→ Normalized snapshot
→ `watcher.py`
→ Compare with Watch state in `state.json`
→ Detect change
→ Notification formatter
→ ntfy
→ Subscriber devices

Each connector owns its complete data-acquisition lifecycle.

`watcher.py` remains independent of connector-specific acquisition technology and snapshot fields.

GitHub Actions executes the platform.

cron-job.org triggers the GitHub Actions workflows.

## Components

### Connectors

Connectors are responsible for acquiring and normalizing data from an external platform.

Current connectors are stored in:

`connectors/`

Current implementations:

- `golfbox_leaderboard.py`
- `tournytt_api.py`
- `sgf_ranking.py`

Every connector exposes the same public interface:

`fetch_snapshot(watch)`

A connector is responsible for:

- Reading its source-specific configuration from `watch["source"]`
- Owning its complete data-acquisition lifecycle
- Accessing the external source
- Finding the requested entity or data
- Normalizing the result
- Returning a connector-defined normalized snapshot or `None`

Acquisition technologies such as Playwright, HTTP and SSE are connector implementation details.

A connector does not own:

- State persistence
- Change detection
- Notification formatting
- Notification delivery
- Scheduling

The long-term design principle is one connector per external platform or data model where practical, rather than one connector per individual website.

Example:

`golfbox_leaderboard`

rather than:

`haninge`
`strangnas`

The GolfBox connector has been successfully validated across four real-world GolfBox deployments:

- Haninge Golfklubb
- Strängnäs Golfklubb
- NSGK (Hylinge)
- GolfBox Tournament (`golfbox.dk`)

The `golfbox.dk` validation confirmed that the same connector works directly against the GolfBox Tournament site, without site-specific selector or parsing changes.

### Watcher

`watcher.py` is the core execution engine.

Its responsibilities are:

- Load configuration
- Filter Watches by execution mode
- Select the configured connector
- Call `fetch_snapshot(watch)`
- Compare the returned snapshot with persistent state
- Detect changes
- Decide when a notification should be triggered
- Invoke the notification formatting layer
- Deliver notifications through the configured notification provider
- Update persistent state

`watcher.py` does not:

- Manage connector acquisition technologies such as Playwright, HTTP or SSE
- Interpret source-specific configuration inside `watch["source"]`
- Interpret connector-specific snapshot fields for presentation

Source-specific acquisition and normalization remain inside connectors.

Connector-specific notification presentation remains inside the notification formatting layer.

### Configuration

`config.yml` defines Watches.

Every Watch uses the generic structure:

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

`id` is the stable technical identity of the Watch across executions.

`name` is the human-readable name and may change without changing Watch identity.

`connector` selects the connector.

`mode` determines the execution mode.

`source` contains all connector-specific configuration.

The Event Platform core does not interpret the contents of `source`. The selected connector owns and interprets those values.

Different connectors may therefore use completely different source configuration without requiring changes to the platform core.

### State

`state.json` stores the latest known state for each Watch.

Each Watch uses its stable `id` as the persistent state key.

This allows source-specific configuration and the human-readable Watch name to change without creating a new state identity.

Each active state entry contains:

- the serialized normalized snapshot used for comparison,
- the normalized snapshot fields returned by the connector.

State allows separate executions of the platform to determine whether something has changed.

GitHub Actions commits updated `state.json` back to the repository when state changes.

The workflow must account for the possibility that `main` changes while an execution is running.

### Change detection

The Event Platform core compares the current normalized snapshot returned by the connector with the previously stored snapshot for the Watch.

The core does not interpret connector-specific snapshot fields.

If the snapshots differ, the change is considered relevant and the platform can trigger a notification and persist the new state.

For Live Watches, the first real observation is considered an event and should generate a notification.

For Daily Watches, the first observation establishes a baseline without generating a notification.

What constitutes a valid observation is determined by the connector through the snapshot it returns or `None`.

### Notifications

Notification triggering and notification presentation are separate responsibilities.

The Event Platform core decides when a notification should be triggered based on change detection.

Connector-specific notification formatting is handled by the separate notification formatting layer.

A notification formatter:

- receives the relevant Watch and normalized snapshot,
- interprets connector-specific snapshot fields,
- creates the user-facing notification title and message.

The Event Platform core does not interpret connector-specific snapshot fields for presentation purposes.

ntfy is currently the notification provider.

The notification provider is responsible for delivering the formatted notification.

The platform publishes once to an ntfy topic.

Multiple devices can subscribe to the same topic and receive the same notifications.

Future notification providers may be added without changing connector acquisition or normalization logic.

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

A multi-round event may use the `hole` field for different purposes during its lifecycle:

- Before a round starts, it may contain the scheduled start time.
- During a round, it contains the current hole.
- After the tournament is complete, it contains `F`.

During multi-round events:

- Completed round scores are populated in the corresponding round fields.
- `today` represents the current round.
- `topar` represents the accumulated tournament score relative to par.
- `total` represents the accumulated stroke total.

The current connector has successfully handled:

- Empty leaderboard before play
- First live result
- Hole-by-hole live scoring
- Position changes caused by other players
- Completion of round 1
- Transition into round 2
- Hole-by-hole scoring in round 2
- Completed two-round tournament

## Tournytt lessons learned

Tournytt exposes leaderboard data through a Server-Sent Events (SSE) API rather than requiring HTML scraping.

The connector communicates directly with the API and receives structured JSON.

Observed behavior:

- Player entries are published before play starts.
- Baseline creation therefore differs from GolfBox.
- Leaderboard updates are published through the API.
- State persistence and change detection work with the current implementation.

The current connector has successfully demonstrated:

- API communication
- Player lookup
- State persistence
- Change detection
- Notifications

Notification formatting should be improved to better present Tournytt-specific fields.

## Design principles

1. Event Platform core should not depend on golf-specific or other domain-specific logic.
2. Connectors own external data acquisition and normalization.
3. Connectors own their complete acquisition lifecycle and expose the common `fetch_snapshot(watch)` interface.
4. The core owns state persistence, snapshot comparison, change detection and deciding when notifications should be triggered.
5. Notification formatting is separate from both connector acquisition logic and core change-detection logic.
6. Scheduling remains external to the platform.
7. Prefer platform-level connectors over website-specific connectors where the underlying technology is shared.
8. Watches use stable IDs and separate generic Watch configuration from connector-specific `source` configuration.
9. Different monitoring needs may use different execution modes and schedules.
10. Source-specific identifiers belong in `source` configuration rather than being hard-coded inside reusable connectors.

## Future direction

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

Future architectural improvements should be driven by demonstrated needs rather than expanding the platform core with source-specific behavior.
