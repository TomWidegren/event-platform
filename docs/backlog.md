
# Event Platform – Backlog

This document tracks completed validation, outstanding work,
technical improvements and future opportunities for Event Platform.

Backlog items are not commitments to a particular release unless
explicitly agreed.

GitHub is the authoritative source of truth.

**Last documented published release:** v1.2.0

**Current implementation:** Automatic Floorball Discovery and Live Monitoring

**Operational status:** Daily and Live external schedules disabled following iBIS API failures.

**Last updated:** 11 November 2026

---

## 1. Immediate priorities

### P0 – Restore iBIS match-data access

**Status: Blocked – v2 authentication investigation incomplete**

**Priority: Highest**

#### Background

Event Platform previously accessed Swedish Floorball match data through the iBIS API.

The original authentication endpoint was:

`https://api.innebandy.se/StatsAppApi/api/startkit`

This returned an `accessToken` and `apiRoot`.

The connector then retrieved match data using a Bearer token.

This implementation worked during multiple real-world matches in October 2026.

In early November, both Daily Discovery and Live Monitoring began failing.

#### Verified failure

The old startkit endpoint returns:

`HTTP 503 Service Unavailable`

The error was reproduced in:

- GitHub Actions Daily Discovery.
- GitHub Actions Live Monitoring.
- A normal web browser.

Both cron-job.org schedules were subsequently disabled by the user to prevent repeated failures and email notifications.

The exact date of the manual shutdown has not been independently established.

No production connector changes have been made during the v2 investigation.

#### New v2 API

The public statistics website uses:

`GET https://api.innebandy.se/v2/api/auth/startkit`

This returns:

- `accessToken`
- `apiRoot`

The observed API root is:

`https://api.innebandy.se/v2/api/public/`

The public website also uses:

`POST https://api.innebandy.se/v2/api/auth/handshake`

Match data is retrieved from:

`GET /v2/api/public/matches/{match_id}`

The new startkit and handshake endpoints have both been verified from GitHub Actions.

#### Verified diagnostic results

| Operation | Result |
|---|---|
| Old startkit | HTTP 503 |
| New v2 startkit | HTTP 200 |
| New v2 handshake | HTTP 200 |
| Session cookie after startkit | None |
| Session cookie after handshake | Created |
| Handshake JSON fields | `ss`, `st` |
| Handshake response header | `X-Session-Hash` |
| Match retrieval from Chrome | HTTP 200 |
| Match retrieval from Python | HTTP 401 |

The Python test used a new `requests.Session()`.

It did not reuse browser cookies or copied authentication tokens.

The handshake successfully established a session, but the subsequent match request was rejected.

The 401 response did not expose a recognized error code or useful authentication explanation in the diagnostic output.

#### Additional browser observations

The working browser request includes:

- `Authorization`
- `Cookie`
- `Origin`
- `Referer`
- `X-Nonce`
- `X-Signature`
- `X-Timestamp`

The handshake request includes:

- `Authorization`
- `Cookie`
- `Origin`
- `Referer`

The handshake request does not include:

- `X-Nonce`
- `X-Signature`
- `X-Timestamp`

Both handshake and match responses include:

`X-Session-Hash`

These observations suggest that v2 uses additional request validation or signing.

The signing algorithm, session requirements and exact cause of HTTP 401 have not been established.

Do not assume that `X-Session-Hash`, `ss` or `st` can be used interchangeably with the request signature.

#### Official API documentation

The published v2 API documentation includes:

`POST /api/login`

The documented login request requires:

- `UserName`
- `Password`

The response includes:

- `AccessToken`
- `TokenExpirationTime`

This is distinct from the public statistics website's observed startkit and handshake flow.

No supported external-client specification for the website's request-signing mechanism was identified during the investigation.

The documented API access model may require separate authorization.

#### Existing diagnostic workflow

`.github/workflows/test-ibis-new-api.yml`

This workflow was created during the investigation.

It has been used for several isolated, read-only tests.

The latest diagnostic test verified:

- Startkit HTTP 200.
- Handshake HTTP 200.
- Session established.
- Match retrieval HTTP 401.
- No recognized error fields.

Important:

The workflow may report GitHub Actions success even when match retrieval returns HTTP 401, because authorization failure is handled as a diagnostic result.

Do not interpret a green workflow as successful match-data retrieval.

#### Next investigation

- [ ] Confirm the intended and permitted v2 authentication method for the required match-data access.
- [ ] Investigate available official client documentation or supported integration methods.
- [ ] Determine whether signed requests are supported for external clients.
- [ ] Verify complete read-only match retrieval from GitHub Actions.
- [ ] Verify access to competition match lists used by Discovery.
- [ ] Verify that response schemas remain compatible with existing normalization.
- [ ] Review and agree on the minimum necessary implementation changes.
- [ ] Run appropriate regression tests.
- [ ] Verify controlled Daily and Live executions.
- [ ] Re-enable external schedules only after successful verification.

Do not change production code or attempt to bypass access controls.

#### Architectural constraint

Retain the existing Event Platform architecture.

Connectors continue to expose:

`fetch_snapshot(watch)`

Authentication and acquisition remain connector responsibilities.

Do not modify state persistence, notification formatting or scheduling merely to accommodate an API authentication change.

A shared authentication helper may be considered separately if justified.

---

### P0 – Restore operational scheduling safely

**Status: Both cron-job.org schedules disabled**

Affected jobs:

- Event Platform – Daily
- Event Platform – Live

The jobs were disabled after repeated execution failures.

The original GitHub token issue from October was resolved before these failures.

The current iBIS failure is a separate issue.

Before reactivation:

- [ ] Verify working iBIS access.
- [ ] Verify Daily Discovery.
- [ ] Verify Live match acquisition.
- [ ] Confirm no unintended state changes.
- [ ] Confirm GitHub Actions success.
- [ ] Confirm both cron-job.org configurations.
- [ ] Reactivate schedules deliberately.
- [ ] Observe subsequent automatic executions.

Consider whether golf monitoring should be allowed to continue independently when iBIS is unavailable.

This requires an explicit design decision rather than an unreviewed workflow change.

---

### P0 – Investigate missing late-match notifications

**Status: Open incident – 25 October 2026**

Match:

Tyresö Trollbäcken IBK (A) – Älta IF A

MatchID: `1703577`

Observed:

- Notifications worked earlier in the match.
- The last received notification referred to 10–4.
- Later goals and the final-result notification were not received.
- Final result 11–5 was persisted.
- `has_final_result: true`.
- `match_status: 4`.
- Registry status: `completed`.

The root cause remains unknown.

Investigation:

- [ ] Review Live execution logs around match completion.
- [ ] Review Git history for the final state update.
- [ ] Inspect notification generation and delivery behavior.
- [ ] Inspect match-selection time-window behavior.
- [ ] Review available ntfy evidence.
- [ ] Identify the root cause.
- [ ] Add regression coverage if a defect is confirmed.

This incident remains separate from the November API failure.

---

### P1 – Complete automatic Floorball acceptance

**Status: Partially verified**

#### 23 October – JAS

MatchID: `1750707`

Verified:

- Automatic monitoring worked.
- Match notifications were received.
- Lukas-specific assist highlighting with ⭐ worked.
- Registry completion was later confirmed.

Remaining:

- [ ] Complete notification history.
- [ ] Final snapshot independently reviewed.
- [ ] Exact activation timing.
- [ ] Duplicate-notification assessment.

#### 25 October – Herrar

MatchID: `1703577`

Verified:

- Automatic monitoring worked.
- Notifications were received earlier in the match.
- Final state 11–5 persisted.
- Registry status became `completed`.

Remaining:

- [ ] Resolve missing late-match notifications.
- [ ] Verify complete notification lifecycle.

#### 28 October – Herrar

MatchID: `1703581`

User reported successful monitoring.

Registry status:

`completed`

Remaining:

- [ ] Independently verify final snapshot and notification history.

#### 30 October – JAS

MatchID: `1750712`

Registry status:

`completed`

Complete notification history has not been independently verified.

#### 6 November – JAS

MatchID: `1750719`

The match was present in the registry with:

- Scheduled start: 19:45.
- `monitoring_status: scheduled`.
- `cancelled: false`.
- `postponed: false`.

Live selected three Watches in a failed execution.

The iBIS connector failed at the old startkit endpoint with HTTP 503.

Match monitoring was therefore not successfully completed.

---

## 2. Completed implementation and verification

### Golf monitoring

**Status: Previously operational and validated**

Connectors:

- `golfbox_leaderboard`
- `tournytt_api`
- `sgf_ranking`

Verified capabilities:

- Live scoring.
- Position changes.
- Multi-round competitions.
- Round transitions.
- Final results.
- Daily ranking monitoring.
- Persistent state.
- Notifications.

Existing golf regression tests passed on 22 October 2026.

### Initial Floorball connector

**Status: Implemented and previously validated**

Real-world validations:

15 October 2026:

Huddinge IBS – Tyresö Trollbäcken IBK

MatchID: `1750693`

17 October 2026:

IFK Haninge (B) – Tyresö Trollbäcken IBK (A)

MatchID: `1703572`

Verified:

- iBIS match acquisition.
- Goals.
- Assists.
- Penalties.
- Period events.
- Final results.
- Notifications.
- State persistence.

Empty-net goals were identified as MatchEventTypeID 12.

### Automatic Floorball Discovery

**Status: Implemented; currently blocked by API access**

Capabilities:

- Configured teams and competitions.
- Match-list retrieval.
- Team filtering.
- Match registry updates.
- Schedule updates.
- Preservation of completed matches.
- Git persistence.

Verified on 22 October:

- 31 matches discovered.
- Registry persisted.
- Repeated execution detected zero changes.
- Manual Daily integration passed.

### Automatic Live Monitoring

**Status: Implemented; currently blocked for Floorball**

Capabilities:

- Dynamic Watch selection.
- Multiple eligible matches.
- Activation 15 minutes before match start.
- Stable Watch IDs.
- Preservation of golf Watches.
- Automatic match completion.
- Coordinated Git persistence.

Real-world monitoring worked during October before the API failure.

### Coordinated Git persistence

**Status: Implemented and technically verified**

Includes:

- Registry field ownership.
- Preservation of unrelated state.
- Git push retries.
- Optimistic concurrency checking.
- Coordinated final-state and completion commits.

Real-world final-state persistence was confirmed on 25 October.

### Consolidated regression testing

Permanent workflow:

`.github/workflows/test-regression.yml`

Last confirmed complete run:

22 October 2026.

Results:

- 105 Floorball tests passed.
- Existing golf regression tests passed.

No equivalent complete regression result has been documented after the November API investigation.

### Live workflow optimization

**Status: Completed and verified**

Measured execution times:

- Before optimization: 4 minutes 20 seconds.
- Optimized manual execution: approximately 37 seconds.
- Subsequent automatic execution: approximately 30 seconds.

---

## 3. Authentication and scheduling maintenance

### GitHub scheduler token

**Status: Renewed and verified on 29 October 2026**

Both cron-job.org jobs were updated with the renewed GitHub token.

Authorization format:

`Bearer <token>`

Both jobs returned HTTP 204 and successfully triggered GitHub Actions.

Token expiration:

**28 November 2026**

Future action:

- [ ] Renew before expiration.
- [ ] Update both cron-job.org jobs.
- [ ] Verify API dispatch and GitHub Actions execution.
- [ ] Consider a more maintainable authentication arrangement.

Never store tokens in repository documentation.

### External scheduling

cron-job.org remains the external scheduler.

The current schedules are disabled.

Do not confuse the GitHub scheduler token with iBIS authentication.

---

## 4. Release management

### First Floorball production release

**Status: Not published**

Last documented published release:

v1.2.0

Floorball functionality was implemented after v1.2.0.

Before a new release:

- [ ] Restore stable match-data acquisition.
- [ ] Resolve or explicitly assess operational incidents.
- [ ] Complete required acceptance.
- [ ] Confirm release scope.
- [ ] Run regression tests.
- [ ] Update release documentation.
- [ ] Obtain explicit approval.
- [ ] Publish the agreed release.

Do not assume v1.3.0 has been released.

---

## 5. Reliability improvements

### External API resilience

**Status: Identified improvement**

Potential work:

- Bounded retries.
- Exponential backoff.
- Failure classification.
- Improved diagnostics.
- Preservation of last known valid state.
- Alerting for repeated failures.
- Isolation of unrelated Watches and connectors.

Retries must not be treated as a solution to persistent authorization failures.

### Notification delivery and persistence

**Status: Known limitation**

Notifications are sent before state persistence.

If delivery succeeds but persistence fails, notifications may repeat.

Exactly-once delivery is not guaranteed.

Potential improvements:

- Persistent notification identifiers.
- Stronger delivery coordination.
- Outbox or equivalent mechanism.

### Late first-observation recovery

**Status: Not implemented**

The automatic runner rejects a first observation that already contains match activity.

Future work:

- Safe baseline recovery.
- Historical-event handling.
- Controlled notification behavior.

### Corrected and deleted match events

**Status: Not implemented**

Evaluate:

- Corrected event details.
- Deleted events.
- Corrected scores.
- Source revisions.

### Concurrent monitoring reliability

**Status: Partially addressed**

Implemented:

- Shared workflow concurrency group.
- Git persistence retries.
- Optimistic same-Watch protection.
- Preservation of unrelated state.

Remaining:

- [ ] Verify realistic overlapping executions.
- [ ] Improve diagnostics.
- [ ] Review recovery behavior.

---

## 6. Floorball notification improvements

### Player-specific highlighting

**Status: Assist highlighting verified**

Supported event types:

- Goals.
- Assists.
- Penalties.

Lukas-specific assist highlighting with ⭐ was verified on 23 October 2026.

Goal and penalty highlighting remain to be observed during qualifying real-world events.

### Empty-net goal formatting

**Status: Implemented; further real-world verification pending**

MatchEventTypeID 12 is treated as an empty-net goal.

Presentation:

`(tom bur)`

### Additional improvements

- Improve match-start wording.
- Evaluate additional event types.
- Introduce configurable notification preferences.
- Improve notification presentation.

---

## 7. Golf monitoring improvements

### GolfBox hole-by-hole monitoring

**Status: Not started**

Evaluate richer hole-by-hole notifications using:

- Individual hole scores.
- Strokes.
- Score classes.
- Total score.
- Leaderboard position.

### SGF Ranking notification changes

**Status: Not started**

Show previous and new ranking values.

Example:

    Placering: 1204 → 1143
    Poäng: 4,32 → 5,30
    Tävlingar: 6 → 7

### Tournytt notification formatting

**Status: Not started**

Improve:

- Position.
- Score.
- To par.
- Played holes.
- Competition class.

### Min Golf integration

**Status: Future opportunity**

Potential sources:

- Entry lists.
- Start lists.
- Upcoming competitions.

Verify availability before implementation.

---

## 8. Platform improvements

### Connector Development Guide

**Status: Not started**

Document a repeatable process:

1. Identify the external platform.
2. Check existing connectors.
3. Inspect source behavior.
4. Define source configuration.
5. Implement the connector.
6. Establish baseline.
7. Verify change detection.
8. Verify notifications.
9. Enable scheduling.

### Connector template

**Status: Not started**

Create a reusable reference implementation following:

`fetch_snapshot(watch)`

### Multi-user support

**Status: Long-term opportunity**

Potential capabilities:

- Multiple recipients.
- User profiles.
- Subscription management.
- Notification preferences.

### User interfaces and external access

**Status: Long-term opportunity**

Potential capabilities:

- REST API.
- Web interface.
- Mobile application.

No implementation commitment has been made.

---

## 9. Technical cleanup

### Consolidate GitHub Actions workflows

**Status: Planned**

The repository contains numerous historical test-workflows.

Actions:

- [ ] Inventory workflows.
- [ ] Confirm external scheduler dependencies.
- [ ] Preserve `daily.yml`.
- [ ] Preserve `live.yml`.
- [ ] Preserve `test-regression.yml`.
- [ ] Retain useful manual diagnostic workflows.
- [ ] Review `floorball-baseline.yml`.
- [ ] Review `floorball-daily-discovery.yml`.
- [ ] Retain `test-ibis-new-api.yml` until the investigation is complete.
- [ ] Remove redundant standalone workflows after verification.
- [ ] Run consolidated regression tests.

### Review obsolete Python modules

**Status: Planned**

- [ ] Identify production imports.
- [ ] Identify test-only dependencies.
- [ ] Identify unused modules.
- [ ] Remove obsolete code only after verification.

### Remove obsolete manual Floorball Watches

**Status: Planned**

Historical manual Watches remain in `config.yml`.

Automatic Live execution excludes them.

After operational recovery:

- [ ] Confirm automatic monitoring.
- [ ] Preserve historical state.
- [ ] Remove obsolete manual configuration.
- [ ] Verify Daily and Live.

### Documentation and conversation lifecycle

**Status: Handover preparation – 11 November 2026**

The latest extended development conversation became excessively long.

A separate Work continuation inherited substantial context and became stuck in a long-running Thinking state.

Observed:

- Work displayed more than 43 hours of elapsed time.
- No Stop control was available.
- A subsequent user message resulted in `Unknown error`.
- The actual background execution status could not be independently confirmed.

This is a ChatGPT workflow issue, not an Event Platform production incident.

Process improvement required:

- [ ] Update `docs/ways-of-working.md`.
- [ ] Prefer a completely new conversation inside the Event Platform project.
- [ ] Avoid continuing or branching from excessively long conversations.
- [ ] Restore context from current GitHub documentation.
- [ ] Keep `PROJECT_CONTEXT.md` concise and current.
- [ ] Document substantial findings before changing conversations.
- [ ] Do not rely on unresolved Work conversations for project handover.

The stalled Work continuation must not be treated as an authoritative source of technical results.

---

## 10. Documentation and source of truth

GitHub is the authoritative source of truth.

Important documents:

- `PROJECT_CONTEXT.md`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/decisions.md`
- `docs/backlog.md`
- `docs/ways-of-working.md`
- `docs/design-floorball.md`
- `docs/design-floorball-automation.md`
- `docs/design-v1.2.md`

This backlog records the iBIS v2 investigation through
11 November 2026.

The next development conversation should begin with the current
repository documentation rather than reconstructing the investigation
from conversation history.

## Next development priority

Restore authorized, reliable iBIS match-data acquisition.

Do not repeat completed diagnostic tests unnecessarily.

Do not change production code before agreeing on a verified
integration approach.

Keep Daily and Live schedules disabled until controlled
verification supports reactivation.
