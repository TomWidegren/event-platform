# Event Platform – Decisions

This document records important decisions for Event Platform and why they were made.

It is not a description of the current architecture. See `architecture.md` for that.

A decision should only be changed deliberately. If a decision changes, document the new decision and why.

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

`watcher.py` owns:

- Configuration loading
- Connector selection
- Snapshot comparison
- Change detection
- Notification triggering
- State updates

**Reason**

All connectors should benefit from the same monitoring behavior without implementing it themselves.

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

The platform currently supports:

- `daily`
- `live`

Daily is used for relatively slow-changing sources.

Live is used during active events.

**Reason**

Different sources require different polling frequencies and operational behavior.

---

## D007 – Live polling interval is five minutes

**Decision**

Live monitoring currently runs every five minutes.

The Live schedule is enabled during relevant events and disabled between events.

**Reason**

Five minutes provides useful live updates without unnecessary continuous polling.

---

## D008 – Daily monitoring remains enabled

**Decision**

Daily monitoring runs continuously once per day.

Current use case:

SGF Ranking.

**Reason**

Ranking changes relatively infrequently and does not require event-specific activation.

---

## D009 – First observation behaves differently for Daily and Live

**Decision**

For Daily:

First observation establishes a baseline without sending a notification.

For Live:

The first real event result establishes the baseline and sends a notification.

An empty or not-yet-started leaderboard is not considered a real result.

**Reason**

For ranking, the initial state is primarily a comparison benchmark.

For live events, the transition from no result to the first result is itself meaningful.

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

`state.json` stores the latest known snapshot.

GitHub Actions commits changed state back to the repository.

**Reason**

Executions are stateless GitHub runners. Persistent state is required to compare one execution with the next.

The workflow must account for the possibility that `main` changes while a run is executing.

---

## D012 – Source-specific parameters belong in configuration

**Decision**

Reusable connectors should not permanently hard-code event-specific identifiers.

Examples include:

- competition ID
- leaderboard ID
- player
- other source-specific identifiers

These should ultimately be supplied through configuration.

**Reason**

A reusable connector should ideally support the next event through configuration rather than Python changes.

---

## D013 – Verify behavior with real events where practical

**Decision**

Prefer real-world validation over artificial state manipulation when practical.

**Reason**

The Haninge and Strängnäs tests revealed behavior that would have been difficult to predict from static testing alone.

Examples include:

- changing leaderboard layouts
- multiple competition classes
- live position changes
- round transitions
- final result population

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
