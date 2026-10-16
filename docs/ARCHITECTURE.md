# Event Platform Architecture

## Purpose

Event Platform monitors external event data, detects relevant changes, stores the latest known state, and sends notifications when something changes.

Golf was the first use case, but the platform is designed to remain independent of golf-specific or other domain-specific logic.

The architecture supports monitoring different external platforms through reusable connectors.

## Current version

Current published production release: **v1.2.0**

The platform supports two monitoring modes:

- Live event monitoring
- Daily data monitoring

Connectors included in the published release:

- `golfbox_leaderboard` – live GolfBox competition leaderboards
- `tournytt_api` – Tournytt SSE leaderboard API
- `sgf_ranking` – Swedish Golf Federation ranking data

Additional implemented connector undergoing real-world validation:

- `ibis_floorball` – Swedish floorball match monitoring through iBIS

The floorball implementation has not yet been included in a published production release.

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

Current implementations are stored in `connectors/`:

- `golfbox_leaderboard.py`
- `tournytt_api.py`
- `sgf_ranking.py`
- `ibis_floorball.py` – implemented, undergoing real-world validation

Every connector exposes the same public interface:

`fetch_snapshot(watch)`

A connector is responsible for:

- Reading its source-specific configuration from `watch["source"]`
- Owning its complete data-acquisition lifecycle
- Accessing the external source
- Finding the requested entity or data
- Normalizing the result
- Returning a connector-defined normalized snapshot or `None`

Acquisition technologies such as Playwright, HTTP, HTML parsing, JSON APIs and SSE are connector implementation details.

A connector does not own:

- State persistence
- Change detection
- Notification formatting
- Notification delivery
- Scheduling

The long-term design principle is one connector per external platform or data model where practical, rather than one connector per individual website.

For example:

`golfbox_leaderboard`

rather than separate connectors for Haninge and Strängnäs.

The GolfBox connector has been successfully validated across four real-world deployments:

- Haninge Golfklubb
- Strängnäs Golfklubb
- NSGK (Hylinge)
- GolfBox Tournament (`golfbox.dk`)

The `golfbox.dk` validation confirmed that the same connector works directly against the GolfBox Tournament site without site-specific selector or parsing changes.

### iBIS Floorball Connector

The floorball connector is implemented in:

`connectors/ibis_floorball.py`

It retrieves structured match information from the Swedish Floorball / iBIS API.

The connector:

1. Obtains a temporary access token through the iBIS startkit endpoint.
2. Validates the returned API root.
3. Retrieves the configured match using an authenticated HTTP request.
4. Verifies that the returned MatchID matches the requested match.
5. Normalizes match information and registered events.
6. Sorts events by period, match time and event ID.
7. Returns a normalized match snapshot.

The normalized snapshot contains:

- Match ID
- Competition
- Home and away teams
- Home and away TeamIDs
- Home and away MatchTeamIDs
- Match date and time
- Match status
- Final-result indicator
- Home and away goals
- Registered match events

Each normalized event includes available information such as:

- Event ID
- Event type and type ID
- MatchTeamID
- Period and match time
- Score
- Player identity
- Assist identity
- Penalty description

The connector does not interpret events for notification presentation.

That responsibility remains in the notification formatting layer.

The connector uses the same `fetch_snapshot(watch)` interface as the existing golf connectors.

### Watcher

`watcher.py` is the core execution engine.

Its responsibilities are:

- Load configuration
- Filter Watches by execution mode
- Optionally select a specific Watch using `WATCH_ID`
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

Example – Tournytt:

```yaml
id: "lukas-tournytt"
name: "Lukas Widegren - Tournytt"
connector: tournytt_api
mode: live
source:
  player: "Lukas Widegren"
  competition: 5406076
```

Example – Floorball:

```yaml
id: "floorball-match-1703572"
name: "IFK Haninge (B) - Tyresö Trollbäcken IBK (A)"
connector: ibis_floorball
mode: live
source:
  match_id: 1703572
  team_id: 4194
  highlight_player_id: 585280
```

`id` is the stable technical identity of the Watch across executions.

`name` is the human-readable name and may change without changing Watch identity.

`connector` selects the connector.

`mode` determines the execution mode.

`source` contains all connector-specific configuration.

The Event Platform core does not interpret the contents of `source`.

The selected connector owns and interprets those values.

Different connectors may therefore use different source configuration without requiring changes to the platform core.

### Watch selection

The platform supports optional Watch selection using the environment variable:

`WATCH_ID`

When configured, execution is restricted to the selected Watch.

This allows an individual Live Watch to be executed without processing other configured Watches.

The current Live workflow uses a hard-coded `WATCH_ID` value.

For the floorball match on 17 October 2026:

`WATCH_ID: floorball-match-1703572`

The configuration supports multiple Watches with independent IDs and state entries.

However, the current Live workflow is operationally configured to execute one selected Watch per run.

Supporting multiple simultaneous Live Watches without manually changing the workflow configuration remains future work.

### State

`state.json` stores the latest known state for each Watch.

Each Watch uses its stable `id` as the persistent state key.

This allows source-specific configuration and the human-readable Watch name to change without creating a new state identity.

Each active state entry contains:

- The serialized normalized snapshot used for comparison.
- The normalized snapshot fields returned by the connector.

State allows separate executions of the platform to determine whether something has changed.

GitHub Actions commits updated `state.json` back to the repository when state changes.

The workflow must account for the possibility that `main` changes while an execution is running.

#### Floorball baseline establishment

Floorball monitoring uses a dedicated workflow:

`.github/workflows/floorball-baseline.yml`

Its purpose is to establish a permanent pre-match baseline without generating notifications.

The workflow:

1. Retrieves the configured match snapshot.
2. Verifies that the match has not started.
3. Verifies that no match events or recorded goals exist.
4. Verifies that no baseline already exists for the Watch.
5. Adds the new Watch state.
6. Preserves existing state entries.
7. Synchronizes with the latest repository state before committing.
8. Commits the new baseline.

This allows a new match to be added without replacing the state of previously monitored matches or golf Watches.

The baseline workflow has been successfully used for the floorball matches on 15 and 17 October 2026.

#### Concurrent state persistence limitation

The current Live workflow saves the entire updated `state.json` file temporarily, synchronizes with `main`, and then restores that complete file before committing.

If another workflow updates state during the same period, its changes may be overwritten.

This is a known limitation of the current repository-based persistence approach.

The risk should be addressed before introducing broader concurrent Live monitoring.

### Change detection

The Event Platform core compares the current normalized snapshot returned by the connector with the previously stored snapshot for the Watch.

The core does not interpret connector-specific snapshot fields.

If the snapshots differ, the change is considered relevant and the platform can trigger a notification and persist the new state.

For Live Watches, the first real observation is normally considered an event and should generate a notification.

For Daily Watches, the first observation establishes a baseline without generating a notification.

What constitutes a valid observation is determined by the connector through the snapshot it returns or `None`.

Floorball uses a permanent pre-match baseline to prevent an unwanted initial notification containing historical or unchanged match data.

#### Floorball event detection

The floorball connector returns the complete currently available event collection.

The notification formatter compares the current event IDs with those stored in the previous snapshot.

Events with previously unseen MatchEventIDs are treated as new events.

Multiple new events can be included in one notification.

The current implementation has been verified during real-world match monitoring.

Handling of corrected or deleted events remains a future improvement.

### Notifications

Notification triggering and notification presentation are separate responsibilities.

The Event Platform core decides when a notification should be triggered based on change detection.

Connector-specific notification formatting is handled by the separate formatting layer:

`notification_formatters.py`

A notification formatter:

- Receives the relevant Watch and normalized snapshot.
- Interprets connector-specific snapshot fields.
- Creates the user-facing notification title and message.

The Event Platform core does not interpret connector-specific snapshot fields for presentation purposes.

ntfy is currently the notification provider.

The notification provider delivers the formatted notification.

The platform publishes once to an ntfy topic.

Multiple devices can subscribe to the same topic and receive the same notifications.

Future notification providers may be added without changing connector acquisition or normalization logic.

#### Floorball notification formatting

The floorball formatter receives:

- Current match snapshot
- Previous match snapshot
- Watch configuration

It produces notifications containing:

- Match identification
- Current score
- Match-status changes
- Newly registered match events
- Final result

For goals and penalties, the formatter distinguishes between the followed team and its opponent using TeamID and MatchTeamID.

Supported goal event types include:

- MatchEventTypeID 1 – Regular goal
- MatchEventTypeID 12 – Empty-net goal

Empty-net goals are labeled:

`(tom bur)`

When the event involves the followed team, the notification may include the goal scorer and assist.

Events involving the configured highlighted player are marked with a star.

The initial implementation highlights:

- Goals
- Assists
- Penalties

The first real-world match validation on 15 October 2026 confirmed delivery of goal, penalty, period and final-result notifications.

Player-specific highlighting has been technically tested but remains unverified during a real match involving a relevant player event.

## Execution modes

### Daily

Daily monitoring is intended for sources that change relatively infrequently.

Current example:

- SGF Ranking

Workflow:

`.github/workflows/daily.yml`

External schedule:

`Event Platform - Daily`

The Daily schedule normally remains enabled continuously.

### Live

Live monitoring is intended for data that changes frequently during an event.

Current use cases:

- GolfBox leaderboard
- Tournytt competitions
- Floorball matches under validation

Workflow:

`.github/workflows/live.yml`

External schedule:

`Event Platform - Live`

Current polling interval:

5 minutes.

The Live schedule should normally be enabled only while an event is active and disabled between events.

For the floorball match on 17 October 2026, the Live schedule has been enabled and automatic GitHub Actions execution verified.

### Floorball testing

Technical verification uses:

`.github/workflows/test-floorball.yml`

The tests support validation of the floorball connector and notification formatting.

Real-world match monitoring remains the primary acceptance test for live behavior.

## Scheduling

Scheduling is external to Event Platform.

cron-job.org currently triggers the GitHub Actions workflows.

This separation is intentional.

Event Platform owns monitoring logic.

The scheduler owns when that logic is executed.

This allows scheduling technology to be replaced later without redesigning the platform.

The Daily and Live schedules are managed separately.

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

## Floorball lessons learned

The first floorball implementation demonstrates that Event Platform's generic v1.2 architecture can support a non-golf data source.

The connector uses HTTP/JSON acquisition without requiring changes to the generic connector interface.

The first real-world match validation on 15 October 2026 confirmed:

- Successful live iBIS monitoring
- Goal notifications
- Penalty notifications
- Period-start and period-end notifications
- Final-result notification
- Delivery through ntfy

The validation also revealed that empty-net goals use a separate iBIS event type.

This resulted in an update to the notification formatter.

The second match validation is scheduled for 17 October 2026.

Detailed investigation, implementation and validation findings are documented in:

`docs/design-floorball.md`

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
11. Existing Watch state must be preserved when adding or changing monitoring configuration.
12. New functionality should be verified through controlled tests and real-world operation where practical.

## Future direction

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

Future floorball development should address:

- Automatic discovery of upcoming matches
- Monitoring multiple teams and competitions
- Multiple simultaneous Live Watches
- Safe concurrent state persistence
- Configurable notification preferences
- Corrected and deleted match events

These improvements should be designed before implementation and introduced without unnecessary changes to the Event Platform core.

Future architectural improvements should be driven by demonstrated needs rather than expanding the platform core with source-specific behavior.
