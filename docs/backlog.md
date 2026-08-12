# Event Platform – Backlog

This document contains identified future work for Event Platform.

Items in this backlog are not commitments to a specific release or implementation.

They should be prioritized when planning a development session.

---

## High priority

### Validate GolfBox connector with a third implementation

Validate the existing `golfbox_leaderboard` connector against the NSGK competition before generalizing the connector.

Competition:

- NSGK
- Competition ID: `5543525`

Reason:

The connector has already been verified with Haninge Golfklubb and Strängnäs Golfklubb.

A third real-world implementation provides additional evidence about which parts of the connector are genuinely GolfBox-generic before configuration and connector interfaces are generalized.

Validation should include, where available:

- Correct leaderboard/class selection
- Player lookup
- Empty/pre-event leaderboard behavior
- First result
- Live scoring
- Position changes
- Completed result

After this validation, use the combined learnings from Haninge, Strängnäs and NSGK when generalizing GolfBox configuration.

---


### Generalize GolfBox configuration

Move event-specific GolfBox parameters out of `golfbox_leaderboard.py` and into `config.yml`.

Examples:

- competition ID
- leaderboard ID
- player

Goal:

A new GolfBox competition should normally require configuration changes only, with no Python code changes.

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
