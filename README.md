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

# Initialize with AI platform support (copilot, claude, or both)
cortex init --ai copilot
cortex init --ai copilot,claude

# Create your first decision
cortex new --domain auth

# View decisions for a domain
cortex show auth

# Project status dashboard
cortex status

# Supersede an existing decision
cortex supersede 2025-04-25-001

# Validate all records
cortex validate

# Install git pre-commit hook
cortex hook install

# Manage skills
cortex skill list
cortex skill add my-skill .cortex/skills/my-skill.md -d "Custom skill"

# Export JSON Schema
cortex schema
```

## What `cortex init` creates

```
your-project/
├── .cortex/
│   ├── timeline/           ← decision YAML files (source of truth)
│   ├── current/            ← generated domain views (later phases)
│   ├── skills/             ← loadable AI skill files
│   │   ├── _index.md       ← skill summary index
│   │   ├── reviewer.md     ← system skill: PR review
│   │   └── context-owner.md← system skill: drift triage
│   ├── skills.json         ← machine-readable skill registry
│   ├── agent-rules.md      ← how AI agents use this system
│   ├── review-config.yaml  ← per-domain review requirements
│   ├── drift-config.yaml   ← path-based decision triggering
│   └── drift-register.jsonl
│
├── .github/
│   └── copilot-instructions.md  ← (if --ai copilot)
└── CLAUDE.md                    ← (if --ai claude)
```

## AI Platform Support

Cortex generates AI-specific instruction files so your AI assistant understands the context system:

| Platform | Flag | Generated File |
|---|---|---|
| GitHub Copilot | `--ai copilot` | `.github/copilot-instructions.md` |
| Claude | `--ai claude` | `CLAUDE.md` |

Use `--ai copilot,claude` to generate files for multiple platforms at once.

## CLI Commands

| Command | Description |
|---|---|
| `cortex init [--ai <platforms>]` | Scaffold `.cortex/` directory, optionally with AI platform files |
| `cortex new --domain <domain>` | Generate a skeleton decision YAML with auto-incremented date ID |
| `cortex new --domain <d> --parent <id>` | Create a child decision linked to a parent |
| `cortex show <domain>` | Show active decisions for a domain (`--all` includes superseded) |
| `cortex status` | Dashboard: decision counts, domains, unreviewed AI decisions |
| `cortex supersede <id>` | Mark a decision as superseded and create a child |
| `cortex validate` | 3-pass validation: schema → cross-references → cycle detection |
| `cortex hook install` | Install git pre-commit hook for automatic validation |
| `cortex hook uninstall` | Remove the Cortex pre-commit hook |
| `cortex skill add <name> <path>` | Register a skill in `skills.json` |
| `cortex skill list` | List registered skills |
| `cortex schema` | Export JSON Schema to stdout |
| `cortex version` | Show version |

## Skills Registry

Skills are documented in `.cortex/skills/` and indexed in `.cortex/skills.json`:

```json
{
  "skills": [
    {
      "name": "reviewer",
      "path": ".cortex/skills/reviewer.md",
      "description": "PR review criteria for decision records and context quality"
    }
  ]
}
```

AI agents read `skills.json` to discover available skills and their file paths. Use `cortex skill add` to register new skills.

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

## v0.2 Status

Trial-ready build. Current scope:
- `.cortex/` hidden directory structure + templates + system skills
- Pydantic models with full schema validation
- 3-pass validator (schema → cross-refs → cycles)
- AI platform support: `--ai copilot`, `--ai claude`, `--ai copilot,claude`
- Machine-readable `skills.json` registry with `cortex skill add/list`
- CLI: `init`, `new`, `show`, `status`, `supersede`, `validate`, `hook install/uninstall`, `skill add/list`, `schema`, `version`

See [DESIGN.md](DESIGN.md) for the full design record (problem space, architecture decisions, conflicts, implementation plan, and build phases).
