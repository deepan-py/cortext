# Agent Rules — Cortex Decision Tracking

Agents operating on this project MUST follow these rules.

## Before Starting Work

1. Read the current domain state: `cortex show <domain>` (when available)
2. Or check existing decisions: `ls .cortex/timeline/ | grep <domain>`

## When Making Changes

3. Write a decision record for every architectural or structural change.
   - Use `cortex new --domain <domain>` to generate a skeleton.
   - Fill ALL fields. You have no excuse for empty `assumptions`.
4. Include the decision YAML in the same commit as the code change.
5. Validate before committing: `cortex validate`
6. Never edit generated files: `.cortex/current/*.md`, `.cortex/tensions/*.md`, `.cortex/graph.json`, `.cortex/context-graph.html`
7. Declare which skill you loaded (if any) so the human can verify or redirect.

## When to Write a Decision Record

**Needed for:**
- New technology choices (database, framework, library for a new purpose)
- New or changed patterns (how auth works, API structure, data flow)
- Cross-domain changes (one domain's change affects another)
- New domains or domain splits
- Anything that changes the answer to "how does X work?"

**NOT needed for:**
- Bug fixes (unless the approach changes)
- Refactoring (unless system boundaries change)
- Style changes, dependency bumps, test additions
- Feature work that follows an established pattern

**Heuristic:** Would a new developer ask "why is it done this way?" If yes → write a record.

## Decision Record Quality

- `decision` must be concrete and specific (not vague or aspirational)
- `context` must explain the problem, not just the solution
- `assumptions` must be stated — extract them from your reasoning
- `alternatives_rejected` should list what was considered for non-trivial decisions
- `tensions` should flag anything this makes unstable
- `parents` should link to causally relevant prior decisions
