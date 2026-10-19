
# Event Platform – Project Context

This file is the starting point for every new Event Platform development session.

Its purpose is to allow a human or AI assistant to restore sufficient project context without relying on previous conversation history.

**The repository is the source of truth. ChatGPT conversations are working environments, not the project's long-term memory.**

## Project

Name: Event Platform

Current production release: **v1.2.0**

Event Platform monitors changing data from external platforms, detects relevant changes, stores state and sends notifications.

Golf was the first use case, but the platform core remains independent of golf-specific logic.

Floorball monitoring has subsequently been implemented and successfully validated during two real-world matches.

The Floorball capability is being prepared for its first production release, proposed as v1.3.0.

Last development checkpoint: 19 October 2026.

## Current production capabilities

Event Platform supports two monitoring modes:

- Daily
- Live

Connectors included in the current published production release:

- `sgf_ranking`
- `golfbox_leaderboard`
- `tournytt_api`

Additional implemented connector, pending release:

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

GitHub Actions versions updated on 19 October 2026:

- `actions/checkout@v5`
- `actions/setup-python@v6`

The next scheduled Daily execution is 20 October 2026 at 08:00.

**Status: Updated – Production verification pending.**

The next execution should verify:

- Successful GitHub Actions execution.
- Python environment setup.
- Playwright and Chromium installation.
- SGF Ranking acquisition.
- State persistence behavior.
- Absence of Node.js 20 deprecation warnings.

### Live

Workflow: `.github/workflows/live.yml`

Used for active GolfBox, Tournytt and floorball monitoring.

Polling interval: 5 minutes.

The Live schedule is normally disabled between events.

Last verified live monitoring configuration:

- `WATCH_ID: floorball-match-1703572`.
- Automatic execution through cron-job.org and GitHub Actions verified during the match on 17 October 2026.
- Monitoring completed successfully.

On 19 October 2026, the user confirmed that the Live schedule in cron-job.org had been disabled.

GitHub Actions versions updated on 19 October 2026:

- `actions/checkout@v5`
- `actions/setup-python@v6`

**Status: Updated – Production workflow verification pending.**

The Live workflow has not been executed after the Actions version updates.

Do not reactivate Live monitoring solely for regression testing against a completed match.

### Floorball baseline

Workflow: `.github/workflows/floorball-baseline.yml`

Used to establish a permanent pre-match baseline without generating notifications.

The workflow verifies that the match has not started and preserves existing state entries.

Successfully used for both floorball validation matches.

### Floorball testing

Workflow: `.github/workflows/test-floorball.yml`

Used for technical verification of the floorball implementation.

Updated on 19 October 2026 to:

- `actions/checkout@v5`
- `actions/setup-python@v6`

The updated workflow was successfully executed on 19 October 2026.

Verified:

- iBIS connector acquisition and normalization.
- Six floorball notification formatting tests.
- Floorball baseline creation using temporary state.
- No real ntfy notification from the mocked baseline test.
- Successful execution with the updated Actions versions.
- Node.js 20 deprecation warning no longer present.

### Platform regression testing

Workflow: `.github/workflows/test-regression.yml`

Introduced on 19 October 2026.

Purpose:

Verify existing golf monitoring logic without sending real notifications or modifying production state.

The workflow uses:

- Mocked connector snapshots.
- Mocked ntfy notification delivery.
- Temporary state files.
- GitHub Actions with read-only repository permissions.

Verified for:

- SGF Ranking.
- GolfBox.
- Tournytt.

Tests cover:

- Connector registration.
- Notification formatting.
- Daily baseline behavior.
- Live first-observation behavior.
- No additional notification for unchanged data.
- Change detection.
- State persistence.

Updated on 19 October 2026 to:

- `actions/checkout@v5`
- `actions/setup-python@v6`

The updated regression workflow passed successfully.

The Node.js 20 deprecation warning was no longer present.

These tests do not independently verify current external golf data acquisition.

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

**Status: Completed successfully**

Match:

Huddinge IBS – Tyresö Trollbäcken IBK

Competition: Juniorallsvenskan D HJ18

Match ID: 1750693

Followed team ID: 20872

Highlighted player: Lukas Widegren, PlayerID 585280.

The live monitoring operated successfully during the match.

Verified notifications:

- Goals.
- Penalties.
- Period starts.
- Period ends.
- Final result.
- Other registered match events.

An additional iBIS event type was identified:

- MatchEventTypeID 1 – Regular goal.
- MatchEventTypeID 12 – Empty-net goal.

The notification formatter was updated to handle both event types as goals.

Empty-net goals are explicitly identified with the suffix `(tom bur)`.

The updated implementation was verified through inspection of `notification_formatters.py`.

Player-specific highlighting was not verified during the match because Lukas did not score, record an assist or receive a penalty.

#### Second real-world validation – 17 October 2026

**Status: Completed successfully**

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

Real-world results confirmed by the user:

- Automatic live monitoring and ntfy notifications operated at five-minute intervals.
- Notification content and presentation were satisfactory.
- A separate final-result notification was received.
- The final-result notification correctly reported 5–4.

Verified through inspection of the persisted `state.json`:

- Correct Watch ID: `floorball-match-1703572`.
- Correct Match ID: 1703572.
- Final result: IFK Haninge (B) 5 – Tyresö Trollbäcken IBK (A) 4.
- `has_final_result` was `true`.
- `match_status` was `4`.
- The final snapshot contained 30 registered match events.
- All 30 event IDs were unique.
- All five previously existing Watch state entries were preserved.

The second real-world validation was successful.

#### Remaining verification limitations

- Player-specific highlighting has been technically tested but has not been observed during a real match involving Lukas.
- Updated empty-net goal formatting has not yet been verified during a suitable real event.
- A complete comparison of individual notifications with the official match-event history has not been performed.
- The absence of duplicate notifications has not been independently verified through notification history.
- Handling of corrected or deleted match events requires further evaluation.

These limitations do not prevent preparation of the initial Floorball release but must not be described as verified capabilities.

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

The core also sends notifications before saving updated state. A notification or execution failure can therefore result in a change being detected again during a later execution.

No corresponding production incident has been confirmed.

### Floorball

- Automatic discovery of upcoming matches is not implemented.
- Live monitoring currently requires manual Watch configuration.
- The Live workflow uses a specific `WATCH_ID`.
- Multiple simultaneous Live Watches are not yet operationally supported through the current workflow configuration.
- Handling of corrected or deleted match events requires further evaluation.
- Notification preferences are not configurable.
- The complete iBIS event-type model has not been documented.
- Player-specific highlighting remains unverified during a relevant real-world player event.
- Updated empty-net goal formatting remains to be verified in real-world operation.
- GitHub Actions production runtime compatibility requires verification following the October 2026 updates.

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

### Floorball development – Implementation and validation completed

The first floorball connector has been implemented and technically verified.

Two real-world match validations were successfully completed:

- 15 October 2026 – Huddinge IBS vs Tyresö Trollbäcken IBK.
- 17 October 2026 – IFK Haninge (B) vs Tyresö Trollbäcken IBK (A).

The implementation has not yet been included in a published production release.

The verified functionality is considered sufficient to prepare the first Floorball release.

### Planned release – v1.3.0

**Status: Preparation in progress – Not yet published**

Proposed scope:

- Include the implemented `ibis_floorball` connector.
- Include floorball-specific notification formatting.
- Include the permanent pre-match baseline workflow.
- Include automated Floorball tests.
- Include the new platform regression test workflow.
- Preserve the existing v1.2 architecture and production connectors.

Release preparation completed on 19 October 2026:

- Two real-world Floorball validations documented.
- Floorball automated tests passed.
- Golf regression tests passed using mocked data.
- Both test workflows updated to `checkout@v5` and `setup-python@v6`.
- Both test workflows passed after the updates.
- Node.js 20 warnings removed from the test workflows.
- Daily and Live production workflows updated to the same Actions versions.
- Live schedule disabled in cron-job.org after the completed match.

Remaining release verification:

1. Verify the scheduled Daily execution on 20 October 2026 at 08:00.
2. Verify Live workflow compatibility after the GitHub Actions version update.
3. Confirm Playwright and Chromium compatibility in production workflows.
4. Review remaining warnings and known limitations.
5. Confirm final release scope.
6. Publish v1.3.0 only after explicit approval.

No new release has been created.

### Next development phase – Automatic floorball match discovery

**Status: Agreed direction – Design not started**

After the first Floorball release, begin a separate design phase for automatic identification and monitoring of matches.

Initial goal:

Automatically identify upcoming matches for the teams and competitions in which Lukas Widegren participates.

Monitoring should continue for the selected teams regardless of whether Lukas participates in an individual match.

Desired capabilities:

- Configure selected teams and competitions.
- Discover upcoming matches automatically.
- Support multiple teams and competitions.
- Avoid manual MatchID configuration for every match.
- Avoid manually changing `WATCH_ID` between matches.
- Handle postponed and cancelled matches.
- Preserve stable Watch identities and existing state.
- Reuse the Event Platform core wherever possible.

Before implementation, resolve the design questions concerning:

- Match discovery.
- Watch granularity.
- Multiple simultaneous Live Watches.
- Safe concurrent state persistence.
- Match activation and completion.
- Team and competition identification.

The iBIS competition match-list endpoint has already been identified as a potential discovery mechanism.

Architectural changes must be designed, reviewed and agreed before implementation.

### Recommended next goal

Complete the remaining release verification for v1.3.0.

Next session:

1. Review the scheduled Daily execution from 20 October 2026 at 08:00.
2. Confirm that the workflow completed successfully with the updated Actions versions.
3. Verify Playwright and Chromium installation and operation.
4. Determine a safe Live workflow verification approach.
5. Review release readiness and obtain explicit approval before publication.

After v1.3.0, begin the design phase for automatic floorball match discovery.

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
