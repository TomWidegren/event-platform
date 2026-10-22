
# Event Platform – Decisions

This document records important architectural and operational decisions for Event Platform and why they were made.

It is not a description of the current architecture. See `ARCHITECTURE.md` for that.

Decisions should only be changed deliberately. When a decision is superseded, the original decision and its historical context should remain identifiable.

---

## D001 – Event Platform is the product name

**Decision**

The project is called Event Platform.

**Reason**

Golf was the first use case, but the architecture should support other types of events and data sources in the future.

---

## D002 – Connectors represent platforms where practical

**Decision**

Prefer connectors for underlying platforms or data models rather than individual websites.

Examples:

- `golfbox_leaderboard`
- `sgf_ranking`

rather than:

- `haninge`
- `strangnas`

**Reason**

Haninge Golfklubb and Strängnäs Golfklubb both use GolfBox technology. The same connector concept can therefore be reused.

Before creating a new connector, first determine whether the source uses a platform we already support.

---

## D003 – Connectors only acquire and normalize data

**Decision**

Connectors are responsible for:

- Accessing an external source
- Finding the requested entity
- Extracting relevant data
- Returning a normalized snapshot

Connectors are not responsible for:

- State persistence
- Change detection
- Notifications
- Scheduling

**Reason**

This keeps connectors reusable and separates source-specific logic from platform logic.

---

## D004 – Core owns state and change detection

**Decision**

The Event Platform monitoring layer owns:

- Configuration loading
- Connector selection
- Snapshot comparison
- Change detection
- Notification triggering
- State updates

`watcher.py` provides the generic monitoring implementation.

Automatic Live execution is coordinated separately through `event_platform_live.py`, which reuses existing connectors, notification formatting and monitoring conventions.

**Reason**

All connectors should benefit from common monitoring behavior without implementing it themselves.

The separate Live execution layer allows automatic match selection and coordinated Git persistence without introducing floorball-specific acquisition logic into the generic watcher.

**Updated:** 22 October 2026.

---

## D005 – Scheduling is external

**Decision**

Event Platform does not own its scheduler.

cron-job.org currently triggers GitHub Actions.

**Reason**

Scheduling and monitoring are separate responsibilities.

The scheduler can therefore be replaced later without redesigning connectors or the platform core.

---

## D006 – Daily and Live are separate execution modes

**Decision**

The platform supports:

- `daily`
- `live`

Daily is used for relatively slow-changing sources and automatic discovery.

Live is used for frequently changing event data.

**Reason**

Different sources require different polling frequencies and operational behavior.

---

## D007 – Live polling interval is five minutes

**Decision**

Live monitoring runs every five minutes.

The external Live schedule remains enabled continuously, while runtime Watch selection determines which floorball matches are eligible for monitoring.

**Reason**

Five minutes provides useful live updates.

Automatic Watch selection removes the need to manually enable and disable the scheduler for individual floorball matches.

**Updated:** 22 October 2026.

---

## D008 – Daily monitoring remains enabled

**Decision**

Daily monitoring runs continuously once per day.

Current responsibilities include:

- SGF Ranking
- Automatic floorball match discovery

**Reason**

Ranking changes relatively infrequently.

Floorball schedules can also be refreshed daily without continuous polling.

Both functions can reuse the existing reliable Daily schedule.

**Updated:** 22 October 2026.

---

## D009 – First observation behaves differently for Daily and Live

**Decision**

For Daily:

The first observation establishes a baseline without sending a notification.

For golf Live monitoring:

The first valid event result establishes the baseline and may generate a notification.

An empty or not-yet-started leaderboard is not considered a real result.

For floorball Live monitoring:

The first pre-match observation establishes a baseline without notification.

If the first observation already contains match activity, the current automatic Live runner rejects the late baseline rather than silently discarding events.

**Reason**

Different sources have different event lifecycles.

Floorball monitoring requires a known baseline to distinguish new match events from historical events.

Late-baseline recovery remains future work.

**Updated:** 22 October 2026.

---

## D010 – Position changes are relevant Live changes

**Decision**

A Live notification may be generated when the watched player's position changes even if the player's own score has not changed.

**Reason**

Other competitors' results can change the player's leaderboard position.

This is considered meaningful live information.

A future notification preference may allow users to choose between all changes and player-score-only changes.

---

## D011 – State is persisted in the repository

**Decision**

`state.json` stores the latest known monitoring snapshots.

GitHub Actions commits changed state back to the repository.

The automatic Live implementation merges changed Watch entries against the latest repository state rather than blindly replacing the complete state file.

**Reason**

GitHub Actions runners are stateless.

Persistent state is required to compare independent executions.

The implementation must preserve unrelated Watches and protect against concurrent updates.

**Updated:** 22 October 2026.

---

## D012 – Source-specific parameters belong in configuration

**Decision**

Reusable connectors should not permanently hard-code event-specific identifiers.

Examples include:

- Competition ID
- Leaderboard ID
- Player
- Team
- Other source-specific identifiers

These belong in configuration or dynamically generated Watch configuration.

**Reason**

A reusable connector should ideally support the next event without Python changes.

---

## D013 – Verify behavior with real events where practical

**Decision**

Prefer real-world validation over artificial state manipulation when practical.

Automated tests remain necessary but do not replace operational verification.

**Reason**

The Haninge, Strängnäs and floorball validations revealed behavior that would have been difficult to predict from static testing alone.

Examples include:

- Changing leaderboard layouts
- Multiple competition classes
- Live position changes
- Round transitions
- Final result population
- Floorball event types and MatchTeamID handling

---

## D014 – Do not change a working live system during an event without need

**Decision**

Once a live event is working correctly, avoid nonessential code changes until the event is complete.

**Reason**

A live event provides valuable real-world validation and unnecessary changes introduce avoidable risk.

---

## D015 – Documentation is the project's long-term memory

**Decision**

Important architecture, decisions, ways of working and backlog items are stored in the repository.

Chat history or AI conversational context is not considered the project's source of truth.

**Reason**

Conversation context is finite.

Repository documentation allows future development sessions to reconstruct the necessary project context reliably.

---

## D016 – Unified Connector Interface

**Decision**

All Event Platform connectors use the same public interface:

`fetch_snapshot(watch)`

A Watch has the generic structure:

- `id`
- `name`
- `connector`
- `mode`
- `source`

`id` is the stable technical identity of the Watch across executions.

The Watch `id` must remain stable once the Watch has persistent state.

Human-readable `name` and source-specific configuration may change without changing Watch identity.

The Event Platform core understands the generic Watch structure but does not interpret the contents of `source`.

The selected connector owns and interprets everything inside `source`, including:

- The monitored entity
- Source-specific identifiers
- Source-specific configuration

Examples may include:

- Player
- Team
- Competition ID
- Leaderboard ID
- Other future source-specific parameters

Each connector owns its complete data-acquisition lifecycle.

Acquisition technologies such as:

- Playwright
- HTTP
- HTML parsing
- JSON APIs
- Server-Sent Events (SSE)
- Future source-specific technologies

are connector implementation details and are not managed by the Event Platform core.

A connector returns either:

- A connector-defined normalized snapshot
- `None` when no relevant observation is available

The snapshot does not use a fixed platform-wide field schema.

Each connector defines a stable normalized snapshot appropriate to its external source and Watch.

The Event Platform monitoring layer owns:

- Connector selection
- State persistence using the Watch `id`
- Snapshot comparison
- Change detection
- Deciding when a notification should be triggered

Notification formatting is handled by a separate formatting layer.

Notification formatters:

- Interpret connector-specific snapshot fields
- Create user-facing notification content
- Remain separate from connector acquisition logic and monitoring logic

The notification provider is responsible for delivering the formatted notification.

**Reason**

This creates stable boundaries between the Event Platform monitoring layer, source-specific connectors and notification presentation.

The architecture remains independent of:

- Acquisition technology
- Monitored entity type
- Source-specific configuration
- Connector-specific snapshot fields
- Connector-specific notification presentation

Stable Watch IDs allow source configuration and human-readable names to evolve without creating new state baselines.

Separating notification formatting allows presentation to evolve without adding source-specific interpretation to connectors or the generic monitoring engine.

New connectors and future non-golf use cases can therefore be introduced without expanding the platform core with source-specific concepts.

The original design was derived from real-world experience with GolfBox, SGF Ranking and Tournytt and is documented in detail in `design-v1.2.md`.

---

## D017 – Floorball match discovery is separate from Live monitoring

**Decision**

Automatic floorball match discovery and Live monitoring are separate responsibilities.

Discovery:

- Retrieves upcoming matches.
- Identifies matches for configured teams.
- Maintains scheduling information.
- Registers new matches.
- Updates existing match schedules.

Live:

- Selects eligible registered matches.
- Retrieves match observations.
- Detects changes.
- Generates notifications.
- Updates monitoring lifecycle.

**Reason**

Match discovery and match monitoring operate at different frequencies and have different responsibilities.

Separating them prevents unnecessary discovery calls during frequent Live polling and avoids mixing scheduling changes with match-event processing.

**Date:** 22 October 2026.

---

## D018 – Match registry is persistent and separate from Watch state

**Decision**

Floorball matches are stored in:

`match_registry.json`

Monitoring snapshots remain stored in:

`state.json`

The registry uses stable iBIS MatchIDs as keys.

**Reason**

The match registry describes which matches exist and when they should be monitored.

Watch state describes what has been observed during monitoring.

These are different concerns and should remain separate.

The registry also allows monitoring to resume across independent GitHub Actions executions.

**Date:** 22 October 2026.

---

## D019 – Discovery and Live have explicit registry ownership

**Decision**

Discovery owns match identity, scheduling and source scheduling information.

Live owns monitoring lifecycle and completion status.

Updates are merged according to these ownership boundaries.

Discovery must not reactivate completed matches.

Live must not modify Discovery-owned scheduling information or create unknown matches implicitly.

**Reason**

Daily Discovery and Live Monitoring may update the same registry at different times.

Explicit ownership prevents one process from unintentionally overwriting another process's information.

**Date:** 22 October 2026.

---

## D020 – Automatic Live Watches replace manually selected floorball Watches

**Decision**

Live Monitoring dynamically generates floorball Watches from the persistent match registry.

Manually configured floorball Watches are excluded from the automatic Live configuration.

Existing non-floorball Live Watches, including GolfBox and Tournytt, are preserved.

Generated Watch IDs use:

`floorball-match-{match_id}`

**Reason**

Manual MatchID selection required workflow changes before each match.

Dynamic Watch generation allows new matches to be monitored without manually editing `config.yml` or `live.yml`.

It also avoids duplicate monitoring of the same match through manual and automatic Watches.

**Date:** 22 October 2026.

---

## D021 – Floorball monitoring starts before scheduled match time

**Decision**

An eligible floorball match enters its automatic Live monitoring window 15 minutes before its scheduled start.

Cancelled, postponed and completed matches are excluded according to the match-selection rules.

The selection logic supports multiple simultaneous matches.

**Reason**

Starting before the scheduled match time allows the platform to establish a pre-match baseline.

This reduces the risk of treating historical match events as new notifications.

The exact activation behavior has been verified through simulated-time tests.

**Date:** 22 October 2026.

---

## D022 – Reuse the existing Daily schedule for Discovery

**Decision**

Automatic Floorball Discovery executes after the existing Daily golf monitoring within `daily.yml`.

The existing cron-job.org Daily schedule is reused.

No additional scheduler or external cron-job is introduced.

**Reason**

The existing Daily schedule has demonstrated reliable operation.

Reusing it reduces operational complexity and avoids unnecessary scheduling infrastructure.

The two functions remain separate Python implementations.

**Date:** 22 October 2026.

---

## D023 – Automatic Live uses the existing Live workflow and scheduler

**Decision**

The existing `.github/workflows/live.yml` is the production Live workflow.

It executes:

`event_platform_live.py`

The previous hard-coded `WATCH_ID` is removed.

The existing cron-job.org Live job is reused with a five-minute polling interval.

**Reason**

One Live workflow can process both existing golf Watches and dynamically selected floorball Watches.

There is no need to create a separate Live scheduler for floorball.

**Date:** 22 October 2026.

---

## D024 – Preserve unrelated state and reject stale same-Watch updates

**Decision**

Automatic Live persistence refreshes the latest Git repository state before committing.

Only changed Watch entries are merged.

Unrelated Watch entries must be preserved.

Optimistic concurrency checking compares the state used for observation with the latest persisted state.

If another execution has changed the same Watch, the stale update is rejected rather than blindly overwriting newer state.

**Reason**

GitHub Actions executions operate independently.

A complete-file overwrite could lose changes made by another execution.

The merge and conflict-detection approach reduces this risk.

The concurrency protection has passed regression tests, while broader real-world concurrent execution remains an operational validation area.

**Date:** 22 October 2026.

---

## D025 – Completed floorball matches use coordinated persistence

**Decision**

When a final floorball result is detected, the final Watch snapshot and registry completion status are persisted together in one Git commit.

The final snapshot is stored in `state.json`.

The match is marked `completed` in `match_registry.json`.

Completed matches must not be automatically reactivated.

**Reason**

The final monitoring observation and the monitoring lifecycle must remain consistent.

Atomic Git persistence prevents a successful commit from containing only one of the two related updates.

The underlying functionality has passed automated tests.

Automatic completion during a real match remains pending verification.

**Date:** 22 October 2026.

---

## D026 – Notification delivery is not guaranteed exactly once

**Decision**

The current automatic Live implementation sends notifications before committing the corresponding state changes to Git.

Exactly-once delivery is not guaranteed.

If notification delivery succeeds but persistence fails, the same event may be notified again during a later execution.

**Reason**

ntfy delivery and Git persistence are independent operations.

Git commits cannot atomically include an external notification delivery.

This limitation is accepted for the current implementation and must remain documented.

A more advanced delivery coordination mechanism may be considered if operational experience demonstrates a need.

**Date:** 22 October 2026.

---

## D027 – Coordinate production workflows through GitHub Actions concurrency

**Decision**

Participating Daily and Live workflows use the concurrency group:

`event-platform-state`

With:

`cancel-in-progress: false`

**Reason**

The workflows may update persistent files in the same repository.

Serializing participating executions reduces overlapping Git updates.

Git persistence retains its own conflict-detection and retry mechanisms.

**Date:** 22 October 2026.

---

## D028 – Retain Playwright for GolfBox but optimize installation

**Decision**

The GolfBox connector continues to use Playwright and Chromium.

The Live workflow installs Python dependencies and Chromium without running the full Playwright operating-system dependency installation on every execution.

**Reason**

GolfBox requires browser automation.

However, repeatedly installing and upgrading system packages caused excessive GitHub Actions runtime.

The optimized workflow reduced a measured execution from 4 minutes 20 seconds to approximately 37 seconds.

A subsequent automatically triggered execution completed in approximately 30 seconds.

This provides sufficient operational margin for the current five-minute polling interval under observed conditions.

**Date:** 22 October 2026.

---

## D029 – Consolidate automated regression testing

**Decision**

Use the permanent workflow:

`.github/workflows/test-regression.yml`

for consolidated regression testing.

Retain the Python test files in `tests/`.

Historical standalone test-workflows may be removed after confirming they are no longer required.

**Reason**

During development, many individual GitHub Actions test-workflows were created.

A consolidated regression workflow reduces maintenance and manual administration without sacrificing test coverage.

As of 22 October 2026, 105 Floorball tests and the existing golf regression tests have passed.

**Date:** 22 October 2026.

---

## D030 – Real-world acceptance remains separate from technical verification

**Decision**

Successful automated tests and successful GitHub Actions execution do not automatically establish complete real-world acceptance.

Automatic floorball monitoring must also be verified during actual matches.

Required operational validation includes:

- Automatic match activation
- Pre-match baseline
- Match-event notifications
- Final-result notification
- Final snapshot persistence
- Registry completion
- Exclusion of completed matches from future monitoring

**Reason**

External platforms and real events can exhibit behavior that automated tests do not fully reproduce.

As of 22 October 2026, the automatic Live workflow is deployed and running successfully, but the first full real-world automatic match validation remains pending.

**Date:** 22 October 2026.

---

## D031 – Protect active monitoring during maintenance and cleanup

**Decision**

Nonessential production code changes and deletion of historical workflows should be deferred while an important real-world monitoring validation is approaching or active.

Documentation and low-risk maintenance may continue.

**Reason**

The working automatic Live system is scheduled to monitor real floorball matches on 23 and 25 October 2026.

Avoiding unnecessary changes protects the first production acceptance tests.

**Date:** 22 October 2026.
