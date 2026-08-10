# Event Platform – Ways of Working

This document defines how development sessions for Event Platform should be conducted.

The purpose is to keep development predictable, understandable and easy to resume across sessions.

## 1. Start every session by restoring context

Before proposing changes:

1. Read `docs/architecture.md`.
2. Read `docs/decisions.md`.
3. Read `docs/ways-of-working.md`.
4. Read `docs/backlog.md` when it exists.
5. Identify the current production release.
6. Read only the source files relevant to the session's goal.

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

- inspect the real page,
- inspect logs,
- inspect state,
- use temporary debug output when necessary.

Do not guess HTML structure, selectors, API behavior or data formats when they can be observed.

The SGF Ranking and GolfBox implementations demonstrated the value of this approach.

## 5. Prefer complete files for substantial code changes

When a file requires significant modification, provide the complete intended file rather than a sequence of small edits.

Small, unambiguous changes may be described as individual line changes.

This reduces ambiguity about:

- what should remain,
- what should be removed,
- indentation,
- old debug code,
- obsolete imports.

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

## 8. Separate debugging from production design

Temporary debug code is allowed when investigating an unknown source.

Once the behavior is understood:

- remove debug code,
- restore a clean production implementation,
- verify the production implementation.

Do not leave a debug implementation in place accidentally.

## 9. Protect working live systems

During an active event:

- prioritize stability,
- avoid refactoring,
- avoid cosmetic changes,
- fix only issues that materially affect monitoring.

Use the live event as an acceptance test.

Refactoring and generalization should normally happen after the event.

## 10. Record new knowledge

At the end of a meaningful development session, ask:

- Did the architecture change?
- Was a new design decision made?
- Did we learn something important about a connector?
- Did we identify future work?
- Did our development process change?

Update the appropriate document when necessary:

- `architecture.md` – how the system works now
- `decisions.md` – important decisions and why
- `ways-of-working.md` – how development should be conducted
- `backlog.md` – future work

## 11. Keep documentation current rather than historical

`architecture.md` describes the current system.

Do not preserve obsolete architecture there merely for historical completeness.

Important historical reasoning belongs in `decisions.md`.

Git history and releases provide detailed implementation history.

## 12. End every session with a checkpoint

Before ending a development session, summarize:

1. What was completed.
2. What was verified.
3. What remains unresolved.
4. Whether documentation needs updating.
5. The recommended next goal.

The next session should be able to restart from repository documentation without requiring the previous conversation history.

## 13. Release deliberately

Create a release when a meaningful, verified capability has been completed.

A release should describe what is actually working, not what is merely planned.

Use semantic versioning:

- patch – fixes without meaningful capability changes
- minor – new backward-compatible capability
- major – significant incompatible architectural change

## Core working principle

One goal.

One step.

One verification.

Then the next step.
