# Event Platform – Backlog

This document contains identified future work for Event Platform.

Items in this backlog are not commitments to a specific release or implementation.

They should be prioritized when planning a development session.

The current production release is v1.2.0.

---

## Completed validations

### GolfBox connector

Successfully validated across four real-world GolfBox deployments:

- Haninge Golfklubb
- Strängnäs Golfklubb
- NSGK (Hylinge)
- GolfBox Tournament (`golfbox.dk`)

Verified:

- Empty leaderboard
- Player present before start
- First result
- Live scoring
- Position changes
- Round transitions
- Completed tournament
- Final state persistence
- Notifications

The validation provides sufficient evidence for further improvements to the GolfBox connector.

### Floorball – First live match

**Status: Completed – 15 October 2026**

Match: Huddinge IBS – Tyresö Trollbäcken IBK

Competition: Juniorallsvenskan D HJ18

Match ID: 1750693

Verified through real-world monitoring:

- Live iBIS data acquisition.
- Goal notifications.
- Penalty notifications.
- Period-start notifications.
- Period-end notifications.
- Final-result notification.
- Delivery through ntfy.

An additional iBIS event type for empty-net goals was identified.

The notification formatter was updated to recognize MatchEventTypeID 12 as a goal and identify it with `(tom bur)`.

Player-specific highlighting was not verified during the match because Lukas Widegren did not score, record an assist or receive a penalty.

The implementation has been technically tested.

Detailed findings are documented in `docs/design-floorball.md`.

---

## Floorball monitoring

### Initial floorball connector

**Status: Implemented – Real-world validation ongoing**

Initial investigation completed on 12 October 2026.

First implementation completed on 14 October 2026.

Implemented:

- iBIS connector using HTTP/JSON and temporary token authentication.
- Monitoring of one configured match per Watch.
- Normalized match snapshots including registered events.
- Detection of new events using MatchEventID.
- Multiple new events included in one notification.
- Player-specific highlighting for goals, assists and penalties.
- Permanent pre-match baseline.
- WATCH_ID filtering for isolated execution.
- Automated connector, formatting and baseline tests.
- Handling of regular and empty-net goals.

Technical verification completed through GitHub Actions.

First real-world match validation completed successfully on 15 October 2026.

The implementation has not yet been included in a published production release.

### Second live match validation

**Status: Prepared – 17 October 2026**

Match: IFK Haninge (B) – Tyresö Trollbäcken IBK (A)

Competition: Herrar Division 3 Södra

Match ID: 1703572

Start: 13:30

Followed team ID: 4194

Highlighted player: Lukas Widegren, PlayerID 585280

Preparation verified on 16 October:

- Separate Watch configured.
- Existing Watches preserved.
- Permanent baseline established.
- Five existing state entries preserved.
- No notification generated during baseline creation.
- Live workflow updated to the correct Watch ID.
- Manual Live execution successful.
- Automatic execution through cron-job.org verified.
- Five-minute polling interval confirmed.

Validation goals:

- Verify live match notifications.
- Verify goal and penalty notifications.
- Verify period transitions.
- Verify final-result notification.
- Verify Lukas-specific highlighting if relevant events occur.
- Verify updated empty-net goal formatting if applicable.
- Confirm state persistence and absence of duplicate notifications.

After the match, evaluate the results and document lessons learned.

### Generalize floorball monitoring

**Status: Not started**

Extend monitoring beyond manually configured individual matches.

Requirements:

- Monitor all matches for selected teams and competitions.
- Discover upcoming matches automatically.
- Support multiple teams and competitions.
- Handle postponed and cancelled matches.
- Maintain stable Watch identities.
- Reuse the existing Event Platform core wherever possible.

Resolve the long-term Watch granularity and match-discovery design before implementation.

### Multiple simultaneous Live Watches

**Status: Not started**

The current Live workflow uses a hard-coded `WATCH_ID` to select one Watch.

Future development should allow multiple relevant Live Watches to be monitored without manually editing workflow configuration for every event.

Consider:

- Watch selection.
- Active versus inactive events.
- Polling frequency.
- Execution time.
- State isolation.
- Concurrent execution safety.

Design this capability together with improvements to state persistence.

### Safe concurrent state persistence

**Status: Identified – Not started**

The current Live workflow can overwrite concurrent state changes when it restores a complete saved `state.json` after synchronizing with `main`.

This becomes increasingly important when multiple Watches or workflows are active.

Required investigation:

- Determine how concurrent executions can affect state.
- Evaluate safer state merging or other persistence approaches.
- Preserve unrelated Watch entries.
- Avoid lost updates.
- Verify behavior through controlled tests.

Do not introduce broader concurrent Live monitoring before addressing this risk.

### Floorball notification improvements

**Status: Partially implemented**

Implemented:

- Goal notifications.
- Penalty notifications.
- Period events.
- Final-result notifications.
- Empty-net goal handling.
- Player-specific highlighting logic.

Future improvements:

- Verify Lukas-specific highlighting during a real match.
- Verify updated empty-net goal formatting during a suitable real event.
- Improve match-start status wording.
- Handle corrected or deleted match events.
- Introduce configurable notification preferences.
- Evaluate additional event types and presentation.

---

## Golf monitoring improvements

### Evaluate GolfBox hole-by-hole monitoring

**Status: Not started**

Evaluate whether GolfBox hole-by-hole data should enrich live monitoring and notifications.

The GolfBox `holebyhole` view has been verified to expose:

- The same player row ID as the standard leaderboard.
- Individual elements for holes 1–18.
- Strokes per completed hole.
- Semantic score classes such as `score-bogey`.

Potential notification:

```text
Hål 10: 6 (bogey)
Totalt: +2
Placering: T32
```

The existing leaderboard monitoring should remain the primary capability unless hole-by-hole data provides sufficient additional value.

### Show ranking changes in notifications

**Status: Not started**

SGF Ranking notifications should show previous and new values.

Example:

```text
Placering: 1204 → 1143
Poäng: 4,32 → 5,30
Tävlingar: 6 → 7
```

### Improve Tournytt notification formatting

**Status: Not started**

Use the Tournytt snapshot fields to provide richer notifications.

Possible fields:

- Position
- Score
- To par
- Played holes
- Class

The connector already captures these values.

The improvement is limited to presentation formatting.

### Min Golf integration

**Status: Future opportunity**

Originally identified in the early Golf Watcher roadmap.

Potential capabilities:

- Read competition entry lists.
- Read start lists.
- Discover upcoming competitions.

Evaluate source availability and technical feasibility before implementation.

---

## Platform improvements

### Connector Development Guide

**Status: Not started**

Create a repeatable process for adding or evaluating new data sources.

Suggested flow:

1. Identify source/platform.
2. Check whether an existing connector can be reused.
3. Inspect how the source loads and updates data.
4. Determine required configuration.
5. Implement or adapt connector.
6. Establish baseline.
7. Verify change detection.
8. Enable appropriate schedule.

Target:

A new connector should ideally take less than one hour to create once source behavior is understood.

### Connector template

**Status: Not started**

Create a reference implementation or template for new connectors.

A connector should:

- Acquire data.
- Locate the requested entity.
- Normalize the result.
- Return a structured snapshot.
- Expose `fetch_snapshot(watch)` as its public interface.

A connector should not:

- Persist state.
- Detect changes.
- Send notifications.
- Manage scheduling.

### Multi-user support

**Status: Long-term opportunity**

Originally identified in the early Golf Watcher roadmap.

Potential capabilities:

- Multiple notification recipients.
- User profiles.
- Subscription management.
- Notification preferences.

No implementation or release commitment has been made.

### User interfaces and external access

**Status: Long-term opportunity**

Potential capabilities:

- REST API.
- Web interface.
- Mobile application.

These are exploratory opportunities rather than committed features.

---

## Technical maintenance

### GitHub Actions runtime maintenance

**Status: Pending**

GitHub Actions reported warnings in October 2026 concerning:

- Deprecation of Node.js 20 in existing GitHub Actions.
- Migration of `ubuntu-latest` to a newer Ubuntu runner image beginning 19 October 2026.

Required follow-up:

- Review supported versions of `actions/checkout` and `actions/setup-python`.
- Verify compatibility with the updated GitHub Actions runtime.
- Verify Playwright and Chromium compatibility.
- Run regression tests for Daily and Live workflows after required updates.

This maintenance should be addressed separately from the ongoing floorball validation.

---

## Documentation

Current project context:

`PROJECT_CONTEXT.md`

Architecture:

`docs/ARCHITECTURE.md`

Development process:

`docs/ways-of-working.md`

Floorball design and validation:

`docs/design-floorball.md`

The repository documentation is the source of truth.

Future development priorities should be selected deliberately at the beginning of a development session.

No backlog item should be assumed to belong to a specific release until its scope has been agreed.
