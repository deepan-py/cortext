# Cortex Decision Tracking

This project uses **Cortex** for context-aware decision tracking.

## Context System

- Decision records live in `.cortex/timeline/` as YAML files.
- Current domain state lives in `.cortex/current/`.
- Skills are registered in `.cortex/skills.json` and documented in `.cortex/skills/`.
- Agent rules are in `.cortex/agent-rules.md` — read and follow them.

## Before Making Changes

1. Check existing decisions: review `.cortex/timeline/` for the affected domain.
2. Read the skill index: `.cortex/skills.json` lists available skills with paths.
3. Load relevant skills from `.cortex/skills/` before specialized tasks (reviews, triage).

## When Making Architectural Changes

1. Create a decision record: `cortex new --domain <domain>`
2. Fill ALL fields — especially `assumptions` and `alternatives_rejected`.
3. Include the decision YAML in the same commit as the code change.
4. Validate before committing: `cortex validate`

## Decision Record Quality

- `decision` must be concrete and specific.
- `context` must explain the problem, not just the solution.
- `assumptions` must be stated explicitly.
- `alternatives_rejected` should list what was considered.
- `tensions` should flag anything this makes unstable.
