
# Event Platform – Floorball Design Draft

## Purpose

This document captures the investigation, design considerations, implementation and real-world validation of Swedish floorball monitoring in Event Platform.

The initial investigation was conducted on 12 October 2026.

The first implementation was completed on 14 October 2026.

Current production release: v1.2.0.

The repository remains the source of truth.

This document records technical findings, implemented capabilities, validation results and unresolved design questions.

Proposed future architectural changes are not considered approved decisions until explicitly agreed and documented in `decisions.md`.

The floorball connector has been implemented and successfully validated during two real-world matches. It has not yet been included in a published production release.

## 1. Monitoring requirements

### Team monitoring

Event Platform should monitor all matches for selected teams in selected competitions, regardless of whether a particular player participates.

Initial use case:

- Club: Tyresö Trollbäcken IBK
- Multiple teams and competitions
- Season: 2026/27

The user should be able to specify which teams and competitions to monitor.

The initial implementation monitors one explicitly configured match per Watch. Automatic discovery of matches remains future work.

### Match notifications

Initial preference: notify on all relevant registered match events.

Relevant events include:

- Match start
- Goals for both teams
- Empty-net goals
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

The highlighting functionality has been implemented and technically tested but has not yet been verified during a real match involving a relevant event by Lukas.

## 2. Identified data source

Platform: Swedish Floorball / iBIS

Public statistics website:

https://stats.innebandy.se/

Underlying API:

https://api.innebandy.se/v2/api/public/

The website retrieves structured JSON through HTTP GET requests.

The following endpoints were identified using Chrome Developer Tools.

### Authentication

The connector obtains a temporary access token through:

`https://api.innebandy.se/StatsAppApi/api/startkit`

The response provides an access token and API root.

The connector validates the API root before making authenticated requests.

This authentication mechanism has been successfully verified through GitHub Actions and real-world monitoring.

### Player

GET `/players/585280`

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

GET `/competitions/44356/matches`

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

GET `/matches/{match_id}`

Example:

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

The current connector retrieves individual match data through this endpoint.

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

These fields allow identification of goals, assists and the score after each goal.

### Empty-net goals

An additional goal event type was identified during the first real-world validation on 15 October 2026.

- MatchEventTypeID: 12
- Event: Mål i tom bur

The initial notification formatter recognized regular goals using MatchEventTypeID 1.

Following the discovery, the formatter was updated to recognize both event types.

Current implementation:

`if event.get("type_id") in (1, 12):`

Empty-net goals are handled as goals, including:

- Scoring team
- Goal scorer when the followed team scores
- Assist when available
- Score after the goal
- Player-specific highlighting when applicable

The notification includes the suffix:

`(tom bur)`

The updated implementation has been confirmed through inspection of `notification_formatters.py`.

Separate real-world verification of the updated empty-net formatting remains to be documented.

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

Penalty notifications were successfully verified during both real-world match validations.

### Other observed events

The inspected match data also contained event types such as:

- Periodstart
- Periodslut
- Målvakt - In
- Målvakt - Ut
- Straffmål

Period-start and period-end notifications were successfully observed during the first real-world match validation.

The full iBIS event-type model has not yet been documented.

## 4. Identifiers

Identifiers observed during investigation and implementation:

| Entity | Identifier |
|---|---|
| Season 2026/27 | 44 |
| Lukas Widegren | PlayerID 585280 |
| Tyresö Trollbäcken IBK – Herrar | TeamID 4194 |
| Tyresö Trollbäcken IBK – JAS | TeamID 20872 |
| Herrar Division 3 Södra | CompetitionID 44356 |
| Completed match used for investigation | MatchID 1703567 |
| JAS validation match | MatchID 1750693 |
| Herrar validation match | MatchID 1703572 |

The two Tyresö teams have different TeamIDs because they represent different teams within the same club.

The match API also exposes MatchTeamID values, which identify a team's participation in an individual match.

The notification formatter uses the configured TeamID to determine the followed team's corresponding MatchTeamID.

This allows the formatter to distinguish between events involving the followed team and its opponent.

## 5. Current implementation and future monitoring approach

### Current implementation

The first implementation uses one Watch per explicitly configured match.

Each Watch contains:

- Stable Watch ID
- Connector name
- Execution mode
- Match ID
- Followed team ID
- Optional highlighted player ID

Example:

```yaml
- id: "floorball-match-1703572"
  name: "IFK Haninge (B) - Tyresö Trollbäcken IBK (A)"
  connector: ibis_floorball
  mode: live
  source:
    match_id: 1703572
    team_id: 4194
    highlight_player_id: 585280
```

The connector uses the existing v1.2 interface:

`fetch_snapshot(watch)`

It owns:

- Temporary authentication
- HTTP acquisition
- Match data retrieval
- Snapshot normalization
- Event normalization and ordering

The Event Platform core owns:

- Watch selection
- State persistence
- Change detection
- Notification triggering

The notification formatting layer owns the presentation of match events.

### State and baseline

Each match uses a stable Watch ID as its state key.

A dedicated GitHub Actions workflow establishes the pre-match baseline.

The baseline workflow:

1. Retrieves the current match snapshot.
2. Verifies that the match has not started.
3. Verifies that no match events or recorded goals exist.
4. Verifies that a baseline does not already exist.
5. Adds the new Watch state.
6. Preserves existing state entries.
7. Commits the updated state to GitHub.

No notification is sent when establishing the baseline.

### Live execution

The Live workflow supports an optional `WATCH_ID` environment variable.

This allows execution to be restricted to one configured Watch.

The current workflow uses a hard-coded Watch ID, which must be changed manually when switching matches.

cron-job.org triggers GitHub Actions every five minutes while the Live schedule is enabled.

### Future monitoring approach

The longer-term design should support:

1. Configuring selected teams and competitions.
2. Retrieving competition match lists.
3. Discovering relevant upcoming matches.
4. Determining which matches require monitoring.
5. Retrieving individual match details.
6. Normalizing match status, scores and events.
7. Detecting changes using the existing Event Platform core.
8. Formatting notifications with player-specific highlighting.

This remains a design direction, not an approved implementation.

## 6. Open design questions

### DQ1 – Watch granularity

Should one Watch represent:

- One team in one competition?
- One team across several competitions?
- Several teams and competitions?

The current implementation uses one Watch per match.

The long-term model must support multiple teams and competitions without losing stable state identities.

### DQ2 – Match discovery

How frequently should competition match lists be checked?

How should newly scheduled, postponed or cancelled matches be handled?

Automatic match discovery has not yet been implemented.

### DQ3 – Live monitoring

The five-minute polling interval has been used successfully during real-world monitoring.

Further evaluation should determine:

- Typical delay between a match event and its availability through the API.
- Whether different event types have different publication delays.
- Whether five minutes remains appropriate for future use cases.

### DQ4 – Event detection

New events are identified using MatchEventID.

This has been implemented and used during real-world monitoring.

Remaining questions:

- How should corrected events be detected?
- How should deleted events be handled?
- Can an existing MatchEventID change its associated information?

### DQ5 – Notifications

Current notification formatting supports:

- Goals
- Empty-net goals
- Assists associated with goals
- Penalties
- Other registered events
- Match-status changes
- Final results
- Player-specific highlighting

Future work should evaluate:

- More descriptive match-start notifications.
- Configurable event preferences.
- Additional event types.
- Improved handling of event corrections.
- Further presentation improvements.

### DQ6 – Multiple matches per Watch

The current v1.2 interface returns one normalized snapshot per Watch.

The current floorball implementation monitors one match per Watch.

Future design must determine how multiple matches should be discovered, configured and monitored without breaking the generic connector interface.

### DQ7 – Team and player identification

The initial implementation uses explicit TeamIDs and PlayerIDs.

Future development should determine whether teams and competitions can be discovered automatically.

The design must support players participating in multiple teams.

### DQ8 – Concurrent state persistence

The current GitHub-based state persistence approach introduces a potential risk when multiple executions update state concurrently.

The Live workflow can restore an entire saved `state.json` file after synchronizing with `main`.

This could overwrite state changes made by another execution.

The risk should be addressed before broader concurrent Live monitoring is introduced.

### DQ9 – Multiple simultaneous Live Watches

The current Live workflow is restricted to a specific Watch using `WATCH_ID`.

Future development should determine how to execute multiple relevant Live Watches without manually editing workflow configuration for each event.

This should be designed together with state concurrency handling.

## 7. Validation approach

Prefer real-world verification, consistent with Event Platform's established ways of working.

The validation approach includes:

1. Identify an upcoming match.
2. Establish a permanent pre-match baseline.
3. Verify match-start detection.
4. Verify goal and penalty notifications.
5. Verify player-specific highlighting when applicable.
6. Verify period transitions and final result.
7. Verify state persistence.
8. Verify that unchanged data does not generate duplicate notifications.
9. Compare observed notifications with the official match history.

Avoid changing working monitoring code during an active match unless necessary.

Do not modify existing production connectors as part of floorball-specific development.

## 8. Current status

### Initial investigation – Completed

Date: 12 October 2026.

Verified:

- Player profile endpoint.
- Competition match-list endpoint.
- Individual match endpoint.
- Structured goal and assist information.
- Structured penalty information.
- Team, match-team and player identifiers.

### First implementation – Completed

Date: 14 October 2026.

Implemented:

- `connectors/ibis_floorball.py`
- Temporary iBIS authentication.
- HTTP/JSON acquisition.
- Normalized match snapshots.
- Floorball-specific notification formatting.
- MatchEventID-based event detection.
- Multiple new events in one notification.
- Player-specific highlighting.
- Optional `WATCH_ID` filtering.
- Permanent pre-match baseline.
- Automated technical tests.

The existing golf connectors remain unchanged.

### Technical verification – Completed

Verified through GitHub Actions:

- Temporary iBIS access token acquisition.
- Authenticated match API requests.
- Correct match retrieval and normalization.
- Five initial notification formatting tests.
- Multiple events in one formatted notification.
- No repeated previously observed events in formatting tests.
- Simulated final-result formatting.
- Golf notification regression testing.
- Permanent baseline establishment without notification.
- Preservation of existing state entries.
- Isolated Live execution.
- No notification for unchanged match data.

### First real-world validation – Completed

Date: 15 October 2026.

Match:

Huddinge IBS – Tyresö Trollbäcken IBK

Competition: Juniorallsvenskan D HJ18

Match ID: 1750693

Start: 20:15

Followed team ID: 20872

The monitoring operated successfully during the match.

The following notifications were received and verified:

- Goals.
- Penalties.
- Period starts.
- Period ends.
- Final result.
- Other registered match events.

The test confirmed that the platform can monitor a real floorball match and deliver relevant notifications through ntfy.

#### Findings

An additional event type for empty-net goals was identified.

The notification formatter was subsequently updated to recognize MatchEventTypeID 12 as a goal and label it `(tom bur)`.

#### Not verified during this match

Player-specific highlighting for Lukas Widegren could not be verified during real-world operation because Lukas did not score, record an assist or receive a penalty.

The functionality remains technically implemented and tested.

### Second real-world validation – Completed

Date: 17 October 2026.

Match:

IFK Haninge (B) – Tyresö Trollbäcken IBK (A)

Competition: Herrar Division 3 Södra

Match ID: 1703572

Start: 13:30

Venue: Lyckeby Sporthall

Followed team ID: 4194

Highlighted player: Lukas Widegren, PlayerID 585280

Preparation completed on 16 October 2026.

Verified before the match:

- Correct match and team identifiers.
- New Watch added to `config.yml`.
- Existing Watches preserved.
- Dedicated baseline workflow updated.
- Permanent pre-match baseline established.
- Five existing state entries preserved.
- No notification generated during baseline creation.
- Live workflow updated to `floorball-match-1703572`.
- Manual Live execution completed successfully.
- Unchanged match data produced no notification.
- Automatic execution through cron-job.org and GitHub Actions verified.
- Five-minute polling interval confirmed.

#### Real-world validation results

The user confirmed successful monitoring and notification delivery throughout the match.

Verified through user observation:

- Automatic monitoring and notification delivery at five-minute intervals.
- Notifications were received through ntfy.
- Notification content and presentation were satisfactory.
- A separate final-result notification was received with the correct result, 5–4.

Verified through inspection of the persisted `state.json`:

- Watch ID `floorball-match-1703572` was preserved.
- Match ID 1703572 was correct.
- Final score: IFK Haninge (B) 5 – Tyresö Trollbäcken IBK (A) 4.
- `has_final_result` was `true`.
- `match_status` was `4`.
- The final snapshot contained 30 registered match events with 30 unique event IDs.
- All five previously existing Watch state entries were preserved.

#### Remaining verification limitations

- Player-specific highlighting for Lukas Widegren was not observed during the match because he did not score, record an assist or receive a penalty.
- The highlighting functionality remains technically tested.
- The persisted state confirms the final match snapshot but does not independently establish that every individual notification matched the official match-event history.
- A complete notification-by-notification comparison has not been performed.
- The absence of duplicate notifications has not been independently verified through notification history.
- Updated empty-net goal formatting remains to be verified during a suitable real event.

#### Conclusion

The second real-world validation was successful.

The platform delivered usable live floorball notifications, produced the correct final-result notification and persisted the completed match state without losing existing Watch entries.

Together with the first real-world validation on 15 October, this provides sufficient evidence to prepare a first Floorball production release.

The remaining limitations should be documented rather than treated as verified functionality.

### Remaining validation and implementation questions

- Verify Lukas-specific highlighting during a future relevant real-world event.
- Confirm updated empty-net goal formatting during a suitable real event.
- Evaluate corrected and deleted match events.
- Design automatic match discovery.
- Resolve long-term Watch granularity.
- Support multiple simultaneous Live Watches.
- Improve concurrent state persistence.
- Introduce configurable notification preferences.
- Review GitHub Actions runtime compatibility.

The floorball implementation is not yet included in a published production release.

## 9. Recommended next step

Prepare a first Floorball production release based on the verified functionality.

Before publishing:

1. Update `docs/backlog.md` with the results of the second match validation.
2. Update `PROJECT_CONTEXT.md` with the latest verified development status.
3. Review the intended release scope.
4. Confirm that the release contains only verified functionality.
5. Publish the release after explicit approval.

After the release, begin a separate design phase for automatic discovery and monitoring of matches for selected teams and competitions.

The design phase should address:

- Team and competition selection.
- Automatic discovery of upcoming matches.
- Stable Watch identities.
- Monitoring multiple matches.
- Safe concurrent state persistence.
- Handling postponed and cancelled matches.

Continue using the existing Event Platform v1.2 architecture wherever possible.

Do not introduce unnecessary domain-specific behavior into the Event Platform core.

## 10. Release status

Current published production release: **v1.2.0**

Floorball monitoring has been implemented and successfully validated during two real-world matches.

No new production release has yet been published for the floorball capability.

A first Floorball release may be prepared based on the verified implementation, subject to explicit release approval.
