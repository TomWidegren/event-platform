
# Event Platform – Backlog

This document tracks completed validation, outstanding work,
technical improvements, and future opportunities for Event Platform.

Backlog items are not commitments to a particular release unless
explicitly agreed.

GitHub is the authoritative source of truth.

**Current documented published release:** v1.2.0

**Current deployed implementation:** Automatic Floorball Discovery
and Live Monitoring, with operational validation ongoing.

**Last updated:** 6 November 2026

---

## 1. Immediate priorities

### P0 – Investigate recurring iBIS Discovery failures

**Status: Open production incident – 6 November 2026**

The Daily workflow failed on two consecutive days, 5 and
6 November 2026.

A manual Daily execution on 6 November reproduced the failure.

Observed error:

`503 Server Error: Service Unavailable`

The error occurred when Floorball Discovery attempted to access
the iBIS `startkit` endpoint for authentication.

Verified observations:

- GitHub Actions started successfully.
- Python dependencies were installed.
- Daily golf monitoring completed.
- Golf state persistence completed.
- Floorball Discovery failed during iBIS authentication.
- The overall Daily workflow was marked failed.
- A manual retry reproduced the same HTTP 503 error.
- Recent Live workflows were reported successful.

Important limitations:

- Successful Live execution does not prove iBIS availability
  when no floorball match is eligible.
- HTTP 503 indicates the service could not handle the request.
  The underlying cause is not established.
- The existing match registry remains available, but Discovery
  cannot refresh schedules while the error persists.

Investigation:

- [ ] Determine whether the iBIS startkit endpoint is available.
- [ ] Compare Discovery and Live authentication behavior.
- [ ] Review current iBIS API responses and relevant headers.
- [ ] Determine whether the issue is temporary service
      unavailability or a changed API behavior.
- [ ] Evaluate bounded retries with backoff.
- [ ] Ensure transient Discovery failures preserve existing
      registry data.
- [ ] Consider clearer separation of golf monitoring success
      and Discovery failure in workflow reporting.
- [ ] Add focused regression tests if implementation changes.
- [ ] Verify successful scheduled Daily Discovery execution.

Do not change production code before reviewing evidence.

### P0 – Protect Live Monitoring for 6 November match

**Status: Match registered; operational verification pending**

Match:

Tyresö Trollbäcken IBK – IFK Gnesta/FBC Nyköping

Competition: Juniorallsvenskan

MatchID: `1750719`

Scheduled start: 6 November 2026 at 19:45 Europe/Stockholm.

Expected automatic activation: 19:30.

Verified from `match_registry.json` on 6 November:

- Correct MatchID.
- Correct scheduled start.
- `monitoring_status: scheduled`.
- `cancelled: false`.
- `postponed: false`.

The match was registered before the recurring Discovery failures.

Therefore, the existing registry contains the information
needed for automatic Live selection, provided the schedule
has not changed.

Remaining verification:

- [ ] Confirm automatic Watch selection.
- [ ] Confirm pre-match baseline.
- [ ] Confirm successful iBIS acquisition.
- [ ] Confirm match-event notifications.
- [ ] Confirm final-result notification.
- [ ] Confirm final snapshot persistence.
- [ ] Confirm registry status `completed`.

Operational safeguard:

Do not make nonessential production code or workflow changes
before or during this match.

### P0 – Investigate missing late-match notifications

**Status: Open incident – 25 October 2026**

Match:

Tyresö Trollbäcken IBK (A) – Älta IF A

MatchID: `1703577`

Observed by the user:

- Notifications were received during the match.
- The last received notification referred to 10–4 and included
  a Ribbestad penalty and an opponent goal.
- No subsequent Event Platform notifications were received.
- The final-result notification was not received.

Verified from repository data supplied on 26 October:

- Final result: 11–5.
- `has_final_result: true`.
- `match_status: 4`.
- Final snapshot contains the later goals, period end and
  goalkeeper exits.
- `match_registry.json` records `monitoring_status: completed`.

These facts confirm successful final-state persistence and
automatic completion.

They do not confirm successful notification publication
or delivery.

The root cause remains unknown.

Investigation:

- [ ] Review GitHub Actions Live runs around match completion.
- [ ] Identify the run that persisted the final snapshot.
- [ ] Inspect notification-related logs and errors.
- [ ] Inspect Git history for the affected Watch.
- [ ] Review `notification_formatters.py`.
- [ ] Review `event_platform_live.py`.
- [ ] Review `floorball_match_selection.py` for an upper
      monitoring time boundary.
- [ ] Verify monitoring behavior after scheduled match start.
- [ ] Review available ntfy delivery evidence.
- [ ] Establish root cause before changing production code.
- [ ] Add regression coverage for any confirmed defect.

Do not assume the problem was caused by ntfy, time-window
selection or notification formatting without evidence.

### P1 – Complete automatic Floorball acceptance

**Status: Partially verified in real-world operation**

#### JAS match – 23 October 2026

Match:

Tyresö Trollbäcken IBK – FBI Tullinge

MatchID: `1750707`

Verified through user observation:

- [x] Automatic match monitoring worked.
- [x] Match-event notifications were received.
- [x] Lukas-specific assist notification included ⭐.

Remaining independent verification:

- [ ] Exact automatic activation time.
- [ ] Pre-match baseline.
- [ ] Complete notification history.
- [ ] Final snapshot.
- [x] Registry completion confirmed in the registry supplied
      on 6 November.
- [ ] Absence of unexpected duplicate notifications.

#### Men's match – 25 October 2026

MatchID: `1703577`

Verified:

- [x] Automatic monitoring worked.
- [x] Notifications were received during the match.
- [x] Final snapshot persisted: 11–5.
- [x] Match marked `completed`.

Not verified:

- [ ] Complete notification delivery.
- [ ] Final-result notification received.
- [ ] Exact activation time.
- [ ] Absence of duplicate notifications.

The missing notifications remain a separate P0 incident.

#### Men's match – 28 October 2026

Match:

Ingarö IF (A) – Tyresö Trollbäcken IBK (A)

MatchID: `1703581`

User reported that automatic monitoring worked successfully.

The registry supplied on 6 November confirms:

`monitoring_status: completed`

Remaining:

- [ ] Independently verify final snapshot.
- [ ] Independently verify complete notification history.

#### JAS match – 30 October 2026

Match:

Onyx IBS – Tyresö Trollbäcken IBK

MatchID: `1750712`

The registry supplied on 6 November confirms:

`monitoring_status: completed`

The available evidence does not independently establish
the complete notification history.

Remaining:

- [ ] Confirm match monitoring details if required.
- [ ] Verify final snapshot and notifications if required.

### P1 – Confirm scheduled Daily Discovery operation

**Status: Previously integrated; recurring failures now observed**

Verified on 22 October:

- Real iBIS Discovery execution.
- 31 relevant matches registered.
- Permanent Git persistence.
- Repeated execution produced zero changes.
- Manual Daily integration passed.

On 6 November, the scheduled Daily workflow was reported
failed for two consecutive days.

Golf monitoring completed, but Discovery failed with HTTP 503.

Remaining:

- [ ] Resolve the recurring iBIS authentication failure.
- [ ] Verify scheduled Discovery execution.
- [ ] Verify SGF Ranking remains unaffected.
- [ ] Confirm correct registry updates.
- [ ] Confirm no unnecessary Git commits.

### P1 – Protect operational monitoring

**Status: Active safeguard**

- Avoid nonessential production changes during matches.
- Preserve persistent state.
- Preserve existing Live scheduling.
- Retain useful diagnostic information.
- Investigate failed runs using logs and source data.
- Separate verified behavior from assumptions.

---

## 2. Completed implementation and verification

### Golf monitoring

**Status: Operational and validated**

Implemented connectors:

- `golfbox_leaderboard`
- `tournytt_api`
- `sgf_ranking`

GolfBox validated across:

- Haninge Golfklubb
- Strängnäs Golfklubb
- NSGK / Hylinge
- GolfBox Tournament

Verified capabilities:

- Pre-start leaderboard handling.
- First results.
- Live scoring.
- Position changes.
- Round transitions.
- Completed tournaments.
- State persistence.
- Notifications.

Existing golf regression tests passed on 22 October 2026.

### Initial Floorball connector

**Status: Implemented and validated in real matches**

Implementation completed in October 2026.

Verified capabilities:

- iBIS authentication.
- Match retrieval.
- Normalized snapshots.
- Event detection.
- Goal notifications.
- Penalty notifications.
- Period events.
- Final-result notifications.
- ntfy delivery.

#### Match 1 – 15 October 2026

Huddinge IBS – Tyresö Trollbäcken IBK

MatchID: `1750693`

Verified:

- Live iBIS acquisition.
- Goals.
- Penalties.
- Period changes.
- Final result.
- Notifications.

The match revealed the additional iBIS event type for
empty-net goals.

The formatter was updated to recognize MatchEventTypeID 12.

#### Match 2 – 17 October 2026

IFK Haninge (B) – Tyresö Trollbäcken IBK (A)

MatchID: `1703572`

Verified:

- Five-minute Live monitoring.
- Automatic GitHub Actions execution.
- Notifications.
- Final result: 5–4.
- Final state persistence.
- Preservation of existing Watches.

The final snapshot contained 30 unique registered match events.

Player-specific highlighting was not observed during this match.

### Automatic Floorball Discovery

**Status: Implemented; current operational incident open**

Implemented capabilities:

- Configured teams and competitions.
- iBIS match-list retrieval.
- Automatic match identification.
- Stable MatchIDs.
- Persistent match registry.
- Schedule updates.
- Preservation of completed matches.
- Git conflict handling.
- Repeated execution without duplicate registration.

Verified on 22 October:

- 31 matches discovered and persisted.
- Relevant JAS and men's matches present.
- Repeated execution detected zero changes.
- Manual Daily integration passed.

Discovery runs as part of `daily.yml`.

Recurring HTTP 503 failures were observed in November.

### Automatic Live match selection

**Status: Implemented and technically verified**

Capabilities:

- Automatic selection from `match_registry.json`.
- Activation 15 minutes before match start.
- Multiple eligible matches.
- Exclusion of cancelled matches.
- Exclusion of postponed matches.
- Exclusion of completed matches.
- Handling of delayed matches.
- Swedish time-zone handling.

October activation windows passed simulated-time verification.

Subsequent real-world matches demonstrated automatic monitoring.

### Automatic Live execution

**Status: Deployed and operational**

Implementation:

`event_platform_live.py`

Verified:

- Dynamic Live configuration.
- Preservation of GolfBox and Tournytt.
- Exclusion of obsolete manual floorball Watches.
- Automatic GitHub Actions execution.
- cron-job.org triggering.
- Real-world floorball monitoring.

Full acceptance remains conditional on resolving outstanding
notification and reliability questions.

### Coordinated Git persistence

**Status: Implemented and technically verified**

Capabilities:

- Registry field ownership.
- Preservation of unrelated matches.
- Preservation of unrelated Watch state.
- Git push retries.
- Optimistic concurrency checking.
- Protection against stale same-Watch updates.
- Coordinated final-state and completion commits.

Relevant persistence tests passed.

The match on 25 October provided real-world evidence of
successful final-state persistence and registry completion.

Broader concurrent execution remains an operational
validation area.

### Consolidated regression testing

**Status: Implemented**

Permanent workflow:

`.github/workflows/test-regression.yml`

Last confirmed run: 22 October 2026.

- 105 Floorball automated tests passed.
- Existing golf regression tests passed.

Historical standalone test-workflows remain pending cleanup.

### Live workflow runtime optimization

**Status: Completed and verified**

Previous execution time:

4 minutes 20 seconds.

Optimized results:

- Manual execution: approximately 37 seconds.
- Automatic execution: approximately 30 seconds.

GolfBox continues to use Playwright and Chromium.

---

## 3. Scheduling and authentication maintenance

### GitHub scheduler token renewal

**Status: Completed – 29 October 2026**

The GitHub personal access token used by cron-job.org
was approaching expiration.

cron-job.org disabled jobs after repeated failed executions.

The token was renewed and both existing jobs were updated:

- `Event Platform - Daily`
- `Event Platform - Live`

The authorization header was corrected to use:

`Bearer <token>`

Both jobs subsequently returned successful GitHub API responses.

Both GitHub Actions workflows were reported successful.

The renewed token expires:

**28 November 2026**

No Python or workflow code changes were required.

Future maintenance:

- [ ] Renew the token before 28 November 2026.
- [ ] Update both cron-job.org jobs.
- [ ] Verify HTTP 204 responses.
- [ ] Verify successful GitHub Actions execution.
- [ ] Consider a longer-lived or more maintainable
      authentication approach in a future session.

Never store token values in repository documentation.

---

## 4. Release management

### First Floorball production release

**Status: Deployed functionality; formal release pending**

The last documented published release remains v1.2.0.

v1.3.0 was previously proposed for the initial Floorball connector.

The implementation has since expanded to include automatic
Discovery and Live Monitoring.

Before publishing:

- [ ] Resolve or explicitly assess operational incidents.
- [ ] Complete required real-world acceptance.
- [ ] Confirm release scope.
- [ ] Review known limitations.
- [ ] Update release documentation.
- [ ] Obtain explicit approval.
- [ ] Publish the agreed release.

The final version number and scope must be confirmed.

---

## 5. Reliability improvements

### Notification delivery and Git persistence

**Status: Known limitation**

Notifications are sent before corresponding state changes
are committed to Git.

If delivery succeeds but persistence fails, a notification
may be repeated.

Exactly-once delivery is not guaranteed.

Future work:

- Evaluate stronger delivery coordination.
- Consider persistent notification identifiers.
- Consider an outbox or equivalent mechanism if justified.
- Preserve reliable event delivery.

The missing late-match notifications from 25 October
remain a separate open incident.

### Late first-observation recovery

**Status: Not implemented**

If the first automatic Floorball observation already
contains match activity, the Live runner rejects the
late baseline.

Future work:

- Define safe recovery behavior.
- Distinguish historical from new events.
- Establish a valid baseline.
- Resume monitoring without unexpected notifications.

### Corrected and deleted match events

**Status: Not implemented**

Future work:

- Corrected event details.
- Removed events.
- Corrected scores.
- Source revisions.

### Concurrent monitoring reliability

**Status: Partially addressed**

Implemented:

- Shared GitHub Actions concurrency group.
- Git persistence retries.
- Optimistic same-Watch conflict checking.
- Preservation of unrelated state.

Future work:

- Verify overlapping execution behavior.
- Improve conflict diagnostics.
- Review retry and recovery behavior.

### External API resilience

**Status: Improvement identified – 6 November 2026**

The recurring iBIS HTTP 503 failures demonstrate a need
to review external API failure handling.

Potential improvements:

- Bounded retries.
- Exponential backoff.
- Clearer API failure classification.
- Preservation of previous valid registry state.
- Better operational diagnostics.
- Appropriate alerting for repeated failures.

The correct implementation should be selected after
the root cause has been established.

---

## 6. Floorball notification improvements

### Player-specific highlighting

**Status: Assist highlighting verified in real-world operation**

Supported event types:

- Goals.
- Assists.
- Penalties.

Assist highlighting with ⭐ was verified during the
JAS match on 23 October 2026.

Goal and penalty highlighting remain to be observed
during qualifying player events.

### Empty-net goal formatting

**Status: Implemented; real-world verification pending**

MatchEventTypeID 12 is treated as an empty-net goal.

Presentation:

`(tom bur)`

Verify during a suitable real-world event.

### Additional improvements

**Status: Future work**

- Improve match-start wording.
- Evaluate additional event types.
- Introduce configurable notification preferences.
- Improve event presentation where needed.

---

## 7. Golf monitoring improvements

### GolfBox hole-by-hole monitoring

**Status: Not started**

Evaluate whether GolfBox hole-by-hole data should enrich
existing monitoring.

Previously observed:

- Shared player row ID.
- Individual holes 1–18.
- Strokes per completed hole.
- Semantic score classes.

Potential notification:

    Hål 10: 6 (bogey)
    Totalt: +2
    Placering: T32

Existing leaderboard monitoring remains the primary capability.

### Ranking changes in notifications

**Status: Not started**

SGF Ranking notifications could show previous and new values.

Example:

    Placering: 1204 → 1143
    Poäng: 4,32 → 5,30
    Tävlingar: 6 → 7

### Tournytt notification formatting

**Status: Not started**

Improve presentation of:

- Position.
- Score.
- To par.
- Played holes.
- Class.

The connector already captures relevant fields.

### Min Golf integration

**Status: Future opportunity**

Potential capabilities:

- Competition entry lists.
- Start lists.
- Upcoming competition discovery.

Evaluate source availability before implementation.

---

## 8. Platform improvements

### Connector Development Guide

**Status: Not started**

Create a repeatable process for evaluating and adding
new data sources.

Suggested steps:

1. Identify the external platform.
2. Check whether an existing connector can be reused.
3. Inspect source behavior.
4. Define source configuration.
5. Implement or adapt the connector.
6. Establish baseline.
7. Verify change detection.
8. Validate notifications.
9. Enable scheduling.

### Connector template

**Status: Not started**

Create a reusable connector reference implementation.

Interface:

`fetch_snapshot(watch)`

Connectors should not own state persistence, change
detection, notification delivery or scheduling.

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

The repository contains numerous standalone test-workflows
created during development.

The permanent consolidated regression workflow already
runs the relevant Floorball tests.

Actions:

- [ ] Inventory all historical workflows.
- [ ] Confirm none are used by external schedulers.
- [ ] Preserve `daily.yml`.
- [ ] Preserve `live.yml`.
- [ ] Preserve `test-regression.yml`.
- [ ] Retain `floorball-daily-discovery.yml` as a manual tool.
- [ ] Review `floorball-baseline.yml` before removal.
- [ ] Remove redundant standalone test-workflows.
- [ ] Verify consolidated regression tests after cleanup.

Do not remove workflows during active match validation.

### Review obsolete Python modules

**Status: Planned**

Actions:

- [ ] Identify production imports and dependencies.
- [ ] Identify test-only dependencies.
- [ ] Identify genuinely unused modules.
- [ ] Remove obsolete code only after verification.

Do not remove modules solely because they appear redundant.

### Remove obsolete manual Floorball Watches

**Status: Planned – After operational acceptance**

`config.yml` still contains historical manually configured
Floorball Watches.

Automatic Live execution excludes these Watches.

After successful acceptance:

- [ ] Confirm automatic Watch selection works reliably.
- [ ] Confirm historical Watch state remains preserved.
- [ ] Remove obsolete manual Floorball Watches.
- [ ] Verify Daily and Live execution.

Historical state should not be deleted merely because
configuration entries are removed.

### Documentation maintenance

**Status: Updating operational handover – 6 November 2026**

Previously updated:

- [x] `docs/ARCHITECTURE.md`
- [x] `docs/decisions.md`
- [x] `docs/design-floorball-automation.md`
- [x] `docs/ways-of-working.md`
- [x] `README.md`
- [x] `PROJECT_CONTEXT.md` – 26 October checkpoint
- [x] `docs/backlog.md` – 26 October checkpoint

Current documentation session:

- [ ] Update `docs/backlog.md` for 6 November.
- [ ] Update `PROJECT_CONTEXT.md` for 6 November.

Historical design documents should remain available.

---

## 10. Documentation and source of truth

GitHub remains the authoritative source of truth.

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

Future development priorities should be selected deliberately.

No backlog item should be assumed to belong to a particular
release until scope and approval have been agreed.
