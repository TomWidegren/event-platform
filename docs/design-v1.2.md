# Event Platform v1.2 – Design Draft

This document captures design ideas for v1.2.

Nothing in this document is considered an architectural decision until explicitly approved and moved into `decisions.md`.

## Current design topic

Unified Connector Interface

## Design goal

Define a unified connector interface that keeps the Event Platform core independent of source-specific acquisition technology and configuration.

The emerging v1.2 design is:

```text
Watch
├── name
├── connector
├── mode
└── source
     └── connector-specific configuration
          ↓
       Connector
          ↓
   External source
          ↓
 Normalized snapshot
```

## Design Questions

### DQ1 – Who owns data acquisition?
Current alternatives:

### Option A – Core-owned acquisition

The Event Platform core owns shared acquisition resources.

Examples:

- Playwright browser
- Browser pages

Connectors receive access to those shared resources.

Pros:

- Browser startup happens only once.
- Shared browser session.

Cons:

- The core becomes aware of acquisition technology.
- API-based connectors receive resources they do not use.

---

### Option B – Connector-owned acquisition

Each connector owns its complete acquisition technology.

Examples:

- GolfBox starts Playwright.
- SGF Ranking starts Playwright.
- Tournytt uses HTTP requests directly.

Pros:

- The core becomes independent of acquisition technology.
- Each connector controls its own lifecycle.
- New acquisition technologies require no changes to the core.

Cons:

- Browser-based connectors may each create their own browser instance.
Should the Event Platform core create and manage shared resources (such as Playwright), or should each connector own its complete acquisition technology?

## Evaluation Criteria

The preferred alternative should:

1. Keep the Event Platform core independent of acquisition technology.
2. Keep connector responsibilities clearly separated from platform responsibilities.
3. Allow new connectors to be added without modifying the platform core.
4. Support both browser-based and API-based connectors.
5. Avoid unnecessary resource usage where practical.
6. Keep the connector contract simple and predictable.

### DQ1 – Design conclusion

**Resolved direction: Option B – Connector-owned acquisition.**

Each connector owns its complete data-acquisition lifecycle.

Examples:

- GolfBox owns its Playwright usage.
- SGF Ranking owns its Playwright usage.
- Tournytt owns its HTTP/SSE communication.
- Future connectors may use other acquisition technologies without requiring changes to the Event Platform core.

The Event Platform core should not know about or manage acquisition technologies such as Playwright, HTTP, SSE or future source-specific technologies.

The additional resource cost of browser-based connectors independently managing Playwright is considered acceptable at the current scale in exchange for clearer separation of responsibilities.

DQ1 is considered resolved for the v1.2 design.

### DQ2 – What is the connector contract?

The connector contract defines how the Event Platform core requests the current state from any connector.

Current alternatives:

#### Option A – Watch as connector input

Every connector exposes:

`fetch_snapshot(watch)`

The Watch represents the monitoring request.

The connector reads the fields it needs from the Watch and owns the complete process of acquiring and normalizing the external data.

Examples:

- SGF Ranking uses `player`.
- Tournytt uses `player` and `competition`.
- GolfBox uses `player` and GolfBox-specific competition/leaderboard configuration.

The connector returns:

- a normalized snapshot when the requested entity can be observed, or
- `None` when no relevant observation is available.

#### Option B – Explicit parameters

The core supplies parameters such as player, competition and leaderboard explicitly.

This makes individual function parameters visible but requires the core to understand connector-specific requirements.

#### Option C – Separate connector context object

The core constructs a dedicated connector input/context object.

This provides another abstraction layer but no current requirement has been identified that cannot be satisfied by the Watch itself.

### Preferred direction

Current preferred direction:

**Option A – Watch as connector input.**

Reasoning:

- A Watch naturally represents the monitoring request.
- Different connectors can consume different fields without requiring connector-specific logic in the core.
- The interface remains identical for all connectors.
- New connector-specific configuration can be introduced without changing the core.
- Following DQ1, acquisition resources such as Playwright no longer need to be passed through the connector interface.

### DQ2 – Design conclusion

**Resolved direction: Option A – Watch as connector input.**

Every connector will expose the same public interface:

`fetch_snapshot(watch)`

The Watch represents the monitoring request.

Each connector determines which Watch fields it requires, owns its complete acquisition and normalization process, and returns either a normalized snapshot or `None`.

DQ2 is considered resolved for the v1.2 design.

### DQ3 – What belongs in a Watch and how should connector-specific configuration be represented?

A Watch contains information used by the Event Platform core together with configuration required by the selected connector.

Two models were considered:

#### Option A – Flat Watch

Generic and connector-specific fields coexist at the top level.

Example:

```yaml
name: "Lukas Widegren - GolfBox"
connector: golfbox_leaderboard
mode: live
player: "Lukas Widegren"
competition: 5801055
leaderboard: ...
```

This is simple for the current golf use cases but mixes platform-level concepts with connector-specific concepts.

It also assumes that fields such as `player` are generic, while future watches may monitor different types of entities.

#### Option B – Structured Watch

The generic Watch contains only fields understood by the Event Platform core.

Connector-specific configuration is grouped under `source`.

GolfBox example:

```yaml
name: "Lukas Widegren - GolfBox"
connector: golfbox_leaderboard
mode: live

source:
  player: "Lukas Widegren"
  competition: 5801055
  leaderboard: ...
```

Future team-based example:

```yaml
name: "TTIBK match"
connector: <future_connector>
mode: live

source:
  team: "TTIBK"
  ...
```

This creates a clear responsibility boundary:

- The Event Platform core understands `name`, `connector`, `mode` and `source`.
- The selected connector owns and interprets everything inside `source`.
- The core does not need to understand whether the monitored entity is a player, team or another future entity type.

### Preferred direction

Current preferred direction:

**Option B – Structured Watch.**

Reasoning:

- It clearly separates platform configuration from connector-specific configuration.
- It avoids making golf-specific concepts such as `player` part of the generic platform model.
- New connector-specific parameters can be introduced without expanding the core Watch contract.
- It supports future non-golf use cases without requiring the core to understand new entity types.

### DQ3 – Design conclusion

**Resolved direction: Option B – Structured Watch.**

The generic Watch contains only:

- `name`
- `connector`
- `mode`
- `source`

The Event Platform core understands the generic Watch structure but does not interpret the contents of `source`.

The selected connector owns and interprets everything inside `source`, including the monitored entity and any source-specific identifiers or configuration.

DQ3 is considered resolved for the v1.2 design.

### DQ4 – What should the connector method be called?

The connector interface should use terminology that remains valid beyond the current golf use cases.

Current interface:

`fetch_player_snapshot(watch)`

This name is now considered potentially too specific because future Event Platform watches may monitor entities such as teams, matches or other non-player entities.

Current alternatives:

#### Option A – `fetch_player_snapshot(watch)`

Keeps the current name but embeds the current player-based use case in the platform interface.

#### Option B – `fetch_snapshot(watch)`

Describes the connector's responsibility without assuming what type of entity is being monitored.

#### Option C – `get_snapshot(watch)`

Also generic, but describes retrieval rather than the connector's current-state acquisition responsibility.

### DQ4 – Design conclusion

**Resolved direction: Option B – `fetch_snapshot(watch)`.**

The connector interface uses generic terminology that does not assume what type of entity is being monitored.

Every connector will expose:

`fetch_snapshot(watch)`

The connector fetches the current state from its external source, normalizes it and returns either a snapshot or `None`.

DQ4 is considered resolved for the v1.2 design.

### DQ5 – What is the snapshot contract?

The connector returns the current normalized state for the requested Watch.

The snapshot should not use a fixed platform-wide field structure.

Different external sources can expose different information, and different Watches may require different subsets of that information.

Examples:

- GolfBox provides leaderboard and round-specific fields.
- Tournytt provides fields such as score, position, to-par and played holes.
- SGF Ranking provides ranking-specific fields such as position, points and competitions.
- Future connectors may return completely different domain-specific information.

The connector is responsible for:

- selecting the relevant source data,
- normalizing it into a stable structure,
- returning the information needed to detect meaningful changes.

The Event Platform core does not interpret connector-specific snapshot fields.

Current alternatives:

#### Option A – Fixed platform-wide snapshot schema

All connectors return the same predefined set of fields.

#### Option B – Connector-defined normalized snapshot

Each connector returns a normalized dictionary appropriate to the source and Watch.

The only platform-level requirement is that the returned value is suitable for state comparison and change detection.

### DQ5 – Design conclusion

**Resolved direction: Option B – Connector-defined normalized snapshot.**

Each connector defines the normalized snapshot structure appropriate to its external source and Watch.

The Event Platform core does not require or interpret a fixed set of snapshot fields.

A snapshot must:

- represent the relevant current state of the Watch,
- use a stable structure suitable for comparison between executions,
- contain the information required to detect meaningful changes.

The connector owns the meaning and normalization of connector-specific snapshot fields.

The Event Platform core owns persistence and comparison of the returned snapshot.

A connector returns either:

- a normalized snapshot, or
- `None` when no relevant observation is available.

DQ5 is considered resolved for the v1.2 design.

## Source identification

A Watch identifies the Source through its selected connector.

The Source determines which source-specific configuration is required.

Current examples:

- SGF Ranking
- GolfBox Tournament
- Tournytt leaderboard API

A new connector should first identify the underlying Source before defining its source-specific configuration.

### Tournytt source

The Tournytt connector requires:

```yaml
source:
  player: "Lukas Widegren"
  competition: 5406076
```

### SGF Ranking source

The SGF Ranking connector requires:

```yaml
source:
  player: "Lukas Widegren"
  ranking: "Pojkar (juniorer)"
  year: 2026
  club: "Haninge Golfklubb"
```

These values identify what should be monitored in the SGF Ranking source.

The current implementation hard-codes `ranking`, `year` and `club`. In v1.2 these values should move into the Watch configuration under `source`.

Technical acquisition details such as the SGF Ranking URL, Playwright selectors and browser handling remain internal connector implementation details.

### GolfBox source assumption

For v1.2, `golfbox_leaderboard` is designed around GolfBox as the underlying Source rather than individual club websites.

The existing real-world validations include:

- Haninge Golfklubb
- Strängnäs Golfklubb
- NSGK (Hylinge)
- GolfBox Tournament (`golfbox.dk`)

The first three validations were performed through club websites using GolfBox, while the fourth was performed directly against GolfBox Tournament.

For the v1.2 design, we assume that future GolfBox Watches can be resolved directly through the underlying GolfBox Source.

This is a design assumption, not a claim that every historical or future GolfBox deployment has been verified to support direct access in the same way.

### GolfBox source

The GolfBox connector uses GolfBox as its underlying Source.

The proposed source configuration is:

```yaml
source:
  player: "Lukas Widegren"
  competition: 5801055
  leaderboard: <optional leaderboard identifier>
```

`player` identifies the monitored player.

`competition` identifies the GolfBox competition.

`leaderboard` is optional and may be required when a GolfBox competition contains multiple leaderboard classes.

The connector is responsible for resolving these identifiers into the appropriate GolfBox access mechanism.

Club-specific URLs and other acquisition details are not part of the Watch configuration.

If future real-world validation shows that direct GolfBox access cannot support a required deployment, this assumption and source model should be revisited.

## Implementation plan

The v1.2 migration is implemented incrementally.

### Phase 1 – Connector migration

**Status: Completed**

All three current connectors have been migrated to the approved interface:

`fetch_snapshot(watch)`

Completed:

- Tournytt reads its configuration from `watch["source"]`.
- SGF Ranking reads its configuration from `watch["source"]` and owns its Playwright lifecycle.
- GolfBox reads its configuration from `watch["source"]`, owns its Playwright lifecycle and resolves the GolfBox access URL from source configuration.

The connectors retain their existing normalized snapshot structures.

### Phase 2 – Watch and state migration

**Status: Completed**

`config.yml` has been migrated to the Structured Watch model:

- `id`
- `name`
- `connector`
- `mode`
- `source`

All source-specific configuration has been moved under `source`.

Stable Watch IDs have been introduced:

- `lukas-sgf-ranking`
- `lukas-golfbox`
- `lukas-tournytt`

Existing active state has been migrated from legacy state keys to the corresponding Watch IDs without changing snapshot or field content.

Legacy state belonging to inactive Watches does not need to be migrated.

### Phase 3 – Notification formatting separation

**Status: Not started**

Move connector-specific notification formatting out of the Event Platform core.

Notification formatting should be handled by a separate formatting layer according to DQ7.

The formatting layer should:

- receive the relevant Watch and snapshot,
- interpret connector-specific snapshot fields,
- return user-facing notification content.

The core should decide when a notification is triggered without interpreting connector-specific snapshot fields.

### Phase 4 – Core migration

**Status: Not started**

Refactor `watcher.py` so that it:

- uses `watch["id"]` as the persistent state key,
- selects the configured connector,
- calls `fetch_snapshot(watch)`,
- contains no connector-specific acquisition logic,
- no longer owns Playwright,
- contains no connector-specific notification formatting.

Remove:

- the temporary Tournytt-specific branching,
- connector-specific parameter extraction,
- Playwright lifecycle management,
- connector-specific formatting logic.

### Phase 5 – Verification

**Status: Completed**

Successfully verified:

- Daily monitoring with SGF Ranking through the migrated v1.2 architecture.
- Live execution with GolfBox through the migrated v1.2 architecture.
- Live execution with Tournytt through the migrated v1.2 architecture.
- Watch ID based state persistence across separate executions.
- Change detection using migrated state.
- Notification formatting through the separate formatting layer.
- Notification delivery through ntfy.
- Unchanged snapshots correctly produce no notification.

Verification included:

- A real SGF Ranking change was detected, persisted and notified.
- A subsequent SGF execution correctly reported no change.
- GolfBox returned the expected completed-tournament snapshot and a subsequent execution correctly reported no change.
- Tournytt matched its existing completed-tournament state and correctly reported no change.

v1.2 is considered implemented and technically verified.

### DQ6 – What identifies a Watch across executions?

The Event Platform must use a stable identity for each Watch so that state can persist across executions.

The identity must remain independent of:

- connector-specific fields,
- monitored entity type,
- acquisition technology.

Current alternatives:

#### Option A – Use `name` as Watch identity

The Watch `name` is unique and acts as the persistent identity.

Example:

```yaml
name: "Lukas Widegren - Tournytt"
```

Pros:

- No additional Watch field.
- Simple and human-readable.
- Compatible with the current configuration model.

Cons:

- Renaming a Watch changes its identity unless a migration mechanism is provided.

#### Option B – Introduce a dedicated `id`

Each Watch receives a stable technical identifier separate from its display name.

Example:

```yaml
id: "lukas-widegren-tournytt"
name: "Lukas Widegren - Tournytt"
```

Pros:

- Display name can change without changing state identity.
- Explicit technical identity.

Cons:

- Adds another generic Watch field.
- Requires users to manage an additional identifier.

### DQ6 – Design conclusion

**Resolved direction: Option B – Dedicated Watch ID.**

Every Watch has a stable technical `id` that is separate from its human-readable `name`.

The generic Watch structure therefore becomes:

- `id`
- `name`
- `connector`
- `mode`
- `source`

The Watch `id` is used as the persistent identity across executions.

The `name` may change without changing the identity of the Watch or creating a new state baseline.

The Watch `id` must remain stable once the Watch has persistent state.

DQ6 is considered resolved for the v1.2 design.

### Watch ID strategy

Watch IDs are stable technical identifiers.

For the current Watches:

- `lukas-sgf-ranking`
- `lukas-golfbox`
- `lukas-tournytt`

The ID should describe the persistent monitoring intent rather than transient source details such as competition IDs.

Changing a competition or other source-specific configuration must therefore not require changing the Watch ID.

Existing active state should be migrated once from the legacy state keys to the corresponding Watch IDs.

The migration should preserve the existing snapshot and fields unchanged.

Legacy state belonging to Watches that are no longer active does not need to be migrated.

The Event Platform core should not contain permanent backward-compatibility logic for legacy state keys.

### DQ7 – Who owns notification formatting?

The Event Platform core currently contains source-specific notification formatting.

This conflicts with the v1.2 design principle that the core should not interpret connector-specific snapshot fields.

The design must therefore define where notification formatting belongs.

Current alternatives:

#### Option A – Core-owned formatting

The core interprets snapshot fields and constructs the notification message.

This keeps notification generation centralized but makes the core aware of connector-specific snapshot structures.

#### Option B – Connector-owned formatting

The connector provides the notification representation together with the normalized snapshot.

This keeps source-specific interpretation inside the connector but couples notification presentation to the connector.

#### Option C – Separate notification formatting layer

Snapshot normalization remains connector-owned while notification formatting is handled by a separate component that understands the relevant snapshot type.

This creates a clearer separation but introduces another abstraction.

### DQ7 – Design conclusion

**Resolved direction: Option C – Separate notification formatting layer.**

Notification formatting is separate from both connector acquisition logic and Event Platform core logic.

Responsibilities are:

- Connectors acquire and normalize source-specific data.
- The Event Platform core persists snapshots, detects changes and decides when a notification should be triggered.
- Notification formatters interpret connector-specific snapshot fields and create user-facing notification content.
- The notification provider delivers the formatted message.

This allows notification presentation to evolve independently of both connectors and the Event Platform core.

The core must not interpret connector-specific snapshot fields for presentation purposes.

DQ7 is considered resolved for the v1.2 design.

## Design workshop status

The v1.2 Unified Connector Interface design is complete.

DQ1–DQ7 have been resolved and consolidated into architectural decision D016 in `decisions.md`.

The approved design establishes:

- Connectors own their complete data-acquisition lifecycle.
- Every connector exposes `fetch_snapshot(watch)`.
- Watches use the generic structure `id`, `name`, `connector`, `mode` and `source`.
- Watch `id` provides stable identity across executions.
- The selected connector owns and interprets everything inside `source`.
- Snapshots are connector-defined normalized representations rather than a fixed platform-wide schema.
- Notification formatting is separated from both connector acquisition logic and Event Platform core logic.
- The Event Platform core remains responsible for connector selection, state persistence, change detection and deciding when notifications should be triggered.

The design phase is complete.

Implementation is in progress according to the implementation plan.

Phases 1–4 have been implemented.

Daily monitoring with SGF Ranking and Live monitoring with GolfBox have been successfully verified through the migrated v1.2 architecture.

Tournytt verification and final v1.2 verification remain before the implementation can be considered complete and released.
