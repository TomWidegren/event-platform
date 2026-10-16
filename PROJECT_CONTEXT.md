# Event Platform – Project Context

This file is the starting point for every new Event Platform development session.

Its purpose is to allow a human or AI assistant to restore sufficient project context without relying on previous conversation history.

**The repository is the source of truth. ChatGPT conversations are working environments, not the project's long-term memory.**

## Project

Name: Event Platform

Current production release: **v1.2.0**

Event Platform monitors changing data from external platforms, detects relevant changes, stores state and sends notifications.

Golf was the first use case, but the platform core remains independent of golf-specific logic.

Floorball monitoring has subsequently been implemented and is undergoing real-world validation.

## Current production capabilities

Event Platform supports two monitoring modes:

- Daily
- Live

Connectors included in the current production release:

- `sgf_ranking`
- `golfbox_leaderboard`
- `tournytt_api`

Additional connector under development:

- `ibis_floorball`

Current notification provider:

- ntfy

Current execution:

- cron-job.org triggers execution.
- GitHub Actions runs the platform.
- `watcher.py` is the core execution engine.
- `state.json` persists the latest known state.

## Current workflows

### Daily

Workflow: `.github/workflows/daily.yml`

Used for SGF Ranking.

Normally remains enabled continuously.

### Live

Workflow: `.github/workflows/live.yml`

Used for active GolfBox, Tournytt and floorball monitoring.

Polling interval: 5 minutes.

The Live schedule is normally disabled between events.

Current configuration, 16 October 2026:

- Live schedule enabled in cron-job.org.
- Workflow restricted to `WATCH_ID: floorball-match-1703572`.
- Monitoring prepared for the floorball match on 17 October 2026.

### Floorball baseline

Workflow: `.github/workflows/floorball-baseline.yml`

Used to establish a permanent pre-match baseline without generating notifications.

The workflow verifies that the match has not started and preserves existing state entries.

### Floorball testing

Workflow: `.github/workflows/test-floorball.yml`

Used for technical verification of the
