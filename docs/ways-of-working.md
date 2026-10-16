# Event Platform – Ways of Working

This document defines how development sessions for Event Platform should be conducted.

The purpose is to keep development predictable, understandable and easy to resume across sessions and ChatGPT conversations.

The repository is the source of truth. ChatGPT conversations are working environments, not the project's long-term memory.

## 1. Start every session by restoring context

Before proposing changes:

1. Read `PROJECT_CONTEXT.md` first.
2. Read `README.md`.
3. Read `docs/ARCHITECTURE.md`.
4. Read `docs/decisions.md`.
5. Read `docs/ways-of-working.md`.
6. Read `docs/backlog.md`.
7. Identify the current production release and ongoing development.
8. Read only the source files relevant to the session's goal.

Do not rely on conversational memory when repository documentation is available.

The repository is the source of truth.

## 2. Define one goal for the session

Every development session starts with a clear goal.

Example:

> Make the GolfBox connector reusable for the next competition.

Avoid expanding the session into unrelated architecture or feature work unless a discovered issue blocks the agreed goal.

New ideas should normally be added to the backlog rather than implemented immediately.

## 3. Work one step at a time

Development should follow this cycle:

1. Make one understandable change.
2. Run or test it.
3. Observe the result.
4. Draw a conclusion.
5. Only then make the next change.

Avoid changing multiple independent things before verification.

## 4. Prefer evidence over assumptions

When an external source behaves unexpectedly:

- Inspect the real page.
- Inspect logs.
- Inspect state.
- Use temporary debug output when necessary.

Do not guess HTML structure, selectors, API behavior or data formats when they can be observed.

The SGF Ranking, GolfBox and iBIS implementations demonstrated the value of this approach.

## 5. Prefer complete files for substantial code changes

When a file requires significant modification, provide the complete intended file rather than a sequence of small edits.

Small, unambiguous changes may be described as individual line changes.

This reduces ambiguity about:

- What should remain.
- What should be removed.
- Indentation.
- Old debug code.
- Obsolete imports.

When providing a complete replacement file, the entire file must be provided in one continuous copyable block.

Do not use nested code blocks or formatting that accidentally splits the file into multiple sections.

The user should be able to replace the existing file with one copy-and-paste operation.

## 6. Do not repeat completed steps

Before asking for a change, establish what has already been completed.

Do not instruct the user to recreate files, imports, configuration or infrastructure that already exists unless there is a deliberate reason to replace it.

If uncertain, inspect the current file before proposing a change.

## 7. Do not change direction silently

If new information suggests that the agreed plan should change:

1. Explain what new information was discovered.
2. Explain why it affects the current plan.
3. Propose the change of direction.
4. Agree on the new direction before implementing it.

Do not introduce a new architecture or development strategy in the middle of an existing step without making the change explicit.

## 8. Design before implementation

For architectural refactorings:

1. Complete the design phase first.
2. Record the proposed design in a design draft.
3. Review and agree on the design.
4. Only then begin implementation.

Avoid partially implementing an architectural idea while the design is still evolving.

If implementation has started before the design is stable, restore the project to a consistent working state before continuing.

This rule applies to architectural refactorings only.

Ordinary bug fixes and small incremental improvements should continue to follow the normal one-step development process.

## 9. Separate debugging from production design

Temporary debug code is allowed when investigating an unknown source.

Once the behavior is understood:

- Remove debug code.
- Restore a clean production implementation.
- Verify the production implementation.

Do not leave a debug implementation in place accidentally.

## 10. Protect working live systems

During an active event:

- Prioritize stability.
- Avoid refactoring.
- Avoid cosmetic changes.
- Fix only issues that materially affect monitoring.

Use the live event as an acceptance test.

Refactoring and generalization should normally happen after the event.

## 11. Record new knowledge

At the end of a meaningful development session, ask:

- Did the architecture change?
- Was a new design decision made?
- Did we learn something important about a connector?
- Did we identify future work?
- Did our development process change?

Update the appropriate document when necessary:

- `ARCHITECTURE.md` – how the system works now.
- `decisions.md` – important decisions and why.
- `ways-of-working.md` – how development should be conducted.
- `backlog.md` – future work.
- Relevant design documents – implementation findings and unresolved design questions.
- `PROJECT_CONTEXT.md` – current development status and next steps.

Documentation should reflect verified facts, not assumptions or intended behavior.

## 12. Keep documentation current rather than historical

`ARCHITECTURE.md` describes the current system.

Do not preserve obsolete architecture there merely for historical completeness.

Important historical reasoning belongs in `decisions.md`.

Git history and releases provide detailed implementation history.

## 13. Manage ChatGPT conversation lifecycle

ChatGPT conversations have finite context and may eventually reach their maximum length.

Development must not depend on the availability of an earlier conversation.

### When to start a new conversation

As a general rule:

- Start a new conversation when beginning development of a new version.
- A version may span multiple conversations when development is extensive.
- Start a new conversation earlier when the current one becomes long or difficult to navigate.
- Prefer switching between development phases or after a completed session checkpoint.
- Do not interrupt an active test or unfinished implementation solely to change conversations.

A new conversation does not imply a new software release.

A software release is created only when the relevant capability has been implemented and verified.

### Starting a new conversation

The user should only need to say:

"Nu fortsätter vi med Event Platform."

The assistant should then:

1. Request the current `PROJECT_CONTEXT.md` if it is not available.
2. Read the referenced project documentation.
3. Identify the current production release and development status.
4. Confirm the intended goal for the session.
5. Request only additional source files needed for that goal.
6. Continue from the documented project state without recreating completed work.

Do not assume that the assistant can access previous conversations or the latest GitHub repository contents.

If direct repository access is unavailable, request the necessary files from the user.

### Continuity between conversations

`PROJECT_CONTEXT.md` is the primary handover document.

It should contain sufficient information to identify:

- Current production release.
- Ongoing development.
- Latest verified results.
- Important unresolved issues.
- Relevant documentation.
- Recommended next development goal.

Detailed technical information belongs in the appropriate architecture, design or backlog documents rather than being duplicated unnecessarily.

## 14. End every session with a checkpoint

The user can initiate session closure by saying:

"Vi avslutar för idag."

The assistant should:

1. Summarize what was completed.
2. Identify what was actually verified.
3. Identify unresolved issues and risks.
4. Determine which project documents require updates.
5. Provide the required documentation changes, one file at a time.
6. Ask the user to confirm that changes have been committed.
7. Verify that `PROJECT_CONTEXT.md` reflects the current project status.
8. Identify the recommended next development goal.

A session should not be considered fully documented until the relevant repository changes have been committed or explicitly identified as pending.

The next session should be able to restart from repository documentation without requiring previous conversation history.

## 15. Release deliberately

Create a release when a meaningful, verified capability has been completed.

A release should describe what is actually working, not what is merely planned.

Use semantic versioning:

- Patch – fixes without meaningful capability changes.
- Minor – new backward-compatible capability.
- Major – significant incompatible architectural change.

A new ChatGPT conversation does not require a new release.

## Core working principle

One goal.

One step.

One verification.

Then the next step.
