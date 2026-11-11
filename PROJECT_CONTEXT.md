
# Event Platform – Project Context

**Last updated:** 11 November 2026

**Last development checkpoint:** 11 November 2026

**Project:** Event Platform

**Last documented published release:** v1.2.0

**Current development:** Restore iBIS match-data access

**Operational status:** Daily and Live schedules disabled

## 1. Purpose

Event Platform monitors external event data, detects relevant changes, maintains persistent state and sends notifications.

Golf was the first use case. Swedish Floorball was subsequently added through the iBIS connector.

The architecture is designed to remain independent of individual sports, data sources and acquisition technologies.

**GitHub is the authoritative source of truth.**

ChatGPT conversations, Project files and previous attachments must not be assumed to reflect the latest GitHub repository.

## 2. Current architecture

The last documented published release is v1.2.0.

It established the Unified Connector Interface:

`fetch_snapshot(watch)`

Implemented connectors:

- `sgf_ranking`
- `golfbox_leaderboard`
- `tournytt_api`
- `ibis_floorball`

The platform supports:

- Daily monitoring.
- Live monitoring.
- Stable Watch IDs.
- Connector-specific configuration.
- Normalized snapshots.
- Change detection.
- Notification formatting.
- ntfy delivery.
- Persistent Git-based state.

Floorball development after v1.2.0 introduced:

- Automatic match discovery.
- Persistent match registry.
- Automatic match selection.
- Dynamic Live Watches.
- Multiple simultaneous Watches.
- Automatic match completion.
- Coordinated Git persistence.
- Consolidated regression testing.

These capabilities were implemented and technically verified.

The Floorball implementation has not yet been included in a confirmed published release.

For architecture details, see:

`docs/ARCHITECTURE.md`

For implementation history, see:

`docs/design-floorball-automation.md`

## 3. Current production status

### Scheduling

cron-job.org triggers GitHub Actions.

Production workflows:

- `.github/workflows/daily.yml`
- `.github/workflows/live.yml`

Normal schedules:

- Daily: 08:00 Europe/Stockholm.
- Live: Every five minutes.

**Both external schedules are currently disabled.**

The user disabled them after repeated execution failures and email notifications in early November 2026.

Do not reactivate them without explicit agreement and successful verification.

### Daily

Daily executes:

1. SGF Ranking monitoring.
2. Automatic Floorball Discovery.

Golf monitoring completed successfully in the inspected failed runs.

Floorball Discovery failed when attempting iBIS authentication.

### Live

Live executes:

`event_platform_live.py`

It combines configured GolfBox and Tournytt Watches with automatically selected Floorball matches.

During the failed execution on 6 November:

- Three Live Watches were selected.
- GolfBox acquisition succeeded.
- Tournytt was unchanged.
- Floorball acquisition failed during authentication.

The entire Live workflow was marked failed.

### Persistent data

Important files:

- `state.json`
- `match_registry.json`
- `config.yml`

Do not reset or delete persistent state during recovery.

The existing registry contains previously discovered matches.

However, it may no longer reflect subsequent schedule changes because Daily Discovery is not running successfully.

## 4. Real-world Floorball validation

### Earlier successful monitoring

**15 October 2026**

MatchID: `1750693`

Manual monitoring verified goals, penalties, period events, final results and notifications.

**17 October 2026**

MatchID: `1703572`

Manual monitoring verified five-minute polling, notifications and final-state persistence.

### Automatic monitoring

**23 October 2026**

MatchID: `1750707`

Automatic monitoring worked.

Lukas Widegren's assist notification was correctly highlighted with ⭐.

This verified player-specific assist highlighting in real-world operation.

**25 October 2026**

MatchID: `1703577`

Automatic monitoring worked during the match.

Final result 11–5 was correctly persisted.

The registry recorded `completed`.

However, the final two goals and final-result notification were not received.

The cause remains unresolved.

**28 October 2026**

MatchID: `1703581`

The user reported successful automatic monitoring.

Registry completion was confirmed.

**30 October 2026**

MatchID: `1750712`

Registry completion was confirmed.

Complete notification history was not independently verified.

**6 November 2026**

MatchID: `1750719`

The match was correctly registered before the API failure.

Live selected three Watches but failed when the Floorball connector attempted authentication.

Successful monitoring was not achieved.

## 5. Current blocking incident – iBIS API

**Priority: P0**

**Status: Open**

### Original implementation

The existing Floorball connector and Discovery use:

`https://api.innebandy.se/StatsAppApi/api/startkit`

This endpoint began returning HTTP 503.

The failure was reproduced in:

- Daily Discovery.
- Live Monitoring.
- A normal web browser.

### iBIS v2 investigation

The public statistics website now uses:

`GET https://api.innebandy.se/v2/api/auth/startkit`

Followed by:

`POST https://api.innebandy.se/v2/api/auth/handshake`

Match data is retrieved from:

`https://api.innebandy.se/v2/api/public/matches/{match_id}`

Verified from GitHub Actions:

| Operation | Result |
|---|---|
| New startkit | HTTP 200 |
| Handshake | HTTP 200 |
| Session cookie | Created |
| Match retrieval | HTTP 401 |

The public statistics website successfully retrieves the same match data in Chrome.

### Authentication findings

The handshake response contains:

- `ss`
- `st`
- `X-Session-Hash`

The working browser match request contains:

- Bearer authorization.
- Session cookie.
- `X-Nonce`.
- `X-Signature`.
- `X-Timestamp`.

These additional headers were not included in the Python diagnostic match request.

The exact authentication and request-signing requirements have not been established.

The HTTP 401 response did not provide a recognized error code or useful explanation.

**Do not assume that a simple startkit URL change resolves the issue.**

### Diagnostic workflow

Existing test workflow:

`.github/workflows/test-ibis-new-api.yml`

This workflow was created during the investigation.

It performs isolated, read-only authentication tests.

The latest diagnostic test confirmed:

- Startkit HTTP 200.
- Handshake HTTP 200.
- Session established.
- Match retrieval HTTP 401.

The workflow may report GitHub Actions success even when match retrieval is denied.

A green workflow does not mean the v2 integration works.

### Current conclusion

The old authentication endpoint is unavailable.

The new v2 authentication endpoint works, but a complete independent match-data request has not yet succeeded.

The precise cause of HTTP 401 remains unverified.

No production connector or Discovery changes have been made during this investigation.

Detailed evidence, outstanding questions and proposed work are documented in:

`docs/backlog.md`

## 6. Other open issues

### Missing late-match notifications

MatchID: `1703577`

Date: 25 October 2026.

The final state was persisted, but the user did not receive the final two goal notifications or final-result notification.

Root cause unknown.

This is separate from the November API failure.

### External API resilience

The November failures demonstrated that one connector failure can cause an entire workflow to fail.

Potential improvements include:

- Better error isolation.
- Bounded retries.
- Clearer failure diagnostics.
- Preservation of unrelated monitoring.

These are future design decisions, not implemented changes.

### GitHub scheduler token

The GitHub personal access token used by cron-job.org was renewed on 29 October 2026.

Both Daily and Live successfully triggered GitHub Actions after renewal.

**Token expiration: 28 November 2026.**

Renew before expiration.

This token is separate from iBIS authentication.

## 7. Verified tests

Permanent regression workflow:

`.github/workflows/test-regression.yml`

Last confirmed complete run:

22 October 2026.

Results:

- 105 Floorball automated tests passed.
- Existing golf regression tests passed.

The November v2 diagnostic tests were not production acceptance tests.

No complete regression run has been documented after the v2 investigation.

## 8. Current development priorities

### First – Restore iBIS data acquisition

1. Establish a supported and reliable v2 authentication method or another permitted data source.
2. Verify complete match retrieval from GitHub Actions.
3. Verify competition match-list retrieval.
4. Confirm compatibility with existing snapshot normalization.
5. Agree on the minimum implementation change.
6. Update relevant source files.
7. Run regression tests.
8. Perform controlled Daily and Live executions.
9. Reactivate external schedules only after successful verification.

Do not repeat completed startkit and handshake diagnostics unnecessarily.

### Second – Investigate notification incident

Determine why the final notifications from 25 October were not received despite successful final-state persistence.

### Third – Improve reliability

Review connector failure isolation, API error handling and recovery behavior.

### Fourth – Repository cleanup

After operational recovery:

- Consolidate redundant GitHub Actions workflows.
- Review obsolete Python modules.
- Remove obsolete manual Floorball Watches.
- Preserve historical state.
- Prepare the next formal release.

The last documented published release remains v1.2.0.

## 9. Documentation and handover

Important repository documents:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/decisions.md`
- `docs/ways-of-working.md`
- `docs/backlog.md`
- `docs/design-floorball.md`
- `docs/design-floorball-automation.md`
- `docs/design-v1.2.md`

This document is the primary session handover.

Detailed technical investigation findings belong in `docs/backlog.md`.

The repository is authoritative.

## 10. Starting the next development session

Start a completely new conversation inside the Event Platform project.

Do not branch or continue from the previous long conversation.

The user should only need to say:

"Nu fortsätter vi med Event Platform."

The assistant should:

1. Read the current `PROJECT_CONTEXT.md`.
2. Read `docs/ways-of-working.md`.
3. Read relevant repository documentation.
4. Identify the current operational status.
5. Confirm the agreed development goal.
6. Request only source files needed for that goal.
7. Continue without repeating completed tests.

Do not assume that project attachments are synchronized with GitHub.

### Recommended next goal

**Restore reliable iBIS match-data acquisition.**

The next session should start from the verified v2 findings rather than reconstructing the investigation from conversation history.

## 11. Conversation lifecycle

A separate Work continuation was created during the iBIS investigation.

It inherited context from the long conversation and subsequently became stuck in a prolonged Thinking state.

The user observed:

- More than 43 hours of elapsed time.
- No available Stop control.
- An `Unknown error` when attempting to send a stop instruction.

The actual background execution status was not independently confirmed.

No unverified results from that Work continuation should be treated as authoritative.

For future development sessions:

- Prefer completely new conversations within the project.
- Restore context from GitHub documentation.
- Avoid branching from excessively long conversations.
- Document important findings before switching conversations.
- Keep the handover concise.

See `docs/ways-of-working.md` for the complete development process.

## 12. Session checkpoint

**Date:** 11 November 2026

Completed:

- Investigated the iBIS API failure.
- Identified the new v2 authentication endpoints.
- Verified startkit and handshake behavior.
- Identified additional browser request headers.
- Confirmed that Python match retrieval remains unauthorized.
- Updated the project backlog.
- Prepared this project context handover.

Not completed:

- Working v2 match-data integration.
- Restoration of Daily and Live scheduling.
- Resolution of the 25 October notification incident.
- Repository cleanup.
- New production release.

No production source-code changes were made during the investigation.

The next session must continue from this documented state.

## Core principle

One goal.

One step.

One verification.

Then the next step.
