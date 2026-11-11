# Event Platform – Backlog

GitHub is the authoritative source of truth.

Backlog items are not commitments to a particular release
unless explicitly agreed.

**Last updated:** 11 November 2026
**Last documented published release:** v1.2.0
**Operational status:** Daily and Live schedules re-enabled
**Current focus:** Operational acceptance after iBIS v2 recovery

## 1. Immediate priorities

### P0 – Restore iBIS data acquisition

**Status: Implemented and verified against real data**

The old StatsAppApi startkit endpoint returned HTTP 503.

The replacement public-client flow uses:

1. GET /v2/api/auth/startkit
2. POST /v2/api/auth/handshake
3. Signed requests to /v2/api/public/

The handshake establishes a session cookie and returns:

- ss: session signing secret.
- st: server timestamp.

Requests include Bearer authorization and:

- X-Signature.
- X-Timestamp.
- X-Nonce.

The signing implementation was established by inspecting the
public statistics client's JavaScript.

The signature uses HMAC-SHA256 with the UTF-8 session secret.
The canonical request includes method, path and optional query,
timestamp, UUID nonce and SHA-256 hash of the request body.

Implemented:

- [x] Shared ibis_client.py.
- [x] Connector integration.
- [x] Discovery integration.
- [x] API-root and handshake validation.
- [x] Read-only resource validation.
- [x] Redirect rejection.
- [x] Seven isolated client tests.
- [x] Existing Discovery tests adapted.

Verified on 11 November:

- [x] Match 1750719 retrieved from GitHub Actions: HTTP 200.
- [x] Competition 45004 retrieved: HTTP 200, 110 matches.
- [x] Expected match found in competition response.
- [x] Production connector retrieved match 1750693 and 24 events.
- [x] Six notification-formatting tests passed.
- [x] Baseline test passed without sending a notification.
- [x] 112 Floorball regression tests passed after integration.
- [x] Golf regression step passed.
- [x] Standalone Discovery succeeded against real data.
- [x] Production Daily completed through Discovery.
- [x] Manual production Live execution succeeded.

Personal iBIS credentials and copied browser sessions were not
required for the verified implementation.

Remaining:

- [ ] Verify acquisition throughout an active match.
- [ ] Verify notification delivery during that match.
- [ ] Verify final-result handling with the new client.

The authentication blocker is resolved. Full active-match
acceptance after recovery remains outstanding.

### P0 – Restore operational scheduling

**Status: Both schedules re-enabled; Live automatic execution verified**

Daily:

- Schedule: 08:00 Europe/Stockholm.
- Manual production execution passed.
- User confirmed external job re-enabled.
- [ ] Observe the next scheduled automatic Daily execution.

Live:

- Schedule: Every five minutes, 06:00–23:55.
- Timezone: Europe/Stockholm.
- Cron expression: */5 6-23 * * *
- External dispatch returned HTTP 204.
- Corresponding GitHub Actions execution succeeded in 30 seconds.

The verified automatic Live execution processed two unchanged
golf Watches and required no persistence.

No Floorball match was eligible during that execution.

Daily installation issue:

- --with-deps stalled while downloading Ubuntu font packages.
- Daily now installs Chromium without --with-deps.
- The subsequent production Daily execution succeeded.

Do not treat a successful scheduler dispatch alone as successful
monitoring. Verify the corresponding GitHub Actions result.

### P0 – Investigate missing late-match notifications

**Status: Open incident – 25 October 2026**

Match:

Tyresö Trollbäcken IBK (A) – Älta IF A

MatchID: 1703577

Observed:

- Notifications worked earlier in the match.
- Last received notification referred to 10–4.
- Final two goals and final-result notification were not received.
- Final result 11–5 was persisted.
- has_final_result: true.
- match_status: 4.
- Registry monitoring_status: completed.

Root cause remains unknown.

Investigation:

- [ ] Review Live logs around match completion.
- [ ] Review Git history for the final state update.
- [ ] Inspect notification generation and delivery.
- [ ] Inspect match-selection behavior.
- [ ] Review available ntfy evidence.
- [ ] Identify the root cause.
- [ ] Add regression coverage if a defect is confirmed.

This incident is separate from the November authentication failure.

### P1 – Complete automatic Floorball acceptance

**Status: Partially verified**

Next match in the inspected registry:

- MatchID: 1703587.
- Tyresö Trollbäcken IBK (A) – Hammarbyhöjden IBK.
- Start: 14 November 2026, 15:00.
- Monitoring activation: 14:45.
- Timezone: Europe/Stockholm.

Acceptance checks:

- [ ] Confirm automatic activation.
- [ ] Confirm pre-match baseline.
- [ ] Observe successful acquisition during play.
- [ ] Compare notifications with official match events.
- [ ] Verify player highlighting when applicable.
- [ ] Verify final-result notification.
- [ ] Verify final snapshot and completed registry status.
- [ ] Check for duplicate notifications.

Avoid nonessential production changes during acceptance.

## 2. Match validation and recovery record

### 15 and 17 October – Manual monitoring

MatchIDs: 1750693 and 1703572.

Previously verified:

- Match acquisition.
- Goals, assists and penalties.
- Period events.
- Final results.
- Notifications.
- State persistence.

Empty-net goals use MatchEventTypeID 12.

### 23 October – Automatic JAS monitoring

MatchID: 1750707.

Verified:

- Automatic monitoring worked.
- Notifications were received.
- Lukas-specific assist highlighting with a star worked.
- Registry completion was subsequently confirmed.

Remaining:

- [ ] Independently review complete notification history.
- [ ] Independently review final snapshot.
- [ ] Confirm exact activation timing.
- [ ] Assess duplicate notifications.

### 25 October – Automatic men's monitoring

MatchID: 1703577.

Verified:

- Monitoring and earlier notifications worked.
- Final state 11–5 persisted.
- Registry became completed.

Remaining:

- [ ] Resolve missing late-match notifications.
- [ ] Verify the complete notification lifecycle.

### 28 October

MatchID: 1703581.

User reported successful monitoring.
Registry completion was confirmed.

- [ ] Independently verify final snapshot and notification history.

### 30 October

MatchID: 1750712.

Registry completion was confirmed.

- [ ] Independently verify complete notification history.

### 6 November – Missed match

MatchID: 1750719.

Monitoring failed during the authentication outage.

On 11 November:

- Registry still recorded scheduled.
- No floorball-match-1750719 entry existed in state.json.
- Existing selection rules would still select this overdue match.
- Live would reject its late first observation.

The user approved minimal administrative closure:

- [x] monitoring_status manually changed to completed.
- [x] No historical notifications sent.
- [x] No final snapshot added.
- [x] Existing state preserved.

This is an explicit exception, not successful match monitoring.
Do not recreate a baseline or reactivate this match.

## 3. Implemented platform capabilities

### Golf monitoring

Connectors:

- golfbox_leaderboard
- sgf_ranking
- tournytt_api

Previously verified:

- Live scoring and position changes.
- Multi-round competitions and round transitions.
- Final results.
- Daily ranking monitoring.
- State persistence and notifications.

Golf regression passed during the November recovery.

### Automatic Discovery

Implemented:

- Configured teams and competitions.
- Competition match-list retrieval.
- Team and date filtering.
- Registry creation and schedule updates.
- Preservation of completed and unrelated matches.
- Git persistence.

Recovery verification returned 31 total registry entries and
zero changes.

This does not mean 31 new or upcoming matches were discovered.
The registry includes preserved historical entries.

No real registry write was needed during the recovery verification.

### Automatic Live monitoring

Implemented:

- Dynamic Watch selection.
- Multiple eligible matches.
- Activation 15 minutes before start.
- Stable Watch IDs.
- Preservation of configured golf Watches.
- Automatic completion.
- Coordinated Git persistence.

### Git persistence

Implemented and regression-tested:

- Explicit registry ownership.
- Preservation of unrelated state.
- Push retries.
- Optimistic same-Watch conflict checks.
- Coordinated final-snapshot and completion commits.

Real-world final-state persistence was confirmed on 25 October.

### Consolidated regression testing

Permanent workflow:

.github/workflows/test-regression.yml

Latest confirmed Floorball result:

112 tests passed on 11 November 2026 after v2 integration.

The separate golf regression step also passed.

New tests should normally join this suite.
Do not create a workflow for every individual test.

## 4. Reliability improvements

### External API failure isolation

**Status: Not implemented**

Evaluate:

- Bounded retries and backoff.
- Failure classification.
- Clearer diagnostics.
- Preservation of last valid state.
- Alerts for repeated failures.
- Isolation of unrelated Watches and connectors.

Retries are not a solution to persistent authorization failures.

Allowing golf to continue independently during Floorball failures
requires an explicit design decision.

### Late first-observation recovery

**Status: Not implemented**

The runner rejects a first Floorball observation containing
activity or a final result.

Evaluate:

- Safe recovery baselines.
- Historical-event handling.
- Explicit notification behavior.
- Reconciliation after outages.

The manual closure of match 1750719 is not a general recovery
implementation.

### Overdue match expiration

**Status: Not implemented**

Selection has no upper time limit after activation.

An overdue match remains eligible until completed, cancelled
or postponed.

Design recovery and expiration rules before changing selection.
Do not silently discard delayed matches or historical state.

### Notification delivery and persistence

**Status: Known limitation**

Notifications are sent before Git persistence.

Delivery can succeed while persistence fails, resulting in
duplicate notifications on a subsequent execution.

Exactly-once delivery is not guaranteed.

Potential improvements:

- Persistent notification identifiers.
- Delivery coordination.
- Outbox or equivalent mechanism.

### Corrected and deleted events

**Status: Not implemented**

Evaluate corrected event details, deleted events, corrected
scores and source revisions.

### Concurrent monitoring

**Status: Partially addressed**

Implemented:

- Shared workflow concurrency group.
- Git retries.
- Optimistic same-Watch checks.
- Preservation of unrelated state.

Remaining:

- [ ] Verify realistic overlapping executions.
- [ ] Improve diagnostics and recovery behavior.

### iBIS source model

- [ ] Verify interpretation of timestamps without UTC offsets.
- [ ] Verify provisional cancellation and abandonment fields.
- [ ] Document the complete relevant event-type model.

## 5. Authentication and scheduling maintenance

### GitHub scheduler token

Renewed and verified on 29 October 2026.

Both cron-job.org jobs use Bearer authorization.

Token expiration: 28 November 2026.

- [ ] Renew before expiration.
- [ ] Update both jobs.
- [ ] Verify dispatch and workflow execution.
- [ ] Consider a more maintainable authentication arrangement.

This token is separate from temporary iBIS authentication.

Never store tokens in repository documentation.

## 6. Notification and golf improvements

### Floorball presentation

Implemented highlighting covers goals, assists and penalties.

Assist highlighting was verified in real operation on 23 October.

- [ ] Observe qualifying highlighted-player goals.
- [ ] Observe qualifying highlighted-player penalties.
- [ ] Further verify empty-net goal presentation: (tom bur).
- [ ] Improve match-start wording.
- [ ] Evaluate additional event types.
- [ ] Introduce configurable notification preferences.

### GolfBox

- [ ] Evaluate richer individual-hole notifications using hole
      scores, strokes, score classes, totals and position.

### SGF Ranking

- [ ] Show previous and new values for ranking position,
      points and competition count.

### Tournytt

- [ ] Improve presentation of position, score, to-par,
      played holes and competition class.

### Min Golf

- [ ] Investigate availability of entry lists, start lists
      and upcoming competitions before implementation.

## 7. Release and repository maintenance

### First Floorball release

**Status: Not published**

Last documented published release remains v1.2.0.

Before a new release:

- [ ] Complete or explicitly assess operational acceptance.
- [ ] Assess unresolved incidents.
- [ ] Agree on release scope.
- [ ] Run relevant regression tests.
- [ ] Update documentation.
- [ ] Obtain explicit approval.
- [ ] Publish the agreed release.

Do not infer a release solely from deployed code.

### Workflow consolidation

After operational recovery and acceptance:

- [ ] Inventory existing workflows.
- [ ] Confirm scheduler dependencies.
- [ ] Preserve daily.yml and live.yml.
- [ ] Preserve test-regression.yml.
- [ ] Review floorball-baseline.yml.
- [ ] Review floorball-daily-discovery.yml.
- [ ] Review test-floorball.yml.
- [ ] Review test-ibis-new-api.yml after recovery documentation.
- [ ] Retain useful diagnostics and Python tests.
- [ ] Remove redundant workflows only after verification.

### Modules and configuration

- [ ] Identify production and test imports.
- [ ] Review unused modules before deletion.
- [ ] Remove obsolete manual Floorball Watches after acceptance.
- [ ] Preserve historical state.
- [ ] Verify Daily and Live after cleanup.

## 8. Future platform opportunities

No implementation commitment has been made.

### Connector development guidance

- [ ] Document source identification and inspection.
- [ ] Document configuration and normalization.
- [ ] Document baseline and notification verification.
- [ ] Document safe scheduling activation.
- [ ] Create a reusable connector template.

### Longer-term capabilities

- Multi-user subscriptions and preferences.
- Additional teams and competitions.
- Additional event sources.
- REST API, web or mobile interface.
- Alternative notification providers.
- Improved operational diagnostics.

## 9. Documentation and conversation lifecycle

GitHub remains the authoritative source of truth.

Pending documentation reconciliation for the November recovery:

- [x] Replacement PROJECT_CONTEXT.md committed by the user.
- [ ] Update this backlog and confirm commit.
- [ ] Update docs/ARCHITECTURE.md.
- [ ] Update docs/decisions.md.
- [ ] Update README.md.
- [ ] Update docs/ways-of-working.md.
- [ ] Reconcile relevant design documentation where necessary.
- [ ] Refresh ChatGPT Project sources from committed versions.

Required process additions:

- Verify PROJECT_CONTEXT.md freshness at session start.
- Request the current GitHub file when freshness is uncertain.
- Refresh the ChatGPT Project source after committing handover
  updates.

Continue using independent new project conversations.
Do not depend on long, branched or unfinished Work conversations.

The previously stalled Work continuation is not authoritative
technical evidence.

Before changing conversations:

- Record verified results and unresolved issues.
- Commit the required documentation.
- Keep the handover concise.
- Identify the next goal.
- Refresh the Project sources.

## Next development priority

Verify scheduled Daily execution and complete real-world
Floorball acceptance after iBIS v2 recovery.

The next registered match is 14 November 2026 at 15:00,
with monitoring activation at 14:45, Europe/Stockholm.

Protect working monitoring during the match.
