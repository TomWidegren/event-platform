
# Event Platform – Backlog

This document tracks completed validation, outstanding work,
technical improvements, and future opportunities for Event Platform.

Backlog items are not commitments to a particular release unless
explicitly agreed.

GitHub is the authoritative source of truth.

**Current published production release:** v1.2.0

**Current deployed implementation:** Automatic Floorball Discovery
and Live Monitoring, pending full real-world acceptance.

**Last updated:** 26 October 2026

---

## 1. Immediate priorities

### P0 – Verify automatic Floorball Monitoring in real matches

**Status: Partially verified in real-world operation; notification incident open**

The automatic monitoring implementation is deployed and
scheduled through cron-job.org.

The first two automatic match monitoring trials took place on 23 and 25 October 2026. The remaining acceptance criteria must be verified from logs and persisted data.

#### JAS match – 23 October 2026

Match:

Tyresö Trollbäcken IBK – FBI Tullinge

MatchID: `1750707`

Scheduled start: 19:45 Europe/Stockholm.

Expected automatic activation: 19:30.

Verification:

- [ ] Automatic Watch selection at 19:30.
- [ ] Pre-match baseline established.
- [x] Match monitoring and notifications observed by the user.
- [x] Lukas-specific assist notification with star (⭐) verified in real operation.
- [ ] Complete match-event and goal notification history independently verified.
- [ ] Penalty and period notifications delivered when applicable.
- [ ] No unexpected duplicate notifications.
- [ ] Final-result notification independently confirmed.
- [ ] Final snapshot independently confirmed in `state.json`.
- [ ] Match `completed` status independently confirmed in `match_registry.json`.
- [ ] Completed match excluded from subsequent monitoring.

#### Men's match – 25 October 2026

Match:

Tyresö Trollbäcken IBK (A) – Älta IF A

MatchID: `1703577`

Scheduled start: 15:45 Europe/Stockholm.

Expected automatic activation: 15:30.

Verification:

- [ ] Automatic Watch selection at 15:30.
- [ ] Pre-match baseline established.
- [x] Match monitoring and event notifications observed by the user.
- [ ] Full event-notification delivery verified (last events were missing).
- [ ] Final-result notification delivered (not received by user).
- [x] Final snapshot persisted: 11–5, `has_final_result: true`, `match_status: 4`.
- [x] Match marked `completed` in `match_registry.json`.
- [ ] Completed match excluded from future monitoring.

Player-specific highlighting should be verified if Lukas
generates a qualifying event.

Absence of such an event is not a test failure.

### P0 – Investigate missing late-match notifications (25 October)

**Status: Open incident – root cause not established**

MatchID: `1703577` (Tyresö Trollbäcken IBK (A) – Älta IF A).

Observed by the user:

- Notifications were received during the match.
- The last received notification referred to 10–4 and included a Ribbestad penalty and an opponent goal.
- No subsequent Event Platform notifications were received, including no separate final-result notification.
- cron-job.org was checked on 26 October and remained enabled; this does not establish whether each scheduled run succeeded.

Verified from repository data supplied on 26 October:

- `state.json` contains the final score 11–5.
- `has_final_result` is `true` and `match_status` is `4`.
- The final snapshot includes later events: 11–4, 11–5, third-period end and goalkeeper exits.
- `match_registry.json` records `monitoring_status: completed`.

These facts establish final-state persistence and completion, **not** successful delivery of the final notification. The cause of missing notifications remains unknown.

Next investigation (no code changes until evidence is reviewed):

- [ ] Review GitHub Actions Live runs and timestamps around the end of the match.
- [ ] Inspect run output and errors for the final observation and notification delivery.
- [ ] Inspect Git history of the Watch entry and registry completion to reconstruct update timing.
- [ ] Compare `notification_formatters.py` and `event_platform_live.py` behavior for final results and multiple new events.
- [ ] Inspect `floorball_match_selection.py` for any upper monitoring time bound or eligibility behavior after scheduled start.
- [ ] Review available ntfy delivery evidence; distinguish publication from device reception.
- [ ] Record root cause, remediation and regression coverage before closing the incident.

### Real-world player highlighting – 23 October

**Status: Verified by user observation**

During the JAS match (MatchID `1750707`), a notification for Lukas Widegren's assist included the expected star (⭐). This closes the previous real-world verification gap for assist highlighting; goal and penalty highlighting remain separately unobserved unless confirmed later.

### P0 – Confirm automatic Daily Discovery operation

**Status: Manual integration verified; scheduled execution pending confirmation**

Completed on 22 October:

- Real iBIS Discovery execution.
- 31 matches registered.
- Permanent Git persistence verified.
- Repeated Discovery execution produced zero changes.
- Daily workflow integration passed manually.

Remaining:

- [ ] Confirm the next automatic 08:00 Daily execution.
- [ ] Verify that SGF Ranking still executes correctly.
- [ ] Verify that Discovery executes after golf monitoring.
- [ ] Confirm that no unnecessary Git commit occurs.

### P0 – Protect live monitoring during acceptance

**Status: Active operational safeguard**

Until the first automatic matches have been validated:

- Avoid nonessential changes to production connectors.
- Avoid modifying `live.yml`.
- Avoid modifying `event_platform_live.py`.
- Avoid deleting persistent state.
- Avoid deleting historical workflows that might still be useful.
- Preserve the existing five-minute Live schedule.
- Investigate failed or unusually slow executions promptly.

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

Verified capabilities include:

- Pre-start leaderboard handling
- First results
- Live scoring
- Position changes
- Round transitions
- Completed tournaments
- State persistence
- Notifications

Existing golf regression tests passed on 22 October 2026.

### Initial Floorball connector

**Status: Implemented and validated in two real matches**

Implementation completed in October 2026.

Verified capabilities:

- iBIS authentication
- Match retrieval
- Normalized match snapshots
- Event detection
- Goal notifications
- Penalty notifications
- Period events
- Final-result notifications
- ntfy delivery

#### Match 1 – 15 October 2026

Huddinge IBS – Tyresö Trollbäcken IBK

MatchID: `1750693`

Verified:

- Live iBIS acquisition
- Goals
- Penalties
- Period changes
- Final result
- Notifications

The match revealed the additional iBIS event type for
empty-net goals.

The formatter was updated to recognize MatchEventTypeID 12.

#### Match 2 – 17 October 2026

IFK Haninge (B) – Tyresö Trollbäcken IBK (A)

MatchID: `1703572`

Verified:

- Five-minute Live monitoring
- Automatic GitHub Actions execution
- Notifications
- Correct final result: 5–4
- Final state persistence
- Preservation of existing Watches

The final snapshot contained 30 unique registered match events.

Player-specific highlighting was not observed because Lukas
did not generate a qualifying event.

### Automatic Floorball Discovery

**Status: Implemented and operational**

Completed on 22 October 2026.

Capabilities:

- Configured teams and competitions
- iBIS match-list retrieval
- Automatic match identification
- Stable MatchIDs
- Persistent match registry
- Schedule updates
- Preservation of completed matches
- Git conflict handling
- Repeated execution without duplicate registration

Verified:

- 31 matches discovered and persisted.
- Relevant JAS and men's matches present.
- Second run detected zero changes.
- Manual Daily workflow integration passed.

Discovery now runs as part of `daily.yml`.

### Automatic Live match selection

**Status: Implemented and technically verified**

Capabilities:

- Automatic selection from `match_registry.json`
- Activation 15 minutes before match start
- Multiple simultaneous eligible matches
- Exclusion of cancelled matches
- Exclusion of postponed matches
- Exclusion of completed matches
- Handling of delayed matches
- Swedish time-zone handling

The October 23 and October 25 activation windows
passed simulated-time verification.

### Automatic Live execution

**Status: Deployed and operational outside active floorball matches**

Implementation:

`event_platform_live.py`

Verified on 22 October:

- Dynamic Live configuration
- Preservation of GolfBox and Tournytt
- Exclusion of obsolete manual floorball Watches
- Successful automatic GitHub Actions execution
- Correct handling when no floorball match is eligible
- No unnecessary state persistence
- Successful cron-job.org triggering

Full real-world floorball acceptance remains pending.

### Coordinated Git persistence

**Status: Implemented and technically verified**

Capabilities:

- Registry field ownership
- Preservation of unrelated matches
- Preservation of unrelated Watch state
- Git push retries
- Optimistic concurrency checking
- Protection against stale same-Watch updates
- Coordinated final-state and completion commits

The relevant persistence tests passed.

Broader real-world concurrent execution remains an
operational validation area.

### Consolidated regression testing

**Status: Implemented**

Permanent workflow:

`.github/workflows/test-regression.yml`

Verified on 22 October:

- 105 Floorball automated tests passed.
- Existing golf regression tests passed.

Historical standalone test-workflows remain in the repository
pending cleanup.

### Live workflow runtime optimization

**Status: Completed and verified**

The previous Live workflow repeatedly installed full
Playwright operating-system dependencies.

A measured execution took 4 minutes 20 seconds.

The workflow was optimized to install Python dependencies
and Chromium without the full system dependency installation.

Verified results:

- Optimized manual execution: approximately 37 seconds.
- Subsequent automatic execution: approximately 30 seconds.

GolfBox still uses Playwright and Chromium.

---

## 3. Release management

### First Floorball production release

**Status: Deployed functionality; formal release pending**

The current published production release remains v1.2.0.

v1.3.0 was previously proposed for the initial Floorball connector.

The implementation has since expanded to include automatic
Discovery and Live Monitoring.

Before publishing a new release:

- [ ] Complete real-world automatic Floorball validation.
- [ ] Confirm release scope.
- [ ] Review known limitations.
- [ ] Update release documentation.
- [ ] Obtain explicit release approval.
- [ ] Publish the agreed release.

The final version number and scope should be confirmed
rather than assumed.

---

## 4. Reliability improvements

### Notification delivery and Git persistence

**Status: Known limitation**

Notifications are sent before the corresponding state
changes are committed to Git.

If notification delivery succeeds but persistence fails,
the same event may be notified again.

Exactly-once notification delivery is not guaranteed.

Future work:

- Evaluate stronger delivery coordination.
- Consider persistent notification identifiers.
- Consider an outbox or equivalent mechanism if justified.
- Preserve reliable event delivery.

Priority should be based on real operational experience.

### Late first-observation recovery

**Status: Not implemented**

If the first automatic Floorball observation already
contains match activity, the Live runner rejects the
late baseline.

This avoids silently losing historical events but can
prevent monitoring from continuing.

Future work:

- Define recovery behavior.
- Distinguish historical from new events.
- Establish a safe baseline.
- Resume monitoring without unexpected notifications.

### Corrected and deleted match events

**Status: Not implemented**

The current formatter identifies newly registered events.

Future work should evaluate:

- Corrected event details
- Removed events
- Corrected scores
- Source revisions

### Concurrent monitoring reliability

**Status: Partially addressed**

Implemented:

- Shared GitHub Actions concurrency group
- Git persistence retries
- Optimistic same-Watch conflict checking
- Preservation of unrelated state

Future work:

- Verify overlapping execution behavior under realistic conditions.
- Improve diagnostics for rejected updates.
- Review retry and recovery behavior.

---

## 5. Floorball notification improvements

### Player-specific highlighting

**Status: Assist highlighting verified in real-world operation (23 October); other player event types not independently verified**

The formatter highlights relevant player events.

Supported event types include:

- Goals
- Assists
- Penalties

Assist highlighting with ⭐ was observed during the JAS match on 23 October 2026. Verify goal and penalty highlighting when qualifying events occur.

### Empty-net goal formatting

**Status: Implemented; real-world verification pending**

MatchEventTypeID 12 is treated as an empty-net goal.

Notification presentation uses:

`(tom bur)`

Verify during a suitable real-world event.

### Additional improvements

**Status: Future work**

- Improve match-start wording.
- Evaluate additional event types.
- Introduce configurable notification preferences.
- Improve event presentation where needed.

---

## 6. Golf monitoring improvements

### GolfBox hole-by-hole monitoring

**Status: Not started**

Evaluate whether GolfBox hole-by-hole data should enrich
existing monitoring.

Previously observed capabilities:

- Shared player row ID
- Individual holes 1–18
- Strokes per completed hole
- Semantic score classes

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

- Position
- Score
- To par
- Played holes
- Class

The connector already captures relevant fields.

### Min Golf integration

**Status: Future opportunity**

Potential capabilities:

- Competition entry lists
- Start lists
- Upcoming competition discovery

Evaluate source availability before implementation.

---

## 7. Platform improvements

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

The template should follow:

`fetch_snapshot(watch)`

Connectors should not own state persistence, change
detection, notification delivery or scheduling.

### Multi-user support

**Status: Long-term opportunity**

Potential capabilities:

- Multiple recipients
- User profiles
- Subscription management
- Notification preferences

### User interfaces and external access

**Status: Long-term opportunity**

Potential capabilities:

- REST API
- Web interface
- Mobile application

No implementation commitment has been made.

---

## 8. Technical cleanup

### Consolidate GitHub Actions workflows

**Status: Planned – After initial automatic match validation**

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

Several implementation modules were created during
the Floorball automation development.

Actions:

- [ ] Identify production imports and dependencies.
- [ ] Identify test-only dependencies.
- [ ] Identify genuinely unused modules.
- [ ] Remove obsolete code only after verification.

Do not remove modules solely because they appear redundant.

### Remove obsolete manual Floorball Watches

**Status: Planned – After real-world acceptance**

`config.yml` still contains historical manually configured
Floorball Watches.

Automatic Live execution excludes these Watches.

After successful real-world validation:

- [ ] Confirm automatic Watch selection works reliably.
- [ ] Confirm historical Watch state remains preserved.
- [ ] Remove obsolete manual Floorball Watches from configuration.
- [ ] Verify Daily and Live execution.

Historical state should not be deleted merely because
configuration entries are removed.

### Documentation maintenance

**Status: Core documentation updated on 22 October; incident handover update in progress on 26 October**

Documents to review and update:

- [x] `docs/ARCHITECTURE.md`
- [x] `docs/decisions.md`
- [x] `docs/backlog.md`
- [x] `docs/design-floorball-automation.md`
- [x] `docs/ways-of-working.md`
- [x] `README.md`
- [x] `PROJECT_CONTEXT.md` (22 October checkpoint; 26 October update pending)

Historical design documents should remain available.

---

## 9. Documentation and source of truth

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
