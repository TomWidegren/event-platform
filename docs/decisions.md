# Event Platform – Decisions

This document records architectural and operational decisions
and their rationale.

It is not the current architecture description.
See ARCHITECTURE.md for the implemented architecture.

Superseded decisions remain identifiable.

Last updated: 11 November 2026.

## D001 – Event Platform is the product name

Decision:

The project is called Event Platform.

Reason:

Golf was the first use case, but the platform should support
other event types and data sources.

## D002 – Connectors represent platforms where practical

Decision:

Prefer connectors for underlying platforms or data models
rather than individual websites.

Examples include golfbox_leaderboard and sgf_ranking rather
than separate Haninge and Strängnäs connectors.

Before creating a connector, check whether the source uses
an already supported platform.

Reason:

The same underlying technology can serve multiple websites
and events.

## D003 – Connectors acquire and normalize data

Decision:

Connectors own:

- External-source access.
- Entity identification.
- Data extraction.
- Snapshot normalization.

They do not own:

- State persistence.
- Change detection.
- Notifications.
- Scheduling.

Reason:

This separates source acquisition from platform behavior
and keeps connectors reusable.

## D004 – The monitoring layer owns state and change detection

Decision:

The monitoring layer owns configuration loading, connector
selection, snapshot comparison, change detection, notification
triggering and state updates.

watcher.py provides the generic monitoring implementation.

event_platform_live.py coordinates automatic Live execution
using existing connectors, formatting and monitoring conventions.

Reason:

Common monitoring behavior should not be duplicated in connectors.

Automatic selection and coordinated persistence should not add
Floorball acquisition logic to the generic watcher.

Updated: 22 October 2026.

## D005 – Scheduling is external

Decision:

Event Platform does not own its scheduler.

cron-job.org currently triggers GitHub Actions.

Reason:

Scheduling can be replaced without redesigning acquisition
or monitoring.

## D006 – Daily and Live are separate modes

Decision:

The platform supports daily and live execution.

Daily handles slower-changing sources and discovery.
Live handles frequently changing event data.

Reason:

These functions require different frequencies and operational
behavior.

## D007 – Live polling interval is five minutes

Decision:

Live monitoring polls every five minutes.

The October implementation kept the external schedule enabled
continuously, with runtime Watch selection determining which
Floorball matches were eligible.

Reason:

Five-minute polling provides useful updates.
Automatic selection avoids per-match scheduler changes.

Updated: 22 October 2026.

Status:

The five-minute interval remains current.
The continuous all-day schedule was superseded by D030.

## D008 – Daily monitoring runs every day

Decision:

Daily runs once per day.

Responsibilities include:

- SGF Ranking.
- Automatic Floorball Discovery.

Reason:

Both functions can reuse the existing Daily schedule without
continuous polling.

Updated: 22 October 2026.

Operational note:

Schedules were temporarily disabled during the November incident
and re-enabled after recovery verification.

## D009 – First observations depend on monitoring mode

Decision:

Daily first observations establish a baseline without notification.

A first valid golf Live result can establish a baseline and
generate a notification.

An empty or not-yet-started leaderboard is not a real result.

A first pre-match Floorball observation establishes a baseline
without notification.

The automatic Live runner rejects a first Floorball observation
that already contains match activity or a final result.

Reason:

Sources have different lifecycles.

Floorball requires a known baseline to distinguish new events
from historical activity.

General late-baseline recovery remains future work.

Updated: 22 October 2026.

Exception:

D031 records a specific administrative closure after the outage.
It does not change normal baseline behavior.

## D010 – Position changes are relevant Live changes

Decision:

A player's position change can trigger a notification even
when the player's own score has not changed.

Reason:

Other competitors can change the watched player's position.

A future preference may distinguish all changes from
player-score-only changes.

## D011 – State is persisted in the repository

Decision:

state.json stores the latest monitoring snapshots.

GitHub Actions commits changed state.

Automatic Live merges changed Watch entries against the latest
repository state rather than replacing the complete file blindly.

Reason:

Actions runners are stateless.

Independent executions require persistent state, preservation
of unrelated Watches and concurrency protection.

Updated: 22 October 2026.

## D012 – Source-specific identifiers belong in configuration

Decision:

Reusable connectors must not permanently hard-code event-specific
identifiers.

Competition, leaderboard, player, team and other source settings
belong in configuration or generated runtime Watches.

Reason:

The next event should normally require configuration rather
than Python changes.

## D013 – Verify behavior with real events

Decision:

Use real-world validation where practical.

Automated tests remain necessary but do not establish operational
acceptance on their own.

Reason:

Real events revealed changing layouts, competition classes,
round transitions, final-result behavior and Floorball
event-model details that static tests alone could miss.

## D014 – Protect working monitoring during events

Decision:

Avoid nonessential production changes during a working live event.

Reason:

Changes introduce risk and can disrupt an important acceptance
opportunity.

## D015 – Repository documentation is long-term memory

Decision:

Architecture, decisions, working procedures, backlog and handover
are stored in the repository.

Chat history is not the source of truth.

Reason:

Conversation context is finite.
Repository documentation enables reliable session restoration.

Operational clarification:

ChatGPT Project sources and attachments are not automatically
synchronized with GitHub.

Their freshness must be established at session start.
Committed handover updates should also be reflected in the
corresponding Project sources.

Detailed procedures belong in ways-of-working.md.

## D016 – Unified Connector Interface

Decision:

All connectors expose:

fetch_snapshot(watch)

A Watch contains:

- id
- name
- connector
- mode
- source

The ID is its stable persistent identity.

Human-readable names and source configuration may change without
creating a new Watch identity.

The core understands the generic Watch structure but does not
interpret source-specific configuration.

Connectors own the complete acquisition lifecycle, including
HTTP, Playwright, HTML parsing, JSON APIs, SSE or other technology.

A connector returns its own normalized snapshot or None.

There is no fixed platform-wide snapshot field schema.

The monitoring layer owns comparison, state and notification
triggering.

A separate formatting layer interprets source-specific fields
and creates notification content.

The delivery provider delivers the formatted notification.

Reason:

These boundaries keep the platform independent of acquisition
technology, entity type, configuration details and presentation.

Stable IDs preserve state continuity as configuration evolves.

Design history: design-v1.2.md.

## D017 – Discovery is separate from Live monitoring

Decision:

Discovery retrieves matches, maintains identity and scheduling,
registers matches and updates schedules.

Live selects registered matches, retrieves observations, detects
changes, generates notifications and updates monitoring lifecycle.

Reason:

The functions have different frequencies and responsibilities.

Frequent Live polling should not repeat match discovery.

Date: 22 October 2026.

## D018 – Match registry is separate from Watch state

Decision:

match_registry.json stores discovered matches.

state.json stores monitoring snapshots.

Registry entries use stable iBIS MatchIDs.

Reason:

Match existence and scheduling differ from observed monitoring
state.

Both must survive independent executions.

Date: 22 October 2026.

## D019 – Registry fields have explicit ownership

Decision:

Discovery owns match identity, scheduling, team, competition
and source scheduling information.

Live owns monitoring lifecycle and completion.

Discovery must not reactivate completed matches.

Live must not alter Discovery-owned scheduling or implicitly
create unknown matches.

Reason:

Explicit ownership prevents independent processes from overwriting
each other's information.

Date: 22 October 2026.

## D020 – Dynamic Watches replace manual Floorball selection

Decision:

Live generates Floorball Watches from the registry.

Manual Floorball Watches are excluded from automatic execution.

Configured non-Floorball Live Watches are preserved.

Generated IDs use:

floorball-match-{match_id}

Reason:

This removes per-match configuration changes and prevents
duplicate manual and automatic monitoring.

Date: 22 October 2026.

## D021 – Activate before scheduled match start

Decision:

Eligible matches enter monitoring 15 minutes before start.

Cancelled, postponed and completed matches are excluded.

Multiple simultaneous matches are supported.

Reason:

A pre-match baseline reduces the risk of confusing historical
events with new activity.

The activation behavior was verified using simulated time.

Date: 22 October 2026.

Limitation:

The current selector has no upper limit for overdue matches.
Expiration and recovery require a separate design.

## D022 – Reuse Daily for Discovery

Decision:

Floorball Discovery runs after golf monitoring in daily.yml.

The existing external Daily schedule is reused.

Reason:

Reusing proven scheduling avoids unnecessary infrastructure
while preserving separate Python responsibilities.

Date: 22 October 2026.

## D023 – Reuse the Live workflow and scheduler

Decision:

live.yml remains the production Live workflow.

It executes event_platform_live.py.

The previous hard-coded WATCH_ID was removed.

The existing external Live job processes configured golf Watches
and dynamically selected Floorball matches.

Reason:

A separate Floorball scheduler is unnecessary.

Date: 22 October 2026.

## D024 – Preserve unrelated state and reject stale updates

Decision:

Automatic Live refreshes repository state before persistence.

Only changed Watch entries are merged.

Optimistic checks compare the original observation state with
the latest persisted entry.

A stale same-Watch update is rejected.

Reason:

Independent executions must not overwrite unrelated or newer
observations.

Regression tests cover the protection.
Broader operational concurrency remains a validation area.

Date: 22 October 2026.

## D025 – Persist normal completion together with final state

Decision:

Normal automatic completion persists the final snapshot in
state.json and completed status in match_registry.json together
in one Git commit.

Completed matches must not automatically reactivate.

Reason:

Final observation and lifecycle must remain consistent.

Atomic persistence has passed automated tests.

Date: 22 October 2026.

Exception:

D031 records an explicitly approved administrative closure
without a final snapshot.

## D026 – Exactly-once notification delivery is not guaranteed

Decision:

Automatic Live sends notifications before committing state.

A notification can repeat if delivery succeeds but persistence
fails.

Reason:

ntfy delivery and Git persistence are independent operations.

This limitation remains documented.
Stronger coordination can be considered if operational evidence
justifies it.

Date: 22 October 2026.

## D027 – Coordinate production workflows with concurrency

Decision:

Participating workflows use:

event-platform-state

cancel-in-progress is false.

Reason:

Serializing participating executions reduces overlapping
repository updates.

Git conflict checks and retries remain necessary.

Date: 22 October 2026.

## D028 – Retain Playwright and optimize Live installation

Decision:

GolfBox continues to use Playwright and Chromium.

Live installs Chromium without the full operating-system
dependency installation on every execution.

Reason:

The optimized installation reduced observed execution from
4 minutes 20 seconds to approximately 37 seconds, followed
by an automatic execution of approximately 30 seconds.

Date: 22 October 2026.

Extension:

D032 applies the same installation command to Daily after
a verified installation problem.

## D029 – Share iBIS v2 authentication and signing

Decision:

ibis_client.py owns temporary iBIS sessions, authentication
and signed read-only requests.

Both the match connector and Discovery use this client.

The verified flow uses startkit, handshake, the resulting session
cookie and HMAC-SHA256 request signing.

Personal iBIS credentials and copied browser tokens are not
required for the verified flow.

Existing connector normalization, Discovery filtering and core
monitoring boundaries are preserved.

The client currently supports match retrieval and competition
match-list retrieval.

It validates the API root, handshake data and resource paths,
and rejects redirects and unsuccessful responses.

Reason:

The old startkit endpoint returned HTTP 503.

The public website's v2 flow was established from its JavaScript
and verified from GitHub Actions.

Sharing acquisition code prevents authentication duplication
between Discovery and the connector.

Verification:

- Real match and competition requests returned HTTP 200.
- Production connector and Discovery checks passed.
- Consolidated Floorball regression reached 112 passing tests.

Active-match acceptance with the new client remains outstanding.

Date: 11 November 2026.

## D030 – Limit Live scheduling to a daily time window

Decision:

Live runs every five minutes between 06:00 and 23:55 daily.

Timezone: Europe/Stockholm.

Cron expression:

*/5 6-23 * * *

Daily remains scheduled for 08:00.

Runtime Floorball selection continues to determine match eligibility
within the external scheduling window.

Reason:

The user approved reducing overnight executions while retaining
coverage for early golf and evening matches.

The time window applies to all configured Live Watches.

Events outside this window would require a deliberate schedule
adjustment.

This supersedes only the all-day scheduling part of D007.
The five-minute interval remains unchanged.

Verification:

The re-enabled Live job returned HTTP 204 and its corresponding
GitHub Actions execution succeeded.

Automatic Daily execution after reactivation remains to be observed.

Date: 11 November 2026.

## D031 – Administratively close missed match 1750719

Decision:

With explicit user approval, only monitoring_status for
MatchID 1750719 was changed from scheduled to completed.

No final snapshot was added.
No historical notifications were sent.
Existing state was preserved.

Reason:

The match was missed during the outage and had no saved Watch
state.

Without intervention, selection would still choose it and the
Live runner would reject its late first observation.

The user requested minimal storage and no notifications.

This records closure of monitoring, not successful monitoring
or verified final-state persistence.

It is a specific exception to normal completion under D025
and does not implement general outage recovery.

Date: 11 November 2026.

## D032 – Use optimized Chromium installation in Daily

Decision:

Daily installs Chromium using:

python -m playwright install chromium

The --with-deps option was removed.

Reason:

The existing installation stalled while downloading Ubuntu
font packages before monitoring began.

The replacement follows the previously verified Live installation
approach.

Verification:

The subsequent production Daily execution completed through
Floorball Discovery successfully.

This extends D028 to Daily.

Date: 11 November 2026.
