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

Used for technical verification of the floorball implementation.

## Verified real-world behavior

### SGF Ranking

Verified:

- Player lookup.
- Baseline creation.
- Daily monitoring.
- Real ranking changes after a competition.

### GolfBox Leaderboard

Verified with:

- Haninge Golfklubb.
- Strängnäs Golfklubb.
- NSGK (Hylinge).
- GolfBox Tournament (`golfbox.dk`).

Verified lifecycle:

- Empty leaderboard.
- First live result.
- Hole-by-hole scoring.
- Position changes caused by other players.
- Completion of round 1.
- Transition to round 2.
- Hole-by-hole scoring in round 2.
- Completed two-round tournament.

The GolfBox connector has been validated across multiple deployments without site-specific parsing changes.

### Tournytt API

Verified:

- SSE API communication.
- Player lookup.
- Baseline creation.
- Change detection.
- State persistence.
- GitHub state updates.
- Notifications.

Observed behavior:

- Player entries are published before play starts.
- Baseline is therefore created before the first score.
- Notification formatting should be improved to better present Tournytt-specific fields.

### Floorball / iBIS

First implementation completed on 14 October 2026.

Implemented:

- `connectors/ibis_floorball.py`.
- Temporary authentication through the iBIS startkit endpoint.
- HTTP/JSON match data acquisition.
- Normalized match snapshots.
- Match status, score and event monitoring.
- Detection of new events using MatchEventID.
- Floorball-specific notification formatting.
- Player-specific highlighting.
- Optional `WATCH_ID` execution filtering.
- Permanent pre-match baseline.
- Automated connector and formatting tests.

#### First real-world validation – 15 October 2026

Match:

Huddinge IBS – Tyresö Trollbäcken IBK

Competition: Juniorallsvenskan D HJ18

Match ID: 1750693

Followed team ID: 20872

Highlighted player: Lukas Widegren, PlayerID 585280.

The live monitoring operated successfully during the match.

An additional iBIS event type was identified:

- MatchEventTypeID 1 – Regular goal.
- MatchEventTypeID 12 – Empty-net goal.

The notification formatter was updated to handle both event types as goals.

Empty-net goals are explicitly identified with the suffix `(tom bur)`.

The current implementation has been verified through inspection of `notification_formatters.py`.

Detailed results for individual match-event categories have not yet been documented.

#### Second real-world validation – 17 October 2026

Match:

IFK Haninge (B) – Tyresö Trollbäcken IBK (A)

Competition: Herrar Division 3 Södra

Match ID: 1703572

Start: 17 October 2026, 13:30

Venue: Lyckeby Sporthall

Followed team ID: 4194

Highlighted player: Lukas Widegren, PlayerID 585280.

Preparation completed on 16 October:

- New Watch added to `config.yml`.
- Existing Golf and Floorball Watches preserved.
- Separate stable Watch ID: `floorball-match-1703572`.
- Permanent pre-match baseline established.
- Five existing state entries preserved.
- No notification generated during baseline creation.
- `live.yml` updated to target the new Watch.
- Manual Live execution completed successfully.
- Unchanged match data produced no notification.
- Automatic execution through cron-job.org and GitHub Actions verified.
- Five-minute polling interval confirmed.

**Current status: Ready for real-world match validation.**

Match-event notifications and final-result handling remain to be evaluated during and after the match.

## Important current limitations

### General platform

- GolfBox competitions may require both competition ID and leaderboard ID.
- Some GolfBox event-specific information may still need further configuration generalization.
- Ranking notifications do not clearly show previous → new values.
- Tournytt notification formatting could be improved.

### State persistence

`state.json` is persisted through GitHub commits.

The current Live workflow can overwrite concurrent state changes because it restores a complete saved state file after synchronizing with `main`.

This risk should be addressed before introducing broader concurrent monitoring.

### Floorball

- Automatic discovery of upcoming matches is not implemented.
- Live monitoring currently requires manual Watch configuration.
- The Live workflow uses a specific `WATCH_ID`.
- Multiple simultaneous Live Watches are not yet operationally supported through the current workflow configuration.
- Handling of corrected or deleted match events requires further evaluation.
- Notification preferences are not configurable.
- The complete iBIS event-type model has not been documented.
- GitHub Actions runtime compatibility requires review following announced platform updates.

## Documentation

Before making architectural or implementation decisions, read:

1. `README.md`
2. `docs/ARCHITECTURE.md`
3. `docs/decisions.md`
4. `docs/ways-of-working.md`
5. `docs/backlog.md`

Relevant design documentation:

- `docs/design-v1.2.md`
- `docs/design-floorball.md`

`PROJECT_CONTEXT.md` is always the first document to read.

The repository documentation is authoritative.

Do not rely on previous AI conversation history when repository documentation is available.

## Starting a development session

At the beginning of every session:

1. Read this file.
2. Read the project documentation listed above.
3. Identify the current production release and ongoing development.
4. Ask or confirm the goal for the session.
5. Read only the source files relevant to that goal.
6. Do not propose code changes before relevant current files have been inspected.

## During a development session

Follow `docs/ways-of-working.md`.

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

1. Summarize completed work.
2. Record verified results.
3. Identify unresolved issues.
4. Update relevant documentation.
5. Update this file when project status materially changes.
6. Confirm that documentation changes have been committed.
7. Identify the recommended next goal.

The next session must be able to continue without access to previous ChatGPT conversations.

## Current development direction

### Completed release – v1.2.0

Event Platform v1.2.0 – Unified Connector Interface has been implemented, verified and published.

Key capabilities:

- Unified connector interface: `fetch_snapshot(watch)`.
- Connector-owned data acquisition.
- Structured Watches with stable IDs.
- Connector-specific configuration under `source`.
- Connector-defined normalized snapshots.
- Separate notification formatting layer.
- Generic Event Platform core.

The v1.2.0 release cycle is complete.

### Floorball development – Real-world validation

The first floorball connector has been implemented and technically verified.

The first real-world match validation took place on 15 October 2026.

A second match is configured for 17 October 2026.

The floorball implementation has not yet been included in a published production release.

The next development phase should be determined after evaluating the real-world match results.

### Recommended next goal

After the match on 17 October:

1. Review GitHub Actions execution logs.
2. Review ntfy notifications.
3. Compare notifications with the official match-event history.
4. Verify final-result handling.
5. Confirm state persistence and absence of duplicate notifications.
6. Document findings in `docs/design-floorball.md`.
7. Update `docs/backlog.md`.
8. Determine the next development priority.

Potential future development includes:

- Multiple simultaneous Live Watches.
- Automatic floorball match discovery.
- More flexible team and competition monitoring.
- Safer concurrent state persistence.
- Improved notification presentation.

No new release should be created until the relevant capability has been verified and deliberately approved for release.

## Context rule

If an AI assistant does not have direct access to the repository, provide this file at the start of the session.

The assistant should then request only the additional documentation or source files needed for the agreed goal.

Do not reconstruct project state from conversational memory when current repository files can be provided.

## ChatGPT conversation lifecycle

A new ChatGPT conversation should normally be started when beginning development of a new software version.

Additional conversations may be started within the same version when necessary.

A conversation change does not imply a software release.

Before changing conversations, ensure that the repository documentation reflects the latest verified development state.

Detailed procedures are defined in `docs/ways-of-working.md`.

## Simple session commands

The user should not need to remember the development-session procedure.

### Start

If the user says:

"Nu fortsätter vi med Event Platform."

The assistant should:

1. Request `PROJECT_CONTEXT.md` if it is not already available.
2. Restore project context from repository documentation.
3. Request only additional files needed for the session.
4. Confirm the session goal before making changes.

### End

If the user says:

"Vi avslutar för idag."

The assistant should:

1. Summarize completed and verified work.
2. Identify unresolved issues and recommended next goal.
3. Determine which documentation needs updating.
4. Provide required documentation changes before ending.
5. Verify that `PROJECT_CONTEXT.md` is current.
6. Confirm that documentation updates have been committed.
