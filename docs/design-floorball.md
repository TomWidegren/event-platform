
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

### Initial investigation – Completed

The initial investigation of the Swedish Floorball/iBIS public API was completed on 12 October 2026.

Verified:

- Player profile endpoint.
- Competition match-list endpoint.
- Individual match endpoint.
- Structured goal and assist information.
- Structured penalty information.
- Team, match-team and player identifiers.

### First implementation – Completed

Date: 14 October 2026.

A first floorball monitoring implementation has been developed using the existing Event Platform v1.2 architecture.

Initial scope:

- One specific match.
- One configured Watch.
- Monitoring of match status, scores and registered events.
- Highlighting of selected player events.

Implemented:

- `connectors/ibis_floorball.py`
- Automatic temporary authentication through the iBIS startkit endpoint.
- HTTP/JSON acquisition and normalized match snapshots.
- Floorball-specific notification formatting.
- Identification of new match events using MatchEventID.
- Support for multiple new events in one notification.
- Highlighting of Lukas Widegren's goals, assists and penalties.
- Optional WATCH_ID filtering in the Event Platform core.
- Floorball Watch configuration in `config.yml`.
- Permanent pre-match baseline in `state.json`.
- Isolated connector, formatting and baseline tests.

The existing golf connectors and their notification formatting remain unchanged.

### Technical verification – Completed

Verified through GitHub Actions:

- iBIS startkit returns a temporary access token.
- Authenticated match API requests return HTTP 200.
- The floorball connector retrieves and normalizes the correct match.
- Five notification formatting tests pass.
- Multiple new events are included in one formatted notification.
- Previously observed events are not repeated in formatting tests.
- Final-result formatting works in simulated tests.
- Existing golf notification formatting passes its regression test.
- The first floorball baseline is established without notification.
- Existing state entries are preserved.
- Manual Live execution using WATCH_ID runs only the floorball Watch.
- Unchanged match data produces no notification.

### Real-world validation – Pending

The first live match validation is planned for 15 October 2026.

Match:

- Huddinge IBS – Tyresö Trollbäcken IBK
- Competition: Juniorallsvenskan D HJ18
- Match ID: 1750693
- Start: 20:15

The Live schedule will be enabled before the match and disabled after completion.

The initial polling interval remains five minutes.

### Remaining design and implementation questions

- Verify match-start detection and notification wording.
- Verify real-time API updates during an active match.
- Verify real ntfy delivery for floorball.
- Evaluate handling of event corrections and deletions.
- Define automatic match discovery across selected teams and competitions.
- Resolve the long-term Watch granularity.
- Define configurable notification preferences.
- Review GitHub Actions runtime compatibility.

The floorball implementation has not yet been included in a published production release.

## 9. Recommended next step

Complete the first real-world floorball validation during the match on 15 October 2026.

After the match:

1. Review GitHub Actions execution logs.
2. Review notifications received through ntfy.
3. Compare the observed notifications with the match event history.
4. Verify state persistence and prevention of duplicate notifications.
5. Document issues and lessons learned.
6. Update the backlog and determine the next development priority.

Continue using the existing Event Platform v1.2 architecture wherever possible.

Do not generalize the floorball connector for multiple teams and competitions until the initial match validation has been evaluated.
