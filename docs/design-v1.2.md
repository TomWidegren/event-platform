# Event Platform v1.2 – Design Draft

This document captures design ideas for v1.2.

Nothing in this document is considered an architectural decision until explicitly approved and moved into `decisions.md`.

## Current design topic

Unified Connector Interface

## Design question

Define the connector execution context.

The goal is to establish one common public interface for every connector while allowing different acquisition technologies.

The connector should not need to know how the platform was started.

The platform should not need to know how the connector acquires data.

## Candidate Context

Current proposal:

context

├── watch
│   ├── name
│   ├── connector
│   ├── mode
│   ├── player
│   ├── competition (optional)
│   ├── leaderboard (optional)
│   └── future connector-specific configuration

Further context elements are intentionally left undefined until the context responsibilities have been designed.


Current observations:

GolfBox requires:

- Playwright page
- watch configuration

Tournytt requires:

- watch configuration only

SGF Ranking requires:

- Playwright page
- player

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

`fetch_player_snapshot(watch)`

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

`fetch_player_snapshot(watch)`

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


## Design workshop status

DQ1 has a preferred direction but no architectural decision has been made.

Implementation remains intentionally paused until the design phase is complete.
