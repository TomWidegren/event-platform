# Event Platform

Event Platform monitors changing external data, detects relevant
changes, maintains persistent state and sends notifications.

Golf was the first use case. Swedish Floorball monitoring was
subsequently added through iBIS.

The architecture separates source acquisition, monitoring,
notification formatting, persistence and scheduling.

GitHub is the authoritative source of truth.

## Current status

Last updated: 11 November 2026.

Last documented published release: v1.2.0.

Floorball automation and the November iBIS recovery are implemented
but have not been included in a confirmed new published release.

Current capabilities:

- Daily SGF Ranking monitoring.
- GolfBox and Tournytt Live monitoring.
- Automatic Floorball match discovery.
- Persistent match registry.
- Automatic match selection and runtime Watches.
- Multiple simultaneous Live Watches.
- Player-specific Floorball highlighting.
- Coordinated final-state and match-completion persistence.
- Shared iBIS v2 authentication and signed requests.

Both cron-job.org schedules have been re-enabled.

Verified after the November recovery:

- Real iBIS match and competition-list retrieval.
- Production Floorball connector and baseline verification.
- Standalone Discovery.
- Manual production Daily execution.
- Manual and externally triggered production Live execution.
- 112 passing Floorball regression tests.
- Passing golf regression checks.

The verified automatic Live execution processed two unchanged
golf Watches. No Floorball match was eligible at that time.

Still to verify:

- The next automatic Daily execution.
- Monitoring and notification delivery throughout an active
  Floorball match using the new v2 client.
- Final-result handling during that acceptance match.

A separate incident involving missing late-match notifications
on 25 October remains unresolved.

See PROJECT_CONTEXT.md for the current handover and
docs/backlog.md for outstanding work.

## Connectors

All connectors expose:

fetch_snapshot(watch)

Connectors own acquisition and normalization.
They do not own scheduling, Git persistence or notification delivery.

### GolfBox Leaderboard

File: connectors/golfbox_leaderboard.py

Uses Playwright and Chromium.

Verified capabilities include:

- Pre-start observations.
- Different player-name formats.
- Multiple leaderboard classes.
- Hole-by-hole scoring.
- Position changes.
- Multi-round competitions.
- Round transitions.
- Final results.

Validated across Haninge, Strängnäs, NSGK/Hylinge and GolfBox
Tournament deployments.

Competition and leaderboard identifiers may both be required.

### SGF Ranking

File: connectors/sgf_ranking.py

Monitors Swedish Golf Federation rankings.

Previously verified with real ranking changes, Daily execution,
state persistence and notifications.

### Tournytt API

File: connectors/tournytt_api.py

Uses structured data from the Tournytt SSE API.

Player entries can be published before play starts.

API communication, player lookup, change detection, persistence
and notifications have been verified.

Notification presentation remains an improvement opportunity.

### Swedish Floorball / iBIS

File: connectors/ibis_floorball.py

Uses ibis_client.py for temporary v2 sessions and signed requests.

The connector retrieves and normalizes:

- Match identity and competition.
- Teams and team identifiers.
- Match datetime and status.
- Scores and final-result indicator.
- Registered match events.
- Player, assist and penalty information.

Notification formatting remains separate.

The original connector worked during real matches in October.
The updated v2 connector was verified against real completed
match data on 11 November.

Active-match acceptance after the v2 change remains outstanding.

## iBIS v2 access

Shared client: ibis_client.py

The client:

1. Retrieves a temporary Bearer token through startkit.
2. Performs a handshake in the same HTTP session.
3. Retains the session cookie.
4. Uses the returned session secret and server time.
5. Signs read-only data requests.

Supported resources:

- matches/{match_id}
- competitions/{competition_id}/matches

Requests include X-Signature, X-Timestamp and X-Nonce.

The verified flow does not require a personal iBIS login or
copied browser credentials.

The former StatsAppApi startkit endpoint returned HTTP 503
and is no longer used by the updated connector or Discovery.

The client rejects unexpected API roots, invalid handshake data,
unsupported resource paths and redirects.

See docs/ARCHITECTURE.md for signing details.

## Watch configuration

Configured Watches are stored in config.yml.

Each Watch contains:

- id
- name
- connector
- mode
- source

The ID is the stable identity used in state.json.

Connector-specific settings belong in source.

Human-readable names can change without creating a new
persistent identity.

Automatic Floorball Watches are generated from the registry
and use IDs of the form:

floorball-match-{match_id}

Obsolete manually configured Floorball Watches are excluded
from automatic Live execution.

Configured non-Floorball Live Watches are preserved.

## Execution and scheduling

cron-job.org triggers GitHub Actions through workflow_dispatch.

All schedule times use Europe/Stockholm.

### Daily

Workflow: .github/workflows/daily.yml

Schedule: 08:00 every day.

Responsibilities:

1. Run Daily golf monitoring.
2. Persist changed golf state when required.
3. Run Floorball Discovery.
4. Persist registry changes when required.

The external Daily job has been re-enabled.
Its next scheduled execution remains to be observed.

### Live

Workflow: .github/workflows/live.yml

Entry point: event_platform_live.py

Schedule:

Every five minutes, 06:00–23:55 daily.

Cron expression:

*/5 6-23 * * *

Runtime selection determines which Floorball matches are eligible.

Live also processes configured GolfBox and Tournytt Watches.

Events outside the scheduling window require a deliberate
schedule adjustment.

Automatic dispatch and the corresponding GitHub Actions execution
have been verified after reactivation.

### Workflow coordination

Participating workflows use the GitHub Actions concurrency group:

event-platform-state

cancel-in-progress is false.

Git persistence also includes merge, conflict and retry handling.

### Chromium installation

Daily and Live install Chromium without --with-deps.

This avoids the repeated full system-package installation that
stalled Daily during recovery.

A subsequent Daily execution succeeded with the updated command.

### Verifying execution

HTTP 204 in cron-job.org confirms that GitHub accepted the
dispatch request.

Check the corresponding GitHub Actions result to determine
whether monitoring completed successfully.

The scheduler response alone does not establish monitoring success.

## Automatic Floorball Discovery

Main module: floorball_discovery.py

Discovery retrieves competition match lists through the shared
iBIS client and filters them for configured teams.

Initial configured teams:

| Team | TeamID | CompetitionID |
| --- | --- | --- |
| Tyresö Trollbäcken IBK – JAS | 20872 | 45004 |
| Tyresö Trollbäcken IBK – Herrar | 4194 | 44356 |

Highlighted player:

Lukas Widegren, PlayerID 585280.

Monitoring follows the configured teams regardless of whether
the highlighted player participates.

Discovery updates match identity and scheduling information.
It preserves historical entries and Live-owned completion status.

The discovery function itself does not write files, execute Git,
send notifications or activate monitoring.

On 11 November, real-data verification produced 31 total registry
entries and zero required changes.

The count includes preserved historical matches.
It does not represent 31 newly discovered or upcoming matches.

## Automatic match selection

Main module: floorball_match_selection.py

Floorball monitoring activates 15 minutes before scheduled start.

Selection excludes completed, cancelled and postponed matches.

Multiple matches can be eligible simultaneously.

There is currently no upper time limit for overdue matches.
General outage recovery and expiration rules remain future work.

The next match in the inspected registry is:

- MatchID: 1703587.
- Tyresö Trollbäcken IBK (A) – Hammarbyhöjden IBK.
- Start: 14 November 2026, 15:00.
- Monitoring activation: 14:45.

These times use Europe/Stockholm.

## Persistent data

### state.json

Stores normalized monitoring snapshots under stable Watch IDs.

Each entry includes serialized snapshot data and snapshot fields.

### match_registry.json

Stores discovered matches and monitoring lifecycle information.

Discovery owns match identity and scheduling fields.

Live owns monitoring completion status.

Discovery must not reactivate completed matches.

### Live persistence

Automatic Live merges changed Watch entries against the latest
repository state.

It preserves unrelated entries and rejects stale same-Watch updates.

Normal completion persists the final snapshot and registry
completion together in one Git commit.

Persistence uses git reset --hard while refreshing its checkout.
It requires a dedicated disposable GitHub Actions working directory.

Do not run this persistence code in a working directory containing
user changes.

## Notifications

Formatting: notification_formatters.py

Provider: ntfy

Floorball formatting supports:

- Match identity and score.
- Match-status changes.
- Period events.
- Goals and penalties.
- Final results.
- Player-specific goals, assists and penalty highlighting.

Empty-net goals use event type 12 and are labelled (tom bur).

Lukas-specific assist highlighting was observed in real operation
on 23 October.

New events are identified using previously unseen event IDs.

## Known limitations and incidents

- Notifications are sent before Git persistence.
- Exactly-once notification delivery is not guaranteed.
- A connector failure can fail an entire workflow.
- A first Floorball observation containing activity is rejected
  for review rather than silently baselined.
- Overdue matches do not expire automatically.
- Corrected and deleted events require further evaluation.
- Source timestamps without UTC offsets are interpreted as Swedish
  local time, pending source-model verification.
- Cancellation and abandonment field interpretation remains provisional.

On 25 October, final state and completion were persisted for
match 1703577, but the final two goal notifications and
final-result notification were not received.

The cause remains unresolved and is separate from the November
authentication incident.

### Missed match during the outage

Match 1750719 on 6 November was not successfully monitored.

With explicit user approval, its registry monitoring_status was
manually set to completed.

No final snapshot was added and no historical notifications
were sent.

This was administrative closure of monitoring, not normal
automatic completion or successful match acceptance.

## Testing

Permanent consolidated workflow:

.github/workflows/test-regression.yml

It runs golf regression checks and discovers:

tests/test_floorball_*.py

Coverage includes authentication, request signing, Discovery,
registry ownership, selection, Watch merging, formatting,
Live integration and Git persistence.

Latest verified result after v2 integration:

112 Floorball tests passed on 11 November 2026.

The golf regression step also passed.

Existing additional workflows include:

- test-floorball.yml: real connector retrieval, formatting
  and temporary baseline verification.
- test-ibis-new-api.yml: isolated signed API diagnostics.
- floorball-daily-discovery.yml: manual Discovery and persistence.
- floorball-baseline.yml: historical baseline tooling.

These are not additional external production schedules.

Review redundant workflows after operational acceptance.
Preserve useful tests and diagnostics.

Do not create a new workflow for every individual test.

## Main project files

Production workflows:

- .github/workflows/daily.yml
- .github/workflows/live.yml

Shared acquisition:

- ibis_client.py

Connectors:

- connectors/golfbox_leaderboard.py
- connectors/sgf_ranking.py
- connectors/tournytt_api.py
- connectors/ibis_floorball.py

Monitoring and presentation:

- watcher.py
- event_platform_live.py
- notification_formatters.py

Floorball automation:

- floorball_discovery.py
- floorball_discovery_changes.py
- floorball_live.py
- floorball_match_selection.py
- floorball_watch_merge.py
- floorball_registry.py
- floorball_registry_merge.py
- floorball_git_persistence.py
- floorball_atomic_persistence.py

Configuration and persistence:

- config.yml
- state.json
- match_registry.json

Tests:

- tests/test_floorball_*.py
- Golf regression checks in test-regression.yml

## Development and documentation

Start with the current PROJECT_CONTEXT.md from GitHub.

Verify that any available ChatGPT Project source is current.
Project sources and attachments are not synchronized automatically.

Read the relevant repository documentation before implementation.

Important documents:

- PROJECT_CONTEXT.md: current status and handover.
- docs/ARCHITECTURE.md: implemented architecture.
- docs/decisions.md: decisions and rationale.
- docs/backlog.md: incidents and future work.
- docs/ways-of-working.md: development procedures.
- docs/design-v1.2.md: unified connector design history.
- docs/design-floorball.md: initial Floorball investigation.
- docs/design-floorball-automation.md: automation design history.

Follow:

One agreed goal.
One coherent change.
One appropriate verification.
Then the next increment.

Provide complete replacement files for substantial changes.
Reuse successful evidence and avoid repeating completed tests.

Protect working monitoring during active events.

Before ending a meaningful session:

- Record verified results and unresolved issues.
- Update relevant documentation.
- Confirm repository commits.
- Refresh ChatGPT Project handover sources.

Use independent new conversations before context becomes
difficult to manage.

## Next priorities

1. Observe scheduled Daily execution after reactivation.
2. Complete active-match acceptance using the new iBIS client.
3. Investigate the missing late-match notifications.
4. Reconcile remaining documentation.
5. Consolidate obsolete workflows and configuration after acceptance.
6. Agree on and deliberately publish the next release.

The GitHub scheduler token expires on 28 November 2026.
Renew it before expiration and verify both dispatch jobs.

Never store tokens in repository documentation.
