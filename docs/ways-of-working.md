# Event Platform – Ways of Working

This document defines how Event Platform development sessions
are conducted.

GitHub is the authoritative source of truth.

ChatGPT conversations are working environments, not the project's
long-term memory.

## 1. Restore current context

Before proposing changes:

1. Obtain the current PROJECT_CONTEXT.md from GitHub.
2. Read README.md.
3. Read docs/ARCHITECTURE.md.
4. Read docs/decisions.md.
5. Read docs/ways-of-working.md.
6. Read docs/backlog.md.
7. Identify the last documented published release, current
   implementation and operational status.
8. Read source files relevant to the agreed goal.

### Verify Project-source freshness

A file available as a ChatGPT Project source or previous attachment
must not automatically be treated as the latest GitHub version.

If freshness has not been established, request the current
PROJECT_CONTEXT.md from GitHub before determining project status
or recommending development work.

If the user explicitly supplies the current GitHub version,
use it without repeatedly asking for confirmation.

An updated attachment takes precedence over an older Project
source for that session.

Do not reconstruct status from conversation history when current
repository documentation is available.

### Request files incrementally

When direct repository access is unavailable:

- Request files one at a time.
- Explain briefly why the next file is needed.
- Do not guess filenames and present them as known facts.
- Use repository search results to identify uncertain filenames.
- Distinguish GitHub code search from browser page search.
- Do not require a repository archive unless the user prefers it.

Files already supplied and inspected need not be requested again
unless their contents may have changed.

## 2. Agree on one goal

Every session starts with a clear goal.

Example:

Restore reliable iBIS match-data acquisition.

Avoid expanding into unrelated architecture, cleanup or features.

Related implementation tasks may be grouped when they serve
the same goal.

Record unrelated ideas in the backlog.

## 3. Work in coherent, verifiable increments

Use this cycle:

1. Agree on the goal.
2. Inspect relevant existing files.
3. Define a coherent implementation increment.
4. Implement the related changes.
5. Run appropriate verification.
6. Evaluate the evidence.
7. Continue.

Do not combine unrelated changes before verification.

Do not artificially divide one coherent implementation into
numerous manual fragments.

Related modules, tests and workflow changes may be delivered
together when they form one understandable increment.

## 4. Prefer evidence over assumptions

When a source behaves unexpectedly:

- Inspect actual requests, responses or pages.
- Inspect logs and state.
- Compare observed behavior with expectations.
- Use temporary diagnostics when necessary.

Do not guess selectors, authentication behavior, signatures,
schemas or source semantics when they can be observed.

Distinguish clearly between:

- Observed facts.
- Inferences.
- Implemented behavior.
- Test results.
- Unverified scenarios.

Do not present an unverified URL as a confirmed working link.

A green diagnostic workflow is not proof of successful acquisition
if its code treats denied requests as successful diagnostics.

Acceptance checks should fail when the required outcome fails.

## 5. Provide complete, directly copyable files

For substantial code or documentation changes, provide the
complete intended replacement file.

The user should not need to reconstruct a file from fragments.

A complete replacement must:

- Include necessary imports.
- Preserve required existing functionality.
- Remove obsolete code only when justified.
- Use correct indentation.
- Identify the exact repository path.
- Appear in one continuous copyable code block.

Do not nest Markdown fences inside an outer replacement block.

Provide each related file separately.

Small, unambiguous edits may be described individually when
genuinely simpler.

If the user requests complete files, always provide them.

Avoid asking the user to insert indentation-sensitive blocks
into embedded Python within YAML workflows.

## 6. Deliver agreed work

Once the goal and implementation direction are agreed, proceed.

Do not repeatedly request replies such as OK, Kör or Fortsätt
before routine implementation.

If the agreed next step is code, deliver the code or completed
result rather than another promise.

Ask for a decision when:

- Essential information is missing.
- Architecture or scope would materially change.
- Production behavior would change beyond the agreed work.
- Destructive or irreversible action needs authorization.
- Recovery requires a choice about notifications or saved data.

A request for a missing source file is not another approval step.

## 7. Reuse completed work and verification

Before proposing a change or test, establish what is already done.

Do not recreate existing configuration, modules or infrastructure
without a deliberate reason.

Reuse successful evidence.

Repeat tests when relevant code changes or new evidence justifies
it, not merely because the conversation continues.

Before further diagnostics, identify:

- The unanswered question.
- The new evidence the test can provide.
- The decision its result will support.

If repeated tests do not narrow the issue, reconsider the approach.

## 8. Use risk-based verification

### Low risk

Examples:

- Documentation.
- Comments.
- Nonfunctional cleanup.

Normally require content review.

### Moderate risk

Examples:

- Connector acquisition.
- Authentication changes.
- Formatting.
- Configuration processing.

Require focused tests and appropriate regression checks.

External acquisition also requires verification with real data.

### High risk

Examples:

- Persistent state.
- Git concurrency.
- Notification delivery.
- Live scheduling.
- Automatic completion.
- Outage recovery.

Require focused tests, relevant regression checks and controlled
operational verification.

Match verification effort to actual risk.

## 9. Reuse consolidated regression testing

Permanent workflow:

.github/workflows/test-regression.yml

It runs golf regression checks and discovers:

tests/test_floorball_*.py

Latest confirmed result:

112 Floorball tests passed on 11 November 2026 after iBIS v2
integration. The golf regression step also passed.

Before adding tests, verify that discovery includes them.

Do not create a separate workflow for every test.

Reuse existing diagnostics where appropriate.

When requesting results:

- Ask for the relevant workflow step.
- If successful, request only its summary or necessary evidence.
- If failed, request the failing test name and full traceback.
- Do not require complete logs unnecessarily.

Preserve useful Python tests when removing redundant workflows.

## 10. Do not silently change direction

When new evidence affects the agreed approach:

1. Explain the evidence.
2. Explain its consequence.
3. Propose the change.
4. Agree before materially changing scope or architecture.

Prefer the smallest implementation consistent with existing
architecture.

Avoid infrastructure for hypothetical requirements.

Do not repeatedly reopen an agreed design without new evidence.

## 11. Design architectural changes first

For architectural refactoring:

1. Complete the design.
2. Record it in a design draft.
3. Review and agree.
4. Implement.
5. Verify against the design.

Ordinary fixes and incremental improvements follow the normal
implementation cycle.

Do not leave a partially implemented architecture while its design
is still unresolved.

## 12. Separate diagnostics from production

Temporary diagnostics may investigate unknown source behavior.

Once understood:

- Implement the production solution cleanly.
- Remove unnecessary temporary debugging.
- Verify relevant behavior.
- Review redundant diagnostic workflows.

Do not confuse a diagnostic result with production acceptance.

Do not leave temporary mechanisms in production accidentally.

## 13. Protect working live systems

During an active event or important acceptance test:

- Prioritize stability.
- Preserve state and historical records.
- Avoid refactoring and cosmetic changes.
- Avoid duplicate Watches.
- Fix only issues materially affecting monitoring.
- Preserve useful diagnostics.

Documentation may be updated when it does not affect execution.

Prefer cleanup and generalization after the event.

## 14. State verification categories explicitly

### Implemented

Code exists.

### Automated-test verified

Controlled tests passed.

### Workflow verified

The relevant workflow executed successfully.

### Operationally verified

Behavior was observed with real external data.

### Accepted

Agreed acceptance criteria were met.

A successful historical match retrieval does not establish
continuous active-match monitoring or notification delivery.

A Live run with no eligible Floorball matches does not establish
Floorball match acceptance.

Record limitations and unverified cases.

## 15. Restore scheduling deliberately

Before reactivating external schedules:

1. Verify the relevant source acquisition.
2. Run the production workflow manually.
3. Review state and notification implications.
4. Agree on scheduling changes.
5. Enable and save the external job deliberately.
6. Observe an external dispatch.
7. Verify the corresponding GitHub Actions execution.

For GitHub workflow_dispatch:

HTTP 204 confirms that GitHub accepted the request.
It does not establish that monitoring succeeded.

If the next scheduled execution has not yet occurred, record
the job as enabled but automatic execution as unverified.

Use Europe/Stockholm consistently for user-facing schedule times.

Do not change scheduler credentials unnecessarily.

Never request or expose token values in screenshots or logs.

## 16. Handle outage recovery explicitly

Before running Live after an outage:

- Inspect overdue registry entries.
- Inspect relevant Watch state.
- Inspect selection and baseline behavior.
- Determine potential historical notifications.
- Preserve unrelated data.

Do not silently:

- Create a late baseline.
- Discard historical events.
- Mark missed monitoring as successfully verified.
- Delete or reset state.
- Introduce expiration rules.

If the user approves an administrative closure, record:

- The exact match.
- The changed fields.
- Whether a final snapshot was saved.
- Whether notifications were sent.
- The reason for the exception.

A specific manual exception is not a general recovery design.

## 17. Record new knowledge

At meaningful checkpoints, determine whether the session changed:

- Architecture.
- Decisions.
- Source knowledge.
- Production behavior.
- Scheduling.
- Release status.
- Working procedures.
- Outstanding work.

Update the appropriate documents:

- ARCHITECTURE.md: current implementation.
- decisions.md: decisions and rationale.
- backlog.md: outstanding work.
- Relevant design documents: detailed findings.
- README.md: overview and operation.
- ways-of-working.md: process.
- PROJECT_CONTEXT.md: concise status and handover.

Document verified facts, not intended behavior.

Keep detailed technical findings out of the primary handover
when another document is the appropriate home.

### Refresh ChatGPT Project sources

After committing updated handover documents:

- Refresh the corresponding ChatGPT Project sources.
- In particular, refresh PROJECT_CONTEXT.md.
- Refresh ways-of-working.md when its procedures changed.

If the assistant cannot update Project sources directly, ask
the user to replace them using the committed GitHub versions.

Do not claim sources were refreshed without confirmation.

Repository commits and Project-source refresh are separate steps.

## 18. Keep documentation current

ARCHITECTURE.md describes the current system.

Historical reasoning belongs in decisions.md.

Keep superseded decisions identifiable.

Design documents may preserve original assumptions when clearly
distinguished from implemented behavior.

Git history and releases provide detailed implementation history.

Avoid unnecessary duplication.

After documenting a major recovery, reconcile stale descriptions
of blockers, disabled schedules and outdated acceptance status.

## 19. Manage conversation lifecycle proactively

Prefer a completely new conversation within the project when:

- Beginning a new goal or version.
- Completing a meaningful checkpoint.
- Moving between substantial development phases.
- The conversation becomes difficult to navigate.
- Many files and verification cycles have accumulated.

A new conversation does not imply a new release.

Avoid branching or handing off a very long conversation merely
to obtain a fresh context window.

Do not rely on unfinished Work continuations as authoritative
technical evidence.

### Before changing conversations

1. Complete or safely pause current implementation.
2. Record verified results.
3. Record unresolved issues.
4. Update relevant documentation.
5. Confirm commits.
6. Refresh Project handover sources.
7. Identify the next goal.

Do not interrupt an active production test solely to change chats.

### Starting a new session

The user should only need to say:

Nu fortsätter vi med Event Platform.

The assistant should then:

1. Establish that PROJECT_CONTEXT.md is current.
2. Request the current GitHub version if uncertain.
3. Read working procedures and relevant documentation.
4. Identify current release and operational status.
5. Confirm the next goal.
6. Request only required source files.
7. Continue without repeating completed work.

## 20. End with a checkpoint

When the user says:

Vi avslutar för idag.

The assistant should:

1. Summarize completed work.
2. Identify verified behavior.
3. Identify unresolved risks.
4. Determine necessary documentation updates.
5. Deliver complete replacements one file at a time when that
   is the user's preferred workflow.
6. Confirm commits or explicitly record pending commits.
7. Verify handover consistency.
8. Confirm Project-source refresh.
9. Identify the recommended next goal.

Do not describe a session as fully documented while required
updates are uncommitted or unacknowledged.

## 21. Release deliberately

Publish a release when a meaningful capability has been verified
and the user explicitly approves publication.

Use semantic versioning:

- Patch: compatible fixes.
- Minor: new backward-compatible capability.
- Major: incompatible architectural changes.

Do not infer a published release from deployed code.

Confirm release status from repository tags or releases when
available.

A new conversation does not require a release.

## Core principles

One agreed goal.

One coherent implementation increment.

One appropriate verification.

Then the next increment.

Prefer complete files, evidence and a clean handover.

Keep GitHub authoritative and Project sources current.
