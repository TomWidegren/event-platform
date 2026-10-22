
# Event Platform – Ways of Working

This document defines how development sessions for Event Platform should be conducted.

The purpose is to keep development predictable, efficient, understandable and easy to resume across sessions and ChatGPT conversations.

The GitHub repository is the authoritative source of truth.

ChatGPT conversations are working environments, not the project's long-term memory.

## 1. Start every session by restoring context

Before proposing changes:

1. Read `PROJECT_CONTEXT.md` first.
2. Read `README.md`.
3. Read `docs/ARCHITECTURE.md`.
4. Read `docs/decisions.md`.
5. Read `docs/ways-of-working.md`.
6. Read `docs/backlog.md`.
7. Identify the current published release and ongoing development.
8. Read only the source files relevant to the session's goal.

Do not rely on conversational memory when repository documentation is available.

Do not assume that Project files or ChatGPT attachments are automatically synchronized with GitHub.

When current repository contents are needed and direct GitHub access is unavailable, request the relevant files.

## 2. Define one goal for the session

Every development session starts with a clear goal.

Example:

> Make the GolfBox connector reusable for the next competition.

Avoid expanding the session into unrelated architecture or feature work unless a discovered issue blocks the agreed goal.

New ideas should normally be added to the backlog rather than implemented immediately.

A session may contain multiple related implementation tasks when they serve the same agreed goal.

## 3. Work in coherent, verifiable increments

Development should follow this cycle:

1. Agree on the goal.
2. Inspect relevant existing files.
3. Define a coherent implementation increment.
4. Implement the related changes.
5. Run appropriate verification.
6. Evaluate the result.
7. Continue to the next increment.

Avoid changing multiple unrelated things before verification.

However, do not artificially divide a single coherent change into numerous small manual steps.

Related Python modules, workflow changes and tests may be delivered together when they form one understandable implementation.

The guiding principle is:

**One goal, one coherent change, one appropriate verification, then the next change.**

## 4. Prefer evidence over assumptions

When an external source behaves unexpectedly:

- Inspect the real page or API.
- Inspect logs.
- Inspect state.
- Use temporary debug output when necessary.
- Compare observed behavior with documented expectations.

Do not guess HTML structure, selectors, API behavior or data formats when they can be observed.

The SGF Ranking, GolfBox and iBIS implementations demonstrated the value of this approach.

Clearly distinguish:

- Implemented functionality.
- Automated-test verification.
- Production workflow verification.
- Real-world acceptance.
- Planned or unverified functionality.

A successful automated test does not automatically establish real-world acceptance.

## 5. Provide complete, directly copyable files

For substantial code or documentation changes, provide the complete intended replacement file.

Do not require the user to combine several code fragments, insert code at different locations or manually reconstruct the final result.

A complete replacement should:

- Include all necessary imports.
- Preserve required existing functionality.
- Remove obsolete code only when justified.
- Use correct indentation.
- Be directly copyable into GitHub.
- Be presented in one continuous code block.

Do not place nested Markdown code fences inside an outer code block.

For multiple related files, provide each complete file separately and identify its repository path.

Small, unambiguous changes may still be described as individual edits when that is genuinely simpler.

When the user explicitly requests complete files, always provide complete files.

## 6. Deliver instead of repeatedly requesting approval

Once the user has agreed on a goal and implementation direction, proceed with the agreed work.

Do not repeatedly describe the next step and wait for responses such as:

- OK
- Kör
- Fortsätt

If the next agreed step is to write code, the next assistant response should contain the code or the completed deliverable.

Avoid messages that merely promise a future implementation.

Request approval only when:

- An architectural decision is required.
- A meaningful scope change is proposed.
- Essential information is missing.
- An action could affect working production functionality.
- A destructive or irreversible change requires confirmation.

Routine implementation within the agreed scope does not require repeated approval.

## 7. Do not repeat completed work

Before asking for a change, establish what has already been completed.

Do not instruct the user to recreate files, imports, configuration or infrastructure that already exists unless there is a deliberate reason to replace it.

If uncertain, inspect the current file before proposing a change.

A successful verification should be recorded and reused as evidence rather than unnecessarily repeated.

Repeat regression tests when relevant code changes, not simply because the conversation continues.

## 8. Use risk-based verification

Verification effort should reflect the risk of the change.

### Low-risk changes

Examples:

- Documentation updates.
- Comments.
- Nonfunctional cleanup.

Normally require content review rather than full production regression testing.

### Moderate-risk changes

Examples:

- Connector improvements.
- Notification formatting.
- Configuration processing.

Require relevant automated tests and regression checks.

### High-risk changes

Examples:

- State persistence.
- Git concurrency.
- Notification delivery.
- Live scheduling.
- Automatic match completion.

Require focused automated tests, appropriate regression testing and controlled operational verification.

Do not create a new GitHub Actions workflow for every individual test.

Prefer the existing consolidated regression workflow.

## 9. Maintain consolidated regression testing

The permanent regression workflow is:

`.github/workflows/test-regression.yml`

It covers existing golf monitoring and the Floorball automated test suite.

As of 22 October 2026, 105 Floorball tests and the existing golf regression tests passed.

New automated tests should normally be added to the existing test suite.

Before adding a test, confirm that the regression workflow will discover it.

Historical standalone test-workflows may be removed after verifying that they are no longer required.

Preserve useful Python test cases even when removing redundant GitHub Actions workflows.

## 10. Do not change architectural direction silently

If new information suggests that the agreed plan should change:

1. Explain the new evidence.
2. Explain why it affects the current plan.
3. Propose the change.
4. Agree on the new direction before implementation.

Do not introduce a new architecture or development strategy without making the change explicit.

Prefer the smallest change consistent with the agreed architecture.

Avoid introducing infrastructure merely to address hypothetical future requirements.

## 11. Design before architectural implementation

For architectural refactorings:

1. Complete the design phase.
2. Record the proposed design.
3. Review and agree on the design.
4. Begin implementation.
5. Verify the implementation against the agreed design.

Ordinary bug fixes and incremental improvements do not require a separate formal design phase.

Do not continue debating an already agreed design unless new evidence reveals a material issue.

## 12. Separate debugging from production design

Temporary debug code is allowed when investigating an unknown source.

Once behavior is understood:

- Remove temporary debugging code.
- Restore a clean production implementation.
- Verify relevant functionality.

Do not leave temporary test mechanisms in production accidentally.

Do not retain unnecessary standalone test-workflows indefinitely.

## 13. Protect working live systems

During an active event or important operational acceptance test:

- Prioritize stability.
- Avoid refactoring.
- Avoid cosmetic production changes.
- Avoid deleting active state.
- Fix only issues that materially affect monitoring.
- Preserve useful diagnostics.

Use the event as an acceptance test.

Refactoring, cleanup and generalization should normally happen afterwards.

Documentation may be updated during active monitoring when it does not affect execution.

## 14. Separate technical verification from operational acceptance

Use explicit verification categories.

### Implemented

The functionality exists in the repository.

### Automated-test verified

The functionality passed controlled tests.

### Workflow verified

The relevant GitHub Actions workflow executed successfully.

### Operationally verified

The functionality was observed working with real external data.

### Accepted

The agreed acceptance criteria have been met.

Do not describe a feature as fully accepted merely because its code exists or automated tests passed.

Record known limitations and unverified scenarios.

## 15. Record new knowledge

At the end of a meaningful development session, determine:

- Did the architecture change?
- Was a new design decision made?
- Did we learn something important about a connector?
- Did we identify future work?
- Did our development process change?
- Did the production or release status change?

Update the relevant documents:

- `docs/ARCHITECTURE.md` – current architecture.
- `docs/decisions.md` – architectural and operational decisions.
- `docs/ways-of-working.md` – development process.
- `docs/backlog.md` – outstanding work.
- Relevant design documents – detailed findings.
- `README.md` – project overview.
- `PROJECT_CONTEXT.md` – current status and handover.

Documentation must reflect verified facts rather than assumptions.

## 16. Keep documentation current

`docs/ARCHITECTURE.md` describes the current system.

Do not preserve obsolete architecture there merely for historical completeness.

Historical reasoning belongs in `docs/decisions.md`.

Design documents may retain original assumptions when clearly distinguished from the implemented solution.

Git history and releases provide detailed implementation history.

Avoid duplicating large amounts of technical detail across documents.

## 17. Manage ChatGPT conversation lifecycle

ChatGPT conversations have finite context.

Development must not depend on an earlier conversation remaining available.

### When to start a new conversation

As a general rule:

- Start a new conversation when beginning a new version.
- A version may span multiple conversations.
- Start a new conversation when the current one becomes long or difficult to navigate.
- Prefer switching after a completed checkpoint.
- Do not interrupt an active test solely to change conversations.

A new conversation does not imply a new software release.

### Starting a new conversation

The user should only need to say:

"Nu fortsätter vi med Event Platform."

The assistant should then:

1. Request current project context if unavailable.
2. Read the referenced repository documentation.
3. Identify current release and development status.
4. Confirm the session goal.
5. Request only source files relevant to that goal.
6. Continue without recreating completed work.

Do not assume direct access to the latest GitHub repository.

### Continuity between conversations

`PROJECT_CONTEXT.md` is the primary handover document.

It should contain:

- Current published release.
- Deployed functionality.
- Latest verified results.
- Important unresolved issues.
- Relevant documentation.
- Recommended next goal.

Detailed architecture and backlog information belong in their respective documents.

## 18. End every session with a checkpoint

The user can initiate closure by saying:

"Vi avslutar för idag."

The assistant should:

1. Summarize completed work.
2. Identify verified functionality.
3. Identify unresolved risks.
4. Determine required documentation updates.
5. Provide complete documentation changes.
6. Confirm that the user committed the changes.
7. Verify that `PROJECT_CONTEXT.md` reflects the current status.
8. Identify the next recommended development goal.

A session is not fully documented until required repository updates have been committed or explicitly recorded as pending.

The next session should be able to restart from repository documentation without relying on conversation history.

## 19. Release deliberately

Create a release when a meaningful, verified capability has been completed.

A release should describe what is actually working.

Use semantic versioning:

- Patch – compatible fixes.
- Minor – new backward-compatible capability.
- Major – incompatible architectural changes.

A new ChatGPT conversation does not require a new release.

Do not infer the published release version solely from deployed code.

Confirm release status from repository releases or tags.

## Core working principles

**One agreed goal.**

**One coherent implementation increment.**

**One appropriate verification.**

**Then the next increment.**

Deliver actual work rather than repeatedly promising future work.

Prefer complete files, evidence-based decisions and a clean handover.
