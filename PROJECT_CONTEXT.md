# Event Platform – Project Context

This file is the starting point for every new Event Platform development session.

Its purpose is to allow a human or AI assistant to restore sufficient project context without relying on previous conversation history.

The repository is the source of truth.

## Project

Name: Event Platform

Current production release: v1.1.0

Event Platform monitors changing data from external platforms, detects relevant changes, stores state and sends notifications.

Golf is the first use case, but the platform core should remain independent of golf-specific logic.

## Current production capabilities

Event Platform currently supports two monitoring modes:

- Daily
- Live

Current connectors:

- `sgf_ranking`
- `golfbox_leaderboard`

Current notification provider:

- ntfy

Current execution:

- cron-job.org triggers execution
- GitHub Actions runs the platform
- `watcher.py` is the core execution engine
- `state.json` persists the latest known state

## Current workflows

Daily:

- Workflow: `.github/workflows/daily.yml`
- Used for SGF Ranking
- Normally remains enabled

Live:

- Workflow: `.github/workflows/live.yml`
- Used for active GolfBox events
- Polling interval: 5 minutes
- Normally disabled between events

## Verified real-world behavior

### SGF Ranking

Verified:

- Player lookup
- Baseline creation
- Daily monitoring
- Real ranking changes after a competition

### GolfBox Leaderboard

Verified with both Haninge Golfklubb and Strängnäs Golfklubb.

Verified lifecycle:

- Empty leaderboard
- First live result
- Hole-by-hole scoring
- Position changes caused by other players
- Completion of round 1
- Transition to round 2
- Hole-by-hole scoring in round 2
- Completed two-round tournament

The Strängnäs test verified that a platform-level GolfBox connector can be reused across different club websites.

## Important current limitations

The GolfBox connector still contains event-specific leaderboard information that should ultimately move to configuration.

GolfBox competitions may contain multiple leaderboard classes, so both competition ID and leaderboard ID may be required.

Repository-based `state.json` persistence works but GitHub workflow concurrency must be handled carefully.

Ranking notifications currently show the new state but do not clearly show previous → new values.

## Documentation

Before making architectural or implementation decisions, read:

1. `README.md`
2. `docs/architecture.md`
3. `docs/decisions.md`
4. `docs/ways-of-working.md`
5. `docs/backlog.md`

These documents contain the authoritative project context.

Do not rely on previous AI conversation history when repository documentation is available.

## Starting a development session

At the beginning of every session:

1. Read this file.
2. Read the project documentation listed above.
3. Identify the current production release.
4. Ask or confirm the goal for the session.
5. Read only the source files relevant to that goal.
6. Do not propose code changes before current relevant files have been inspected.

## During a development session

Follow the principles in `docs/ways-of-working.md`.

In particular:

- One goal.
- One step.
- One verification.
- Then the next step.

Prefer evidence over assumptions.

Do not repeat completed work.

Do not silently change direction.

For substantial file changes, provide the entire replacement file in one continuous copyable block.

## Ending a development session

Before ending:

1. Summarize what was completed.
2. Record anything that was verified.
3. Identify unresolved issues.
4. Update documentation if architecture, decisions, ways of working or backlog changed.
5. Update this file if the overall project status materially changed.
6. Identify the recommended next goal.

## Current development direction

### Completed validation – NSGK

The GolfBox connector has now been successfully validated against a third independent GolfBox implementation.

Validation target:

- Site: NSGK
- Competition ID: `5543525`

Verified behavior:

- Empty leaderboard
- Player present before start
- Pre-start handling (start time without score)
- First result
- Completed round 1
- Transition to round 2
- Completed tournament
- Final state persistence
- Notifications

The connector required no NSGK-specific implementation beyond changing the target URL.

The three completed real-world GolfBox validations are now:

- Haninge Golfklubb
- Strängnäs Golfklubb
- NSGK (Hylinge)

This provides sufficient evidence to begin generalizing the GolfBox connector.

## Context rule

If an AI assistant does not have direct access to this repository, provide this file at the start of the session.

The assistant should then request only the additional documentation or source files needed for the agreed session goal.

Do not reconstruct project state from conversational memory when current repository files can be provided.

## Simple session commands

The user should not need to remember the development-session procedure.

### Start

If the user says:

"Nu fortsätter vi med Event Platform."

The assistant should:

1. Request `PROJECT_CONTEXT.md` if it is not already available.
2. Restore project context before proposing work.
3. Request only additional files needed for the session.
4. Confirm the session goal before making changes.

### End

If the user says:

"Vi avslutar för idag."

The assistant should:

1. Summarize what was completed and verified.
2. Identify unresolved issues and recommended next goal.
3. Determine whether Architecture, Decisions, Ways of Working or Backlog need updating.
4. Provide any required documentation updates before ending the session.
5. Determine whether `PROJECT_CONTEXT.md` needs updating.
