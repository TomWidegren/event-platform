# Event Platform – Backlog

This document contains identified future work for Event Platform.

Items in this backlog are not commitments to a specific release or implementation.

They should be prioritized when planning a development session.

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
- Round transitions
- Completed tournament
- Final state persistence
- Notifications

The validation provides sufficient evidence to begin generalizing the GolfBox connector in a future release.

### Evaluate GolfBox hole-by-hole monitoring

Evaluate whether GolfBox hole-by-hole data should be used to enrich live monitoring and notifications.

The GolfBox `holebyhole` view has been verified to expose:

- The same player row ID as the standard leaderboard
- Individual elements for holes 1–18
- Strokes per completed hole
- Semantic score classes such as `score-bogey`

Potential value:

A live notification could include the latest completed hole, for example:

```text
Hål 10: 6 (bogey)
Totalt: +2
Placering: T32
```

The existing leaderboard monitoring should remain the primary GolfBox capability unless hole-by-hole data provides sufficient additional user value.

This is an enhancement opportunity, not a requirement for the existing GolfBox connector.

---

### Connector Development Guide

Create a repeatable process for adding or evaluating a new data source.

The process should start by identifying the underlying platform before creating a new connector.

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

A new connector should ideally take less than one hour to create once the source behavior is understood.

---

### Connector template

Create a clean reference implementation or template for new connectors.

A connector should:

- acquire data,
- locate the requested entity,
- normalize the result,
- return a structured snapshot.
- A connector should expose one public entry point to the Event Platform core.

A connector should not:

- persist state,
- detect changes,
- send notifications,
- manage scheduling.

---

## Notification improvements

### Show ranking changes in notifications

SGF Ranking notifications should show both the previous and new values.

Example:

```text
Placering: 1204 → 1143
Poäng: 4,32 → 5,30
Tävlingar: 6 → 7
```

### Improve Tournytt notification formatting

Use the Tournytt snapshot fields to provide a richer notification.

Possible fields include:

- Position
- Score
- To par
- Played holes
- Class

The connector already captures these values.

The improvement is limited to presentation formatting.


---


## Floorball monitoring

### Initial floorball connector

**Status: Implemented – Real-world validation pending**

Initial investigation completed on 12 October 2026.

First implementation completed on 14 October 2026.

Implemented:

- iBIS connector using HTTP/JSON and temporary token authentication.
- Monitoring of one configured match.
- Normalized match snapshots including registered events.
- Detection of new events using MatchEventID.
- Multiple new events included in one notification.
- Player-specific highlighting for goals, assists and penalties.
- Permanent pre-match baseline.
- WATCH_ID filtering for isolated execution.
- Automated connector, formatting and baseline tests.

Technical verification completed through GitHub Actions.

The implementation is not yet included in a published production release.

### First live match validation

**Status: Planned – 15 October 2026**

Match:

- Huddinge IBS – Tyresö Trollbäcken IBK
- Juniorallsvenskan D HJ18
- Match ID: 1750693
- Start: 20:15

Validation goals:

- Verify match-start detection and notification.
- Verify live API updates.
- Verify goal, assist and penalty notifications.
- Verify multiple events between polling intervals.
- Verify Lukas-specific highlighting.
- Verify final-result notification.
- Verify state persistence and prevention of duplicate notifications.

After the match, evaluate results and document lessons learned.

### Generalize floorball monitoring

**Status: Not started**

Extend monitoring beyond one manually configured match.

Requirements:

- Monitor all matches for selected teams and competitions.
- Discover upcoming matches automatically.
- Support multiple teams and competitions.
- Handle postponed and cancelled matches.
- Maintain stable Watch identities.
- Reuse the existing Event Platform core wherever possible.

Resolve the long-term Watch granularity and match-discovery design before implementation.

### Floorball notification improvements

**Status: Partially implemented**

Future improvements:

- Confirm match-start status mapping and improve notification wording.
- Handle corrected or deleted match events.
- Introduce configurable notification preferences.
- Evaluate additional event types and presentation.
- Improve handling of player-specific highlights.

### GitHub Actions runtime maintenance

**Status: Pending**

GitHub Actions reported warnings in October 2026 concerning:

- Deprecation of Node.js 20 in existing GitHub Actions.
- Migration of `ubuntu-latest` to a newer Ubuntu runner image beginning 19 October 2026.

Required follow-up:

- Review supported versions of `actions/checkout` and `actions/setup-python`.
- Verify compatibility with the updated GitHub Actions runtime.
- Verify Playwright and Chromium compatibility.
- Run regression tests for Daily and Live workflows after any required updates.

This maintenance should be addressed separately from the initial floorball validation.

### Documentation

Detailed investigation, design and implementation status:

`docs/design-floorball.md`

Current project context:

`PROJECT_CONTEXT.md`
