# Cortex

Context-aware decision tracking system. Track architectural decisions as a DAG, with file-based YAML storage and AI-assisted workflows.

Cortex solves the problem of **context loss** — when developers leave, when new members join, when AI agents need to understand *why* the system works the way it does, not just *what* it does.

## Why

- **Context loss during turnover** — decisions live in people's heads, not in the repo
- **Onboarding friction** — new developers ask "why is it done this way?" with no answer
- **AI agents work blind** — without decision history, agents repeat mistakes or contradict existing patterns
- **ADRs fail in practice** — too heavyweight, no enforcement, no graph structure

Cortex tracks decisions as a **DAG** (directed acyclic graph), not flat files. Every decision knows its parents, its children, its assumptions, and its tensions.

## Install

```bash
pip install -e .
```

## Quick Start

```bash
# Initialize in any project
cd your-project
cortex init

# Create your first decision
cortex new --domain auth

# Validate all records
cortex validate

# Export JSON Schema (generated from pydantic models)
cortex schema
```

## What `cortex init` creates

```
your-project/
└── context/
    ├── timeline/           ← decision YAML files (source of truth)
    ├── current/            ← generated domain views (later phases)
    ├── skills/             ← loadable AI skill files
    │   ├── _index.md       ← skill summary index
    │   ├── reviewer.md     ← system skill: PR review
    │   └── context-owner.md← system skill: drift triage
    ├── agent-rules.md      ← how AI agents use this system
    ├── review-config.yaml  ← per-domain review requirements
    ├── drift-config.yaml   ← path-based decision triggering
    └── drift-register.jsonl
```

## CLI Commands

| Command | Description |
|---|---|
| `cortex init` | Scaffold `context/` directory in any project |
| `cortex new --domain <domain>` | Generate a skeleton decision YAML with auto-incremented date ID |
| `cortex new --domain <domain> --parent <id>` | Create a child decision linked to a parent |
| `cortex validate` | 3-pass validation: schema → cross-references → cycle detection |
| `cortex schema` | Export JSON Schema to stdout (generated from pydantic models) |
| `cortex version` | Show version |

## Decision Record Format

```yaml
id: "2025-04-25-001"
status: active
date: "2025-04-25"
author: human
domains:
  - auth
decision: >
  Use JWT with RS256 for API auth.
context: >
  Need stateless auth across multiple service instances.
parents: []
assumptions:
  - "Tokens are stateless, no server-side revocation needed"
alternatives_rejected:
  - option: "Session-based auth"
    reason: "Doesn't scale horizontally without sticky sessions"
tensions:
  - "No token revocation means compromised tokens live until expiry"
tags: [jwt, security, auth]
```

**Required fields:** `id`, `status`, `date`, `author`, `domains`, `decision`, `context`
**Recommended fields:** `parents`, `assumptions`, `alternatives_rejected`, `tensions`, `resolves`, `tags`
**Optional:** `reviewed_by`

## Tech Stack

- **[Pydantic v2](https://docs.pydantic.dev/)** — typed models with validation
- **[Typer](https://typer.tiangolo.com/)** — CLI with rich help and auto-completion
- **[PyYAML](https://pyyaml.org/)** — YAML parsing
- **[Rich](https://rich.readthedocs.io/)** — terminal output formatting

## v0.1 Status

This is the minimal viable build. Current scope:
- Folder scaffolding + templates + system skills
- Pydantic models with full schema validation
- 3-pass validator (schema → cross-refs → cycles)
- CLI: `init`, `new`, `validate`, `schema`, `version`

See [DESIGN.md](DESIGN.md) for the full design record (problem space, architecture decisions, conflicts, implementation plan, and build phases).
