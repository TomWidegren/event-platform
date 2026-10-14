# Event Platform – Project Context

This file is the starting point for every new Event Platform development session.

Its purpose is to allow a human or AI assistant to restore sufficient project context without relying on previous conversation history.

The repository is the source of truth.

## Project

Name: Event Platform

Current production release: v1.2.0

Event Platform monitors changing data from external platforms, detects relevant changes, stores state and sends notifications.

Golf is the first use case, but the platform core should remain independent of golf-specific logic.

## Current production capabilities

Event Platform currently supports two monitoring modes:

- Daily
- Live

Current connectors:

- `sgf_ranking`
- `golfbox_leaderboard`
- `tournytt_api`

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

Verified with:

- Haninge Golfklubb
- Strängnäs Golfklubb
- NSGK (Hylinge)
- GolfBox Tournament (`golfbox.dk`)
  
Verified lifecycle:

- Empty leaderboard
- First live result
- Hole-by-hole scoring
- Position changes caused by other players
- Completion of round 1
- Transition to round 2
- Hole-by-hole scoring in round 2
- Completed two-round tournament

The completed validations demonstrate that the platform-level GolfBox connector can be reused across different club websites and directly against the GolfBox Tournament site without site-specific parsing changes.

### Tournytt API

Verified:

- SSE API communication
- Player lookup
- Baseline creation
- Change detection
- State persistence
- GitHub state updates
- Notifications

Observed behavior:

- Player entries are published before play starts.
- Baseline is therefore created before the first score.
- Notification formatting should be improved to better present Tournytt-specific fields.

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

### Completed validation – GolfBox

The GolfBox connector has now been successfully validated across four real-world GolfBox deployments.

Validated implementations:

- Haninge Golfklubb
- Strängnäs Golfklubb
- NSGK (Hylinge)
- GolfBox Tournament (`golfbox.dk`)

Combined validation covered:

- Empty leaderboard
- Player present before start
- First result
- Live hole-by-hole scoring
- Round-based result publication
- Position changes
- Round transitions
- Completed two-round tournaments
- State persistence
- Notifications

The connector required no site-specific implementation beyond selecting the correct competition/leaderboard.

The GolfBox validation phase is considered complete.

### Completed validation – Tournytt

The Tournytt API connector has been successfully validated.

Validated capabilities:

- SSE API communication
- Player lookup
- State persistence
- Change detection
- GitHub state updates
- Notifications

Observations:

- Tournytt publishes complete player entries before play starts.
- The connector correctly established a baseline before the first result.
- Tournament updates were detected correctly during play.

Known improvement:

- Notification formatting should be adapted to the Tournytt snapshot model.

### Completed release – v1.2.0

Event Platform v1.2.0 – Unified Connector Interface has been implemented, verified and published as the latest GitHub release.

Key capabilities:

- Unified connector interface: `fetch_snapshot(watch)`
- Connector-owned data acquisition
- Structured Watches with stable IDs
- Connector-specific configuration under `source`
- Connector-defined normalized snapshots
- Separate notification formatting layer
- Generic Event Platform core

Verified:

- SGF Ranking – Daily monitoring
- GolfBox – Live monitoring
- Tournytt – Live monitoring
- State persistence and change detection
- Notification formatting and delivery through ntfy

Current production release: v1.2.0

The v1.2 development and release cycle is complete.

Future development should be prioritized from `docs/backlog.md`.


### Floorball development – First implementation

Date: 14 October 2026

Current production release: v1.2.0.

The first floorball monitoring implementation has been developed and technically verified in preparation for a real-world match test on 15 October 2026.

#### Initial match

- Competition: Juniorallsvenskan D HJ18
- Match: Huddinge IBS – Tyresö Trollbäcken IBK
- Match ID: 1750693
- Match start: 15 October 2026, 20:15
- Followed team ID: 20872
- Highlighted player: Lukas Widegren (PlayerID 585280)

#### Implemented

- New connector: `connectors/ibis_floorball.py`
- Automatic temporary authentication through iBIS startkit
- HTTP/JSON match data acquisition
- Normalized match snapshots including match events
- Floorball-specific notification formatting
- Comparison of previous and current match events using MatchEventID
- Highlighting of Lukas goals, assists and penalties
- Generic optional WATCH_ID execution filter
- Structured floorball Watch in `config.yml`
- Permanent baseline in `state.json`
- Isolated connector, formatter and baseline tests

#### Verified

- GitHub Actions can obtain a temporary iBIS access token.
- Authenticated match API requests return HTTP 200.
- The connector retrieves and normalizes the correct match.
- All five notification formatting tests pass.
- Multiple new events are included in one notification.
- Previously observed events are not repeated in formatting tests.
- Final-result formatting works in simulated tests.
- Existing golf notification formatting passes its regression test.
- The first floorball baseline is saved without notification.
- Four existing state entries are preserved.
- Manual Live execution using WATCH_ID runs only the floorball Watch.
- Unchanged match data produces no notification.

#### Current limitations

- Real-time match updates have not yet been verified.
- Match-start detection and notification wording are not finalized.
- Real ntfy delivery for floorball has not yet been verified.
- Event corrections and deletions are not fully handled.
- Automatic discovery of matches across teams and competitions remains future work.
- Notification preferences are not yet configurable.

#### Live validation plan

15 October 2026:

- Enable Event Platform - Live in cron-job.org before travelling to the match, approximately 17:00–18:00.
- Keep the existing five-minute polling interval.
- Monitor match start, goals, penalties and final result.
- Verify notifications and state persistence.
- Disable the Live schedule after the match.

The Live workflow is temporarily restricted to:

`WATCH_ID: floorball-match-1750693`

The Daily workflow remains enabled.

#### Next development goal

Evaluate the real-world match results and address any issues found.

Then continue designing reusable monitoring for multiple floorball teams and competitions.

Detailed design and investigation findings are documented in:

`docs/design-floorball.md`

The floorball implementation is not yet part of a published production release.

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
