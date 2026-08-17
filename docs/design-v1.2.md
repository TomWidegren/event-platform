# Event Platform v1.2 – Design Draft

This document captures design ideas for v1.2.

Nothing in this document is considered an architectural decision until explicitly approved and moved into `decisions.md`.

## Current design topic

Unified Connector Interface

Current question:

Should connectors receive:

- `watch`

or

- `context`

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
