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

Goal:

Design a connector contract that removes connector-specific logic from `watcher.py`.

No implementation has been decided yet.
