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

### Preferred direction

Current preferred direction:

Option B – Connector-owned acquisition.

Reasoning:

The Event Platform core should remain independent of acquisition technology.

Each connector is responsible for its complete acquisition lifecycle and may choose the technology that best matches the external platform.

The current implementation cost of starting Playwright independently in browser-based connectors is considered acceptable in exchange for a cleaner architecture.

This direction has not yet been promoted to an architectural decision.

### DQ2 – What is the connector contract?

Should connectors receive:

- watch

or

- context

or something else?

### DQ3 – What belongs in a Watch?

Which fields are part of the generic watch contract?

Which fields are connector-specific?

### DQ4 – How should connector-specific configuration be represented?

Should connector-specific parameters remain top-level fields or be grouped under a dedicated configuration section?

Goal:

Design a connector contract that removes connector-specific logic from `watcher.py`.

No implementation has been decided yet.
