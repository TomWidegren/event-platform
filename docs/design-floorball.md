
# Event Platform – Floorball Design Draft

## Purpose

This document captures the initial investigation and design considerations for adding Swedish floorball monitoring to Event Platform.

The investigation was conducted on 12 October 2026.

Current production release: v1.2.0.

The repository remains the source of truth. This document records findings and proposals, not approved architectural decisions.

No floorball connector has been implemented yet.

## 1. Monitoring requirements

### Team monitoring

Event Platform should monitor all matches for selected teams in selected competitions, regardless of whether a particular player participates.

Initial use case:

- Club: Tyresö Trollbäcken IBK
- Multiple teams and competitions
- Season: 2026/27

The user should be able to specify which teams and competitions to monitor.

### Match notifications

Initial preference: notify on all relevant registered match events.

Potential events include:

- Match start
- Goals for both teams
- Assists
- Penalties
- Period starts and ends
- Final result
- Other registered match events

Notification preferences may be introduced later to reduce unwanted notifications.

### Player-specific highlighting

Certain player events should be highlighted within normal match notifications.

Initial player:

- Name: Lukas Widegren
- PlayerID: 585280

Highlight when the player:

- Scores a goal
- Records an assist
- Receives a penalty

Team monitoring must continue regardless of whether the player participates.

## 2. Identified data source

Platform: Swedish Floorball / iBIS

Public statistics website:

https://stats.innebandy.se/

Underlying API:

https://api.innebandy.se/v2/api/public/

The website was observed retrieving structured JSON through HTTP GET requests.

The following endpoints were identified using Chrome Developer Tools.

### Player

GET /players/585280

Full URL:

https://api.innebandy.se/v2/api/public/players/585280

Verified fields include:

- PlayerID
- PersonID
- Name
- AssociationOfOriginName
- LicenseHistory
- SeasonID

The player profile aggregates statistics across several competitions.

However, the inspected player response did not expose a clear list of all upcoming matches or current team memberships.

### Competition matches

GET /competitions/44356/matches

Full URL:

https://api.innebandy.se/v2/api/public/competitions/44356/matches

Verified fields include:

- CompetitionID
- MatchID
- HomeTeam / HomeTeamID
- AwayTeam / AwayTeamID
- MatchDateTime
- MatchStatus
- GoalsHomeTeam
- GoalsAwayTeam
- HasFinalResult

The endpoint returns matches for the competition, not just one team.

This provides a potential mechanism for discovering relevant matches by filtering on team identifiers.

### Individual match

GET /matches/1703567

Full URL:

https://api.innebandy.se/v2/api/public/matches/1703567

Verified fields include:

- MatchID
- CompetitionID
- HomeTeam / AwayTeam
- HomeTeamID / AwayTeamID
- MatchDateTime
- MatchStatus
- GoalsHomeTeam / GoalsAwayTeam
- Events

The Events collection contains structured match events.

## 3. Verified match events

### Goals

Observed event type:

- MatchEventTypeID: 1
- MatchEventType: Mål

Relevant fields:

- MatchEventID
- MatchTeamID
- Period
- Minute
- Second
- GoalsHomeTeam
- GoalsAwayTeam
- PlayerID
- PlayerName
- PlayerAssistID
- PlayerAssistName

These fields should allow identification of goals, assists and the score after each goal.

### Penalties

Observed event type:

- MatchEventTypeID: 2
- MatchEventType: Utvisning

Example from match 1703567:

- MatchEventID: 9772262
- PlayerID: 217400
- PlayerName: David Jorhem
- Period: 2
- Minute: 11
- Second: 4
- PenaltyCode: 208
- PenaltyName: Hårt spel 2 min
- GoalsHomeTeam: 4
- GoalsAwayTeam: 4

This confirms that penalty events expose the player identity and penalty description.

### Other observed events

The inspected match also contained event types such as:

- Periodstart
- Periodslut
- Målvakt - In
- Målvakt - Ut
- Straffmål

The full event-type model has not yet been documented.

## 4. Identifiers

Identifiers observed during the investigation:

| Entity | Identifier |
|---|---|
| Season 2026/27 | 44 |
| Lukas Widegren | PlayerID 585280 |
| Tyresö Trollbäcken IBK team page | Team 4194 |
| Herrar Division 3 Södra | CompetitionID 44356 |
| Completed match | MatchID 1703567 |
| Upcoming match | MatchID 1703572 |

Important:

Team identifiers used by the website and match API may represent different concepts.

For example, the match API contains HomeTeamID / AwayTeamID and also MatchTeamID within events.

Their relationships must be verified before defining the final Watch configuration.

## 5. Candidate monitoring approach

The following is a design hypothesis, not an approved implementation.

1. Configure selected competitions and teams.
2. Retrieve the competition match list.
3. Identify matches involving the configured teams.
4. Determine which matches are relevant for monitoring.
5. Retrieve individual match details.
6. Normalize match status, scores and events.
7. Detect changes using Event Platform's existing core.
8. Format notifications, highlighting selected players.

The solution should use the existing v1.2 connector interface:

`fetch_snapshot(watch)`

The connector should own HTTP acquisition and normalization.

State persistence, change detection and notification triggering remain core responsibilities.

Notification presentation belongs in the separate formatting layer.

## 6. Open design questions

### DQ1 – Watch granularity

Should one Watch represent:

- One team in one competition?
- One team across several competitions?
- Several teams and competitions?

The choice must support players who participate in several teams.

### DQ2 – Match discovery

How frequently should competition match lists be checked?

How should newly scheduled, postponed or cancelled matches be handled?

### DQ3 – Live monitoring

How frequently does the API update during an active match?

Does it publish match events immediately or with a delay?

This has not yet been verified during a live match.

### DQ4 – Event detection

How should new events, corrections and deleted events be detected?

MatchEventID appears suitable for identifying individual events, but its stability and correction behavior require validation.

### DQ5 – Notifications

How should notifications be formatted for:

- Goals
- Assists
- Penalties
- Period transitions
- Final results
- Other match events

How should selected players be highlighted?

How should notification preferences be represented in future configuration?

### DQ6 – Multiple matches per Watch

The current v1.2 interface returns one normalized snapshot per Watch.

We must determine how multiple matches and individual events should be represented without breaking the existing core contract.

### DQ7 – Team and player identification

Which identifiers should be configured?

Can a player's current teams and competitions be discovered automatically, or must they be configured explicitly?

## 7. Validation approach

Prefer real-world verification, consistent with Event Platform's established ways of working.

Initial proposed validation:

1. Identify one upcoming match for a selected team.
2. Establish a baseline before the match.
3. Verify changes during the match.
4. Verify goal and penalty event detection.
5. Verify player-specific highlighting where applicable.
6. Verify period transitions and final result.
7. Verify state persistence and prevention of duplicate notifications.

Do not modify the existing production connectors during this investigation.

## 8. Current status

Completed:

- Identified the underlying public API.
- Verified player profile endpoint.
- Verified competition match-list endpoint.
- Verified individual match endpoint.
- Verified structured goal and assist information.
- Verified structured penalty information.
- Established initial monitoring requirements.

Not completed:

- Full team and competition configuration design.
- Automatic match-discovery design.
- Live API update validation.
- Snapshot and event-state design.
- Notification formatting design.
- Connector implementation.

## 9. Recommended next step

At the next development session, review the open design questions and select a minimal first floorball monitoring scenario.

Use the existing Event Platform v1.2 architecture wherever possible.

Do not implement the connector until the required configuration, snapshot model and verification approach have been agreed.
