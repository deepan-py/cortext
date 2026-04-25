# Context System Design — Full Design Record

> Complete design record of the context-aware development documentation system.
> Covers the problem space, all design decisions made, conflicts encountered, resolutions reached, and the final architecture.
> Intended as a starting point for implementation in a new session.

---

## Table of Contents

1. [Problem Space](#1-problem-space)
2. [What We Rejected and Why](#2-what-we-rejected-and-why)
3. [Core Principles We Landed On](#3-core-principles-we-landed-on)
4. [Design Decisions — In Order](#4-design-decisions--in-order)
5. [Conflicts Encountered](#5-conflicts-encountered)
6. [The Final Architecture](#6-the-final-architecture)
7. [Schema Definitions](#7-schema-definitions)
8. [Graph Structure and Correlations](#8-graph-structure-and-correlations)
9. [Enforcement Layer](#9-enforcement-layer)
10. [Greenfield vs Brownfield Analysis](#10-greenfield-vs-brownfield-analysis)
11. [Known Unresolved Problems](#11-known-unresolved-problems)
12. [What to Build First](#12-what-to-build-first)

---

## 1. Problem Space

### Starting Point: Spec-Driven Development

The original question was whether spec-driven development (SDD) is viable when specs change or get extended.

**The brutal answer**: SDD works for greenfield stable domains. It breaks the moment reality diverges from the spec — which happens constantly in real projects. The core failure: reality changes faster than specs do.

Specific SDD failure modes identified:
- Spec rot — code changes, spec doesn't, they diverge silently
- Over-specification — specs become pseudo-code, defeating the purpose
- Non-determinism — same spec generates different code across runs
- Brownfield blindness — SDD tools are optimized for greenfield, legacy codebases break the workflow
- The TDD parallel — TDD was formalized in 2003, adoption is still under 20% despite proven benefits. SDD faces identical adoption barriers.

### The Shift: On-the-Fly Development with Context

Rather than spec-first, the idea evolved toward: **maintain context as you build**, not before you build.

Two artifacts proposed:
- A **timeline** of what changed and why
- A **current state** of what the system does right now

This separates two fundamentally different reader needs:
- "How does auth work today?" → current state
- "Why does auth work this way?" → timeline

---

## 2. What We Rejected and Why

### Rejected: Feature-based folder organization

**What it was**: A folder per feature, containing that feature's spec and timeline.

**Why rejected**: Features are a lie as an organizational unit. Features don't exist in isolation:
- Feature B silently depends on a decision made in Feature A
- Feature C refactors something Feature A established, breaking Feature B's assumption
- Feature D is Feature A extended but filed as new work

Feature-based folders create false isolation. The links between features are where all the real knowledge lives, and those links get lost entirely in a feature-based structure.

### Rejected: Time-based compression

**What it was**: Compress timeline entries older than N months into a glacier summary.

**Why rejected**:
- A 2-year-old decision can still be fully relevant today
- Compression requires judging what's "load-bearing" — but assumptions are invisible to the person making them
- Bad compression is irreversible — the nuance is gone permanently
- The person compressing doesn't know what future developers will need from that history

### Rejected: Separate glacier summary files

**What it was**: Glacier entries as prose summaries of compressed decisions, with links back to active decisions.

**Why rejected**:
- Glacier links rot — a current state file references G-001, G-001 references D-023, D-023 gets superseded and renamed — three-hop chain with rot risk at every link
- Summaries lose the alternatives considered, which is the most valuable part of any decision record
- Creates two sources of truth (summary + original) that can contradict each other
- One human making a compression judgment call is a single point of knowledge loss

### Rejected: Strict tree structure for decisions

**What it was**: Decisions organized as a tree where children supersede parents.

**Why rejected**:
- Decisions in reality form graphs, not trees. D-031 can be caused by both D-019 and D-027 converging — two parents, not one.
- Forcing a single parent loses real causality
- Leaf identification requires traversal — you can't glance at a tree and know which nodes are current
- Multi-domain decisions don't have a natural home in a domain-organized tree

---

## 3. Core Principles We Landed On

These are non-negotiable. Every design decision below must be consistent with these.

### Principle 1: Code is the ground truth. Always.

Everything else — docs, specs, timelines, decision records — are **derived artifacts**. They exist to help humans and AI understand the code. They never compete with the code. When code and docs conflict, code wins and docs get updated.

### Principle 2: Human is the weakest link

AI making code changes can be forced to update context atomically. Humans cannot be forced — only nudged. Design the system assuming humans will drift, and build a **detection and recovery mechanism**, not a prevention mechanism.

Consequences:
- Don't try to prevent drift — make drift visible
- Don't punish drift — log it publicly
- Don't require perfect documentation — require minimum viable documentation with an escape hatch

### Principle 3: Nothing is ever deleted

History is append-only. Decisions are never removed or compressed out of existence. A superseded decision gets a child — it doesn't get deleted. Future developers (and AI agents) need to understand why things are the way they are. That requires the full lineage, not a summary.

### Principle 4: Structure encodes meaning, not just metadata

Supersession is structural (parent-child relationship in the graph), not just a field (`superseded-by: D-031`). Status is queryable, not inferred. Domain membership is explicit. These things must be in the structure, not in prose.

### Principle 5: Two audiences, two artifacts

- **Current state** — for anyone implementing right now. Must be accurate, minimal, no history.
- **Timeline/graph** — for anyone planning, debugging decisions, or understanding why. Must be honest, complete, traversable.

These two artifacts serve different readers with different questions. They must never be merged into one.

### Principle 6: Sequence number is the universal time axis

All decisions get a monotonically increasing sequence number. This is the time axis. It is never reused. It allows ordering without timestamps, point-in-time queries without date parsing, and correlation across domains without any central coordination beyond the sequence itself.

---

## 4. Design Decisions — In Order

These are the decisions made during this design session, recorded in the same format the system itself will use.

---

**DESIGN-001**
Decision: Organize context by domain concept, not by feature
Context: Feature-based organization creates false isolation. Features link to each other in ways that break any folder structure built around them.
Alternatives rejected: Feature folders, chronological flat files, per-PR documentation
Assumptions made: Domains are more stable than features over time
Tensions introduced: Domain boundaries are themselves unstable — domains split and merge as systems grow

---

**DESIGN-002**
Decision: Separate current state from timeline as two distinct artifacts
Context: These serve different readers with different questions. Merging them creates a document that serves neither well.
Alternatives rejected: Single living document per domain, wiki-style pages
Assumptions made: The team will maintain both artifacts separately
Tensions introduced: Two artifacts can diverge from each other and from the code — three-way sync problem

---

**DESIGN-003**
Decision: Code is ground truth. Docs are derived.
Context: Both humans and AI change code. Docs always lag. Establishing a clear authority hierarchy prevents the question "which one is right?" from having multiple answers.
Alternatives rejected: Docs as source of truth, docs and code as co-equal
Assumptions made: Team accepts that stale docs are a normal state requiring detection, not prevention
Tensions introduced: None — this simplifies rather than complicates

---

**DESIGN-004**
Decision: Drift detection over drift prevention
Context: Human developers cannot be forced to update docs. Any system that tries to prevent drift will be circumvented under deadline pressure.
Alternatives rejected: Hard CI blocks with no escape hatch, mandatory doc updates before code merges
Assumptions made: Drift detection runs regularly and someone reviews its output
Tensions introduced: Drift can accumulate between detection runs. Detection cadence matters.

---

**DESIGN-005**
Decision: Escape hatch with public logging instead of hard block for humans
Context: Developers under deadline will `git commit --no-verify` to bypass hooks. Making the bypass public (drift register) is more effective than making it impossible.
Alternatives rejected: No escape hatch (too brittle), silent bypass (invisible), per-developer opt-out (defeats the purpose)
Assumptions made: The drift register is reviewed regularly by someone with authority to act on it
Tensions introduced: The drift register itself can become noise if not reviewed

---

**DESIGN-006**
Decision: AI commits must atomically include context updates — no escape hatch for AI
Context: AI agents can be programmatically forced to include context updates in the same commit. This is not possible for humans. Different rules for different actors.
Alternatives rejected: Same rules for AI and humans, AI-generated docs reviewed separately
Assumptions made: AI agent commits can be identified reliably (by metadata or commit flag)
Tensions introduced: How to identify AI commits reliably without false positives

---

**DESIGN-007**
Decision: Domain files are projections of the decision graph, not handwritten prose
Context: Handwritten domain files have merge conflicts, go stale, and diverge from the graph. If current state is derived from the graph (filtered by domain + active status), the graph is the single source of truth for documentation.
Alternatives rejected: Hand-maintained domain files, wiki pages, generated-then-human-edited files
Assumptions made: Tooling exists to generate/render domain views from the graph
Tensions introduced: Tooling must be built and maintained. Generated files feel less personal and developers may resist them.

---

**DESIGN-008**
Decision: Glacier is not a compression layer — it is the full decision graph, queryable
Context: Compression destroys history irreversibly. The glacier should be the complete DAG of all decisions ever made, with active/superseded status as a filter for current truth.
Alternatives rejected: Time-based compression, prose summary glacier entries, lossy archiving
Assumptions made: Storage is cheap. Full history is always preferable to compact history.
Tensions introduced: Graph grows indefinitely. Large graphs are slower to traverse and harder to visualize.

---

**DESIGN-009**
Decision: Use a DAG (directed acyclic graph) not a tree
Context: Decisions in reality have multiple causes. D-031 was caused by both D-019 (expiry policy) and D-027 (RBAC introduction) converging. A tree forces a single parent and loses real causality. A DAG is honest about how decisions actually happen.
Alternatives rejected: Strict tree (single parent), flat list with superseded-by fields, linked list
Assumptions made: Tooling can render and traverse a DAG. Developers understand the concept of multiple parents.
Tensions introduced: DAGs are harder to visualize than trees. Cycles are possible and must be prevented by tooling.

---

**DESIGN-010**
Decision: Monotonic sequence number as universal time axis
Context: Decisions need ordering without requiring timestamp parsing. The sequence number IS the time axis. Lower number = happened earlier. This is cheap to compute, impossible to get wrong, and works across all domains.
Alternatives rejected: Timestamps as ordering, git commit hash as ordering, manual date fields as ordering
Assumptions made: Sequence numbers are centrally assigned and never reused
Tensions introduced: Parallel development means two developers can try to claim the same sequence number simultaneously. Requires coordination mechanism.

---

**DESIGN-011**
Decision: Use date-prefixed sequence for distributed teams (20250914-001 format)
Context: A single `next-id.txt` file creates a merge conflict bottleneck. Date-prefixed sequences scope uniqueness to a day, allowing multiple decisions on different days to never conflict, and multiple decisions on the same day to use suffixes.
Alternatives rejected: Central counter file, UUID-based IDs (lose ordering), developer-assigned numbers (collision risk)
Assumptions made: Two developers rarely create decisions on exactly the same day with the same suffix
Tensions introduced: Lexicographic ordering works correctly only if date format is consistent. Must enforce YYYYMMDD format, not MM/DD/YYYY.

---

**DESIGN-012**
Decision: Inherited assumptions must be re-stated at the leaf node
Context: A leaf node (active decision) can inherit assumptions from 3+ levels of parent decisions. If the leaf is self-contained, a developer reading it doesn't need to traverse the full lineage to understand what it depends on. Re-stating inherited assumptions at the leaf makes the leaf independently readable while preserving the full lineage for archaeology.
Alternatives rejected: No assumption propagation (forces traversal), copy-paste from parents (creates sync problem), links only (same archaeology problem)
Assumptions made: Developers writing leaf nodes will faithfully re-state inherited assumptions
Tensions introduced: If a parent assumption changes, the re-statement in the leaf becomes stale. Requires a link integrity check for assumption re-statements, not just decision links.

---

## 5. Conflicts Encountered

These are genuine tensions in the design that were not fully resolved. They are recorded here so the implementation session can address them.

---

### CONFLICT-001: Domain boundaries are unstable

**The problem**: We said "organize by domain because domains are stable." This is partially false. `auth` splits into `auth`, `identity`, `sessions`, `permissions` as systems grow. Domain files created early become wrong domain files later. When a domain splits, all decision records referencing the old domain name need updating — creating a documentation migration problem identical to the feature-linking problem we were trying to solve.

**Partial resolution**: Let domains emerge from the system. Start with one file (`system.md`). Only split when a section is clearly its own concern. Never define domains before the system exists.

**Still unresolved**: Who has authority to split or merge domains? What happens to decision records referencing a domain that no longer exists as a single unit?

---

### CONFLICT-002: The "assumptions made" field will be left empty

**The problem**: Assumptions are invisible to the person making them. The developer writing a decision record doesn't know they're assuming the queue delivers within 30 seconds — that assumption only becomes visible when it breaks, months later. A field that requests assumptions will get: (a) obvious non-assumptions, (b) blank, or (c) retrospective fills after breakage.

**Partial resolution**: The schema requires the field. The PR review process should include a reviewer specifically asking "what are you assuming that you haven't written down?"

**Still unresolved**: No tooling can extract assumptions automatically. This is a human judgment problem. The field will be low quality regardless of enforcement.

---

### CONFLICT-003: Merge conflicts on domain files

**The problem**: Two developers touching the same domain simultaneously will produce a git merge conflict on the domain prose file. Unlike code, prose conflicts cannot be mechanically resolved. Under deadline pressure this gets resolved with "accept mine" and one person's context is permanently lost.

**Resolution reached**: Domain files should be generated from the graph (DESIGN-007), not handwritten. If current state is a rendered view of the decision graph filtered by domain and status, two developers can't conflict on the prose — they each write decision nodes (separate files with unique sequence IDs) and the domain view is re-rendered from both.

**Residual tension**: Tooling to render domain views must be built. Until it is built, domain files remain handwritten and subject to this conflict.

---

### CONFLICT-004: The drift detector produces noise

**The problem**: The detector flags domains where code changed but docs haven't. Most code changes are trivial — variable renames, log message changes, dependency bumps — and don't warrant domain file updates. The detector will fire constantly on trivial changes. Developers will start ignoring it within 2 weeks, exactly like all other noisy automated alerts.

**Partial resolution**: Per-domain configuration specifying which file paths are "significant" for that domain. Changes outside those paths don't trigger the detector.

**Still unresolved**: Who maintains the per-domain configuration? It becomes its own documentation artifact that can go stale.

---

### CONFLICT-005: The link integrity checker has false negatives

**The problem**: The link checker verifies that `D-023` resolves to a file. It cannot verify that the content of D-023 is still relevant to what's referencing it. A domain file can reference a superseded decision — the link resolves, the checker passes, the developer reads stale reasoning and makes decisions based on it.

**Partial resolution**: Status field on every decision. If a domain file references a decision with `status: superseded`, flag it as a stale reference (not a broken link, but a stale link).

**Still unresolved**: Stale reference detection requires parsing decision files to extract status, not just checking file existence. More complex tooling.

---

### CONFLICT-006: Schema drift over time

**The problem**: You define a decision record schema today. In 8 months a new developer writes records with different field names, different levels of detail, different interpretation of "assumptions made." The corpus becomes inconsistent. Running tooling or AI agents over inconsistent records produces garbage.

**Partial resolution**: JSON Schema or a linter for the YAML decision files. CI fails if a record doesn't match the schema.

**Still unresolved**: Schema itself needs to evolve over time. Existing records don't auto-migrate when schema changes. Need a schema version field and migration tooling.

---

### CONFLICT-007: Parallel sequence number assignment

**The problem**: Two developers creating decisions simultaneously can claim the same sequence number if using a central counter. Date-prefixed sequences (DESIGN-011) solve most of this, but two developers creating decisions on the same day with the same suffix still conflict.

**Resolution reached**: Date-prefixed with suffix: `20250914-001`, `20250914-002`. Merge conflict on the sequence itself becomes the coordination mechanism — whoever merges second must increment their suffix. This is visible and recoverable.

**Residual tension**: Requires discipline. Developers must check for conflicts and renumber before merging.

---

### CONFLICT-008: Authority vacuum during team turnover

**The problem**: The person who designed the domain structure and knows why `billing` and `payments` are separate domains leaves the company. New developers don't know the rationale. They start treating them as one domain. Decision records reference both inconsistently. The structure becomes incoherent because the mental model that justified it left with one person.

**Partial resolution**: The decision records themselves should capture the rationale for domain separation. DESIGN-001 (organize by domain) should have a corresponding decision record in the actual system.

**Still unresolved**: If nobody reads the old decision records, the rationale is still effectively lost. Reading the graph requires knowing the graph exists and how to navigate it. Onboarding documentation must cover this explicitly.

---

### CONFLICT-009: The context owner problem

**The problem**: This system requires a context owner — someone whose actual job includes reviewing the drift register weekly, approving domain splits, enforcing schema consistency, and ensuring the graph stays navigable. If that role isn't explicitly assigned with protected time, the system degrades at the rate of team busyness.

**Partial resolution**: Name a context owner explicitly. Rotate it quarterly to prevent single-person dependency.

**Still unresolved**: In small teams, nobody has spare capacity for this role. In large teams, coordination across context owners for shared domains is a new problem.

---

### CONFLICT-010: Brownfield retroactive decision reconstruction

**The problem**: For existing codebases, the historical decisions that shaped the current state are not recoverable. The original developers may be gone. The original context is gone. Reconstructing decisions from git history gives you the *what* but not the *why*. Retroactive decision records are rationalized history — the author knows what was chosen and writes a record that makes it look obviously correct.

**Partial resolution**: Don't try to document the whole brownfield system at once. Pick the highest-churn domain. Write decision records only for new decisions going forward. Let the glacier start empty. Document old territory only when someone needs to change it.

**Still unresolved**: The most important decisions to understand are often the oldest ones — the foundational architectural choices that everything else is built on. These are exactly the ones that are hardest to reconstruct.

---

## 6. The Final Architecture

### Folder Structure

```
/context
  /timeline                     ← all decisions, flat, all time, all domains
    20240115-001.yaml            ← status: superseded
    20240203-001.yaml            ← status: superseded
    20240203-002.yaml            ← status: superseded
    20250914-001.yaml            ← status: active (leaf)
    20250914-002.yaml            ← status: active (leaf)

  /current                      ← domain views, generated from graph
    auth.md                     ← rendered from: domain=auth, status=active
    payments.md                 ← rendered from: domain=payments, status=active
    notifications.md

  /tensions
    active.md                   ← tensions from active nodes with no resolving child
    resolved.md                 ← tensions that have a resolving child in the graph

  graph.json                    ← machine-readable adjacency list, auto-generated by tooling
  drift-register.md             ← log of [skip-context] commits and detected drift
  compression-log.md            ← not used for compression; used for graph integrity audit log
  drift-config.yaml             ← per-domain path configuration for drift detector
```

### Data Flow

```
Developer writes code
       │
       ├── AI agent → must atomically commit decision YAML + code (no escape)
       │
       └── Human → pre-commit hook checks for /context touch
                        │
                        ├── /context touched → passes
                        │
                        └── [skip-context] in message → logs to drift-register, passes
                                                              │
                                                              └── CI validates log entry exists

Tooling runs (on every PR):
  1. Link integrity check → all D-IDs in all files resolve to existing YAML nodes
  2. Stale reference check → domain files referencing status:superseded nodes are flagged
  3. Schema validation → all YAML nodes match current schema
  4. Graph cycle detection → DAG must remain acyclic
  5. Render current state → /current/*.md regenerated from graph

Tooling runs (weekly):
  6. Drift detector → flags domains where code path changed but no new decision was written
  7. Orphaned tension report → tensions with no resolving child decision
  8. Domain coupling report → decisions touching multiple domains (integration risk signals)
```

### Reading the System

| Question | How to answer |
|---|---|
| What does auth do right now? | Read `/current/auth.md` |
| Why does auth work this way? | Read active leaf nodes for auth domain, traverse parents |
| What did auth look like in Aug 2024? | Filter timeline by `domain: auth` + `sequence <= [last seq before Aug 2024]` |
| What's unstable right now? | Read `/tensions/active.md` |
| What decisions caused the most downstream changes? | Find nodes with the most children in `graph.json` |
| Where are the riskiest assumptions? | Find active leaf nodes with the deepest inherited assumption chains |
| What changed in the last sprint? | Filter timeline by sequence range for that sprint period |

---

## 7. Schema Definitions

### Decision Node (YAML)

```yaml
# File: /context/timeline/YYYYMMDD-NNN.yaml
# Filename IS the sequence ID. Lexicographic order = chronological order.

id: 20250914-001              # matches filename exactly
status: active                # active | superseded
date: 2025-09-14              # human-readable, not used for ordering
author: human | ai            # used to verify enforcement rules
domains:                      # list, can be multiple
  - auth
  - payments
parents:                      # list of IDs this decision causally follows from
  - 20240203-001
  - 20240812-002
children:                     # filled when this node is superseded
  - 20251103-001
decision: >
  One paragraph. What was decided. Concrete and specific.
context: >
  One paragraph. Why this decision was needed. What situation forced it.
alternatives_rejected:
  - option: Session-based auth
    reason: Doesn't scale horizontally without sticky sessions
  - option: OAuth only
    reason: Too heavy for internal service-to-service calls
assumptions:
  inherited:                  # re-stated from parent nodes, still load-bearing
    - source: 20240115-001
      assumption: Tokens are stateless, no server-side revocation
    - source: 20240812-002
      assumption: Roles are assigned at login, not per-request
  new:                        # introduced by this decision
    - Role assignments do not change mid-session
    - Mobile clients can handle variable expiry by role
tensions_introduced:
  - Session length now varies by role. Mobile clients must handle expiry differently per role type.
  - Service accounts with 30-day expiry are a long-lived credential risk if keys are compromised.
resolves_tension: >           # optional — tension from a parent node this decision resolves
  Resolves: "Single global expiry can't serve both admin security requirements and service account usability"
  from: 20240812-002
```

### Domain File (Generated Markdown)

```markdown
# Auth — current state
> Generated from graph. Do not edit directly. Last rendered: 2025-09-14.
> Source: decisions with domain=auth, status=active

## What auth does right now

[Rendered from decision bodies of active leaf nodes]

## Active decisions

| ID | Date | Decision summary |
|----|------|-----------------|
| 20250914-001 | 2025-09-14 | Per-role JWT expiry |
| 20250831-002 | 2025-08-31 | Refresh token rotation policy |

## Active tensions

[Rendered from tensions_introduced fields of active nodes with no resolving child]

- Session length varies by role. Mobile clients must handle expiry differently per role type.
- Service accounts with 30-day expiry are long-lived credential risk if compromised.

## Inherited assumptions (still load-bearing)

These assumptions were made in earlier decisions and are still depended on by active decisions.
If any of these become false, the active decisions above may need to be revisited.

- Tokens are stateless, no server-side revocation (from 20240115-001)
- Roles are assigned at login, not per-request (from 20240812-002)
```

### Drift Config (YAML)

```yaml
# /context/drift-config.yaml

domains:
  auth:
    tracks:
      - src/auth/**
      - lib/jwt/**
      - middleware/auth*
    stale_after_days: 14
    owner: platform-team

  payments:
    tracks:
      - src/payments/**
      - services/billing/**
    stale_after_days: 7
    owner: payments-team

  notifications:
    tracks:
      - src/notifications/**
      - workers/notification*
    stale_after_days: 21
    owner: platform-team
```

---

## 8. Graph Structure and Correlations

### The DAG

Every decision node is a vertex. Every parent-child relationship is a directed edge pointing from parent to child (causality flows forward in time). The graph is acyclic by definition — a decision cannot be its own ancestor.

```
Time axis (sequence order):
20240115-001 → 20240203-001 → 20240203-002 → 20240812-001 → 20240812-002 → 20250914-001
     │                │                               │                          ↑
     │                └──────────────────────────────┘                          │
     │                                                                           │
     └───────────────────────────────────────────────────────────────────────────┘

(20250914-001 has two parents: 20240812-002 and 20240115-001)
```

### Useful Graph Queries

**Query 1: Current state of a domain**
```
filter nodes where:
  domain contains "auth"
  AND status == "active"
→ returns all leaf nodes for auth = current truth
```

**Query 2: Full causal history of a decision**
```
starting from node X
traverse parents recursively
→ returns full ancestral chain = why X exists
```

**Query 3: Point-in-time snapshot**
```
filter nodes where:
  domain contains "auth"
  AND id <= "20240901-000"  (lexicographic ceiling for the date)
  AND (status == "active" OR children all have id > "20240901-000")
→ returns what was active as of that date
```

**Query 4: Integration risk map**
```
filter nodes where:
  length(domains) > 1
→ returns all decisions touching multiple domains
  sorted by sequence = shows when coupling was introduced
```

**Query 5: Orphaned tensions**
```
for each active node:
  for each tension in tensions_introduced:
    check if any child node has resolves_tension referencing this node
    if not → tension is orphaned (unresolved technical debt)
→ returns your technical debt map
```

**Query 6: Assumption inheritance depth**
```
for each active leaf node:
  count the length of inherited_assumptions list
→ nodes with many inherited assumptions are fragile
  they stand on decisions made with less context than today
  high count = candidate for a consolidating fresh decision
```

**Query 7: Decision velocity per domain**
```
group nodes by domain
for each domain, count nodes per time window (by sequence range)
→ high velocity in short sequence range = unstable domain
  domain hasn't found its shape yet = architectural risk
```

### graph.json Format

```json
{
  "nodes": {
    "20240115-001": {
      "status": "superseded",
      "domains": ["auth"],
      "children": ["20240203-001", "20240812-002"]
    },
    "20250914-001": {
      "status": "active",
      "domains": ["auth", "payments"],
      "parents": ["20240812-002", "20240115-001"],
      "children": []
    }
  },
  "edges": [
    { "from": "20240115-001", "to": "20240203-001" },
    { "from": "20240115-001", "to": "20240812-002" },
    { "from": "20240812-002", "to": "20250914-001" },
    { "from": "20240115-001", "to": "20250914-001" }
  ]
}
```

---

## 9. Enforcement Layer

### Pre-commit Hook (Client Side)

```bash
#!/bin/bash
# /hooks/pre-commit
# Install: cp hooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

CONTEXT_TOUCHED=$(git diff --cached --name-only | grep -c "^context/")
COMMIT_MSG_FILE="$1"
COMMIT_MSG=$(cat "$COMMIT_MSG_FILE" 2>/dev/null)

if [ "$CONTEXT_TOUCHED" -gt 0 ]; then
  echo "✓ Context updated"
  exit 0
fi

if echo "$COMMIT_MSG" | grep -q "\[skip-context\]"; then
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  BRANCH=$(git branch --show-current)
  FILES=$(git diff --cached --name-only | head -5 | tr '\n' ', ')
  echo "  $TIMESTAMP | branch: $BRANCH | files: $FILES | msg: $COMMIT_MSG" >> context/drift-register.md
  git add context/drift-register.md
  echo "⚠ Context skipped — logged to drift-register.md"
  exit 0
fi

echo "✗ No context updated."
echo "  Update a file in /context/ or add [skip-context] to your commit message."
echo "  [skip-context] commits are logged publicly in context/drift-register.md"
exit 1
```

### CI Checks (Server Side — No Escape)

```yaml
# .github/workflows/context-integrity.yml (or equivalent)

name: Context integrity

on: [pull_request]

jobs:
  check:
    steps:
      - name: Schema validation
        run: |
          # Every .yaml in context/timeline/ must match decision schema
          python tools/validate-schema.py context/timeline/

      - name: Link integrity
        run: |
          # Every D-ID referenced anywhere in /context must resolve to a file
          python tools/check-links.py context/

      - name: Stale reference check
        run: |
          # /current/ files must not reference status:superseded nodes
          python tools/check-stale-refs.py context/

      - name: Cycle detection
        run: |
          # DAG must remain acyclic
          python tools/check-dag.py context/timeline/

      - name: AI commit enforcement
        run: |
          # If commit message contains [ai-commit], context/ must be touched
          python tools/check-ai-commits.py

      - name: Drift register validation
        run: |
          # If commit contains [skip-context], drift-register.md must have been updated
          python tools/check-drift-register.py
```

### AI Commit Rule

Any commit where author is identified as an AI agent (by commit metadata flag `[ai-commit]` in message, or by author email pattern, or by a dedicated git trailer `Context-Updated: true/false`) must include at least one file change in `/context/timeline/`.

No escape hatch. Hard block at CI. Rationale: AI agents can be programmatically forced. The same leniency given to humans is not appropriate for automated actors.

---

## 10. Greenfield vs Brownfield Analysis

### Greenfield — Works, with One Trap

**What works well**:
- You start with one domain file, write the first decision record, and build the corpus as the system grows
- The graph reflects actual evolution because you're writing decisions as they happen, not reconstructing them
- Domain files stay accurate because they're generated from the graph
- New developers can traverse the full lineage from day one

**The bootstrapping trap**:
Domains are hypotheses in a greenfield project. You don't know what the right domain boundaries are until you've built enough to see them. Teams that define 10 domain files on day one will find that 6 are wrong by month 3.

**The rule**: Start with `system.md` as the only domain file. Only split when a section is clearly and obviously its own concern. Let domains emerge from the system — never impose them before the system exists.

**The premature domain problem**: Every domain boundary you define before building is a guess. The graph will accumulate decisions referencing a domain that later gets split. When `auth` splits into `auth` and `identity`, all decisions referencing `auth` need review. Domain splitting is the most expensive refactor in this system.

---

### Brownfield — Hard, Often the Wrong Starting Point

**The core problem**: The most important decisions to understand are the oldest ones — the foundational architectural choices everything else is built on. These are exactly the ones that are hardest to reconstruct because:
- The original developers may be gone
- The original context (deadlines, constraints, alternatives considered) is gone
- Git history gives you *what* changed, not *why*
- Reconstructed decisions are rationalized history, not real history

**What happens in practice**:
A developer reconstructing decisions from a 3-year-old codebase writes records that make the choices look obviously correct — because they know what was chosen and write backwards from that. The alternatives that were actually considered but rejected are lost. The pressure that forced a bad decision is lost. The record looks complete but is actually post-hoc justification.

**The practical approach for brownfield**:

Do not try to document the whole system at once. It will fail. Instead:

1. Pick the highest-churn domain — the one with the most bugs and the most new work
2. Write one domain file for that domain, describing current state accurately
3. Write decision records only for **new decisions going forward** — don't reconstruct old ones
4. Let the glacier start empty or nearly empty
5. Document old territory only when someone needs to change it — make it a rule: "before touching module X, write a current-state domain file for X"
6. Allocate 15-20% of sprint capacity to this, explicitly, in the sprint plan — not as "tech debt" that gets cut under pressure

**The brownfield exception for foundational decisions**:
Even in brownfield, there are usually 3-5 decisions that are truly foundational — the choice of database, the auth approach, the deployment model, the core data model. These are worth reconstructing even imperfectly. An imperfect record of a foundational decision is more valuable than no record, because it prevents future developers from relitigating settled questions.

Label reconstructed decisions explicitly:
```yaml
reconstruction: true
reconstruction_confidence: low | medium | high
reconstruction_note: >
  Reconstructed from git history and interview with original developer.
  Alternatives section is incomplete — original options are unknown.
```

---

### Side-by-Side Comparison

| Dimension | Greenfield | Brownfield |
|---|---|---|
| Starting point | Empty graph, build forward | Existing system, retrofit backward |
| Decision records | Written as decisions happen (accurate) | Reconstructed from history (rationalized) |
| Domain definitions | Emerge from system over time | Must be inferred from existing architecture |
| First value delivered | Immediately — first decision is in the graph | Delayed — system must be understood before documented |
| Biggest risk | Premature domain definition | Selective coverage creating false confidence |
| Recommended starting domain | Wherever first feature is being built | Highest-churn, most bug-prone domain |
| Glacier at start | Empty | Empty (don't reconstruct old decisions unless foundational) |
| Time to useful corpus | 2-3 sprints | 6-12 sprints |

---

## 11. Known Unresolved Problems

These problems were identified but not resolved during this design session. They require either further design decisions or acceptance as known limitations.

**UNRESOLVED-001: Who decides when a domain should split?**
Domain splits require authority, coordination, and migration of existing decision records. There is no defined process or authority for this yet.

**UNRESOLVED-002: How does the drift detector distinguish significant from trivial code changes?**
Per-domain path configuration helps but requires maintenance. Who updates drift-config.yaml when the codebase structure changes?

**UNRESOLVED-003: Schema migration for decision records**
When the decision YAML schema needs to evolve (new required field, renamed field), existing records don't auto-migrate. Need a schema version field and migration tooling. Currently undefined.

**UNRESOLVED-004: Cross-repository decisions**
In a multi-repo environment, a decision can span repositories. Where does it live? How do parent-child links work across repo boundaries? The current design assumes a single repository.

**UNRESOLVED-005: Graph visualization**
The graph.json is machine-readable but not human-navigable for large graphs. A visualization tool (even a simple one) is needed before the graph becomes useful for developers who aren't writing tooling. Currently unspecified.

**UNRESOLVED-006: The context owner problem at scale**
Small teams: nobody has spare capacity for the context owner role. Large teams: multiple context owners for shared domains create coordination overhead. No solution defined.

**UNRESOLVED-007: Assumption extraction**
The `assumptions` field will consistently be the lowest quality field in every decision record. No tooling or process has been defined to improve assumption capture quality. This is the field that matters most when things break.

**UNRESOLVED-008: Retroactive foundational decision quality in brownfield**
Reconstructed decisions are rationalized history. Labeling them `reconstruction: true` with confidence levels helps but doesn't solve the underlying quality problem. Imperfect history may be worse than acknowledged absence of history if it misleads future decisions.

---

## 12. What to Build First

Ordered by dependency and value delivered.

### Step 1: Schema and folder structure (no tooling yet)
Define the YAML schema. Create the folder structure. Write the first real decision record manually. Validate that the schema captures what you actually need by using it on a real decision in your actual project.

Do not build any tooling yet. Use the schema for 2-3 weeks manually. You will discover what's missing or wrong before investing in automation.

### Step 2: Pre-commit hook
Simple bash script. Checks for `/context` touch or `[skip-context]`. Logs skips to drift-register.md. No AI, no complexity. Ship this as soon as the schema is stable.

### Step 3: Schema validator
A script that validates all YAML files in `/context/timeline/` against the schema. Runs in CI. Fails on malformed records. This is the first CI gate.

### Step 4: Link integrity checker
Crawls all markdown and YAML in `/context/`, extracts all decision ID references, checks they resolve to files. Flags broken links and stale references (links to `status: superseded` nodes). Second CI gate.

### Step 5: Graph builder
Script that reads all YAML nodes and builds `graph.json`. Runs as part of CI. Includes cycle detection — fails if a cycle is found.

### Step 6: Domain file renderer
Script that reads `graph.json`, filters by domain and `status: active`, and renders `/current/*.md` files. This is when domain files stop being handwritten. Until this step, domain files are still handwritten and subject to merge conflicts.

### Step 7: Drift detector
Weekly job. Reads `drift-config.yaml`, checks git history per domain's tracked paths, compares against decision record dates, reports staleness. Appends to `drift-register.md`.

### Step 8: Graph visualization
Even a simple static HTML page rendering the DAG is valuable. Nodes as circles, edges as arrows, color-coded by status (active = filled, superseded = hollow), filterable by domain. This is what makes the system navigable for developers who aren't writing tooling.

---

## Appendix: Quick Reference

### Commit conventions
- Normal commit touching context: no special message needed
- Skip context update: add `[skip-context]` to commit message
- AI-generated commit: add `[ai-commit]` to commit message (context update mandatory)

### Status values
- `active` — current truth, leaf node in the graph
- `superseded` — replaced by one or more child decisions, historical record only

### Decision ID format
`YYYYMMDD-NNN` where NNN is a zero-padded counter scoped to the day (001, 002, ...)
Lexicographic sort of filenames = chronological order of decisions

### Field quick reference
| Field | Required | Notes |
|---|---|---|
| id | yes | Must match filename |
| status | yes | active or superseded |
| date | yes | Human readable, not used for ordering |
| author | yes | human or ai |
| domains | yes | List, minimum one |
| parents | no | Empty list for foundational decisions |
| children | no | Filled when superseded |
| decision | yes | What was decided |
| context | yes | Why it was needed |
| alternatives_rejected | recommended | Most valuable for future readers |
| assumptions.inherited | recommended | Re-state from parents, still load-bearing |
| assumptions.new | yes | What this decision now depends on |
| tensions_introduced | recommended | What is now unstable |
| resolves_tension | no | If this resolves a tension from a parent |
| reconstruction | no | true if retroactively reconstructed (brownfield) |
| reconstruction_confidence | if reconstruction=true | low, medium, or high |


---
---

# Cortex — Implementation Design

> Context-aware decision tracking system.
> File-based YAML storage. Python package (typer, pydantic). Date-driven timeline. AI-assisted merge.
> AI-assisted: humans decide, AI drafts. Enforcement catches structural failures, humans catch semantic ones.
> Derived from the full design record in `context-system-design.md`.

---

## Table of Contents

1. [Architecture Decisions](#1-architecture-decisions)
2. [AI-Assisted Operating Model](#2-ai-assisted-operating-model)
3. [Skills and Personas](#3-skills-and-personas)
4. [Folder Structure](#4-folder-structure)
5. [Decision Record Schema](#5-decision-record-schema)
6. [How Decisions Work as a Timeline](#6-how-decisions-work-as-a-timeline)
7. [The DAG — File-Based Graph](#7-the-dag--file-based-graph)
8. [Multi-Developer Merge Strategy](#8-multi-developer-merge-strategy)
9. [Python Tooling](#9-python-tooling)
10. [Enforcement Layer](#10-enforcement-layer)
11. [Frontend — Static Viz in Phase 2, Interactive Deferred](#11-frontend--static-viz-in-phase-2-interactive-deferred)
12. [Build Order](#12-build-order)

---

## 1. Architecture Decisions

### Storage: Files in Git, Not a Database

**Decision:** All decisions, graph state, and domain views live as files inside the repository.

**Why:**

- Clone the repo → you have the full decision history. No external dependencies.
- Git diff shows exactly what changed in a decision record. YAML diffs are readable.
- PR review works natively — a decision record is reviewable like code.
- No infrastructure to host, back up, or migrate.
- Context never gets separated from the code it describes.

**Trade-off accepted:** No native query engine. Python tooling fills this gap — it reads the YAML files, builds an in-memory graph, and answers queries programmatically. Slower than SQL, but the dataset is small (hundreds to low thousands of decisions, not millions).

### Authoring Format: YAML

**Decision:** Decision records are YAML files. One file per decision.

**Why:**

- Human-readable and human-writable
- Machine-parseable (Python `pyyaml` / `ruamel.yaml`)
- Git-diffable
- Supports structured data (lists, nested objects) without inventing a format

### Tooling: Python

**Decision:** All tooling (validation, graph operations, rendering, drift detection) is Python.

**Why:**

- Team already uses Python
- Rich ecosystem: `networkx` for graph operations, `pyyaml` for parsing, `jsonschema` for validation
- Easy to extend with AI capabilities (LLM calls for merge assistance, assumption extraction)
- Frontend can be added later (Streamlit, Panel, or hand off data to a lightweight JS frontend)

### Timeline: Date-Based Decision IDs

**Decision:** Decision IDs use the format `YYYY-MM-DD-NNN`. The filename IS the timeline position.

**Why:**

- Lexicographic sort of filenames = chronological order. No secondary index needed.
- The date is visible in the filename — no need to open the file to know when a decision was made.
- The suffix (`-001`, `-002`) handles multiple decisions on the same day.
- Acts as both identifier AND timeline position. One concept, not two.

### Frontend: Static Visualization Early, Interactive Deferred

**Decision:** Static HTML+SVG graph visualization generated during `build` in Phase 2. Interactive frontend deferred until schema is stable.

**Why:**

- Developers need to *see* the graph from day one — it's their primary review tool.
- Static HTML+SVG is zero-infrastructure: open in a browser, generated by Python, committed to repo.
- Interactive frontend (Streamlit, lightweight JS) added later when interaction patterns are known.
- `graph.json` is the API contract — any frontend can consume it.

---

## 2. AI-Assisted Operating Model

### The Core Shift

This is **AI-assisted development with human decision-making.** AI agents draft code, draft decision records, validate integrity, and assist with merges. Humans make the decisions, review AI output, and direct AI when it deviates from standards.

AI is not autonomous. It assists. Humans don't just oversee — they decide. When AI drafts a decision record, a human reviews it and says "yes, this is what we decided" or "no, change this." The `author: ai` field means "AI drafted this," not "AI decided this."

Agent quality will be inconsistent. The enforcement layer catches structural failures (malformed YAML, broken links, cycles). Human review catches semantic failures (wrong assumptions, missing context, inaccurate decisions). Both are required.

### Who Does What

| Activity | Who Acts | Who Decides |
|---|---|---|
| Write code | AI drafts | Human reviews PR, directs on standards |
| Create decision records | AI drafts | Human reviews for accuracy, approves or corrects |
| Validate schema + integrity | Automated (CI) | No human needed |
| Build graph + render views | Automated (CI) | No human needed |
| Resolve ID collisions | AI resolves (merge-assist) | Human verifies result |
| Detect contradictions | AI flags (merge-assist) | Human (senior dev) resolves |
| Detect drift | Weekly batch job | Human triages findings |
| Domain splits/renames | Human proposes | Senior dev decides |
| Foundational decisions | Human or AI proposes | Senior dev approves |
| Read/visualize system state | Human (CLI/frontend) | Human is primary consumer |
| Choose AI operating mode | Human sets per-session | Developer decides autonomy level |

### Agent Rules

Agents operating on a project with this context system MUST:

1. **Read existing context before making decisions.** Before implementing in any domain, the agent reads `context/current/{domain}.md` and active timeline entries for that domain. It does not work blind.
2. **Write a decision record for every architectural/structural change.** See "When to Write a Decision Record" below.
3. **Fill ALL schema fields.** Agents have no excuse for empty fields. The `assumptions` field — which humans leave blank — is where agents provide the most value. Agents must extract assumptions from their own reasoning.
4. **Include the decision YAML in the same commit as the code change.** Atomic. No separate "docs update" commits.
5. **Validate before committing.** Run `context_cli.py validate` on the new YAML before including it in the commit.
6. **Never edit generated files.** `current/*.md`, `tensions/*.md`, `graph.json`, and `context-graph.html` are build artifacts. Agents write YAML, tooling generates the rest.
7. **Declare which skill is loaded** (if any) so the human can verify or redirect.

### When to Write a Decision Record

**A decision record IS needed for:**

- New technology choices (database, framework, library for a new purpose)
- New patterns (how auth works, how APIs are structured, how data flows)
- Changes to existing patterns (REST → GraphQL, new cache strategy)
- Cross-domain changes (one domain's change affects another)
- New domains or domain splits
- Anything that changes the answer to "how does X work?"

**A decision record is NOT needed for:**

- Bug fixes (unless the fix changes the architectural approach)
- Refactoring (unless it changes system boundaries or data flow)
- Style changes, dependency bumps, test additions
- Feature implementation that follows an existing established pattern

**The heuristic:** If a new developer joined tomorrow and read this code, would they ask "why is it done this way?" If yes → write a decision record. If the code is self-explanatory → no record needed.

**Reviewers CAN reject and delete** agent-generated decision records that aren't decision-worthy. This is curation, not deletion of history — the code change still exists in git.

### Agent Context Discovery

Before an agent starts work in a domain, it needs to know what already exists. The CLI provides this:

```bash
python tools/context_cli.py agent-context --domain auth
```

This outputs a compact, LLM-friendly dump:

- Current active decisions for the domain
- Active tensions (what's unstable)
- Recent decisions (last 10 by date)
- Inherited assumptions still in play
- Related domains (by coupling map)

This is the agent's "briefing" before it starts work. It replaces the need for the agent to read multiple files.

### Domain-Level Review Config

Not all agent decisions need human review. Critical domains require it; stable utility domains don't.

```yaml
# context/review-config.yaml
domains:
  auth:
    agent_review: required        # human must review every agent decision
    reviewer: senior-dev
  payments:
    agent_review: required
    reviewer: senior-dev
  notifications:
    agent_review: optional        # auto-merge if validation passes
  utils:
    agent_review: skip            # no review needed
```

This replaces the rejected `confidence` field. Instead of trusting the agent's self-assessment, the *domain itself* determines the review rigor.

---

## 3. Skills and Personas

### Concept: Loadable Skills for AI Agents

Inspired by the BMAD Method's approach of specialized agents (PM, Architect, Developer, UX, etc.), this system uses **loadable skills** — context files that give an AI agent domain-specific expertise when needed.

A skill is NOT a separate agent. It is a **context file** that the current AI agent reads to gain specialized knowledge for a specific task. One agent, many skills. Skills are detailed prompt context files that ensure consistency across team members and AI platforms — humans can't type them every time, and they must be consistent.

There are two categories:

- **System skills** — ship with the context system. About context management itself (reviewing records, triaging drift).
- **Project skills** — created per project. About the project's technical domain (architecture patterns, frontend conventions, API design).

AI can access both.

### Operating Modes

The developer chooses how much autonomy the AI has in skill selection per session:

| Mode | How it works |
|---|---|
| **1. Full human control** | Human explicitly tells AI which skill to load for every task |
| **2. AI autonomous** | AI selects skills based on task context, declares which it loaded |
| **3. AI unsure → human intervenes** | AI attempts to select, asks human when uncertain |
| **4. Human directs + asks AI opinion** | Human picks the direction, asks AI to suggest which skill applies |

In all modes, the AI **declares which skill it loaded.** If the human disagrees, they debate — the human can redirect, and both learn. Skills get updated based on these interactions.

### How Skills Work

```
Task arrives (e.g., "Review the auth architecture")
        │
        ▼
Operating mode check:
        │
        ├── Mode 1 → Human says: "load architect.md"
        ├── Mode 2 → AI selects architect.md, declares: "I loaded architect.md for this task"
        ├── Mode 3 → AI suggests: "I think architect.md applies. Proceed?"
        └── Mode 4 → Human says: "Review this." AI suggests: "architect.md is relevant"
        │
        ▼
Agent reads the skill file (short description first, full file if needed)
        │
        ▼
Agent performs task with loaded skill context
```

### Skill Files

Skills include a short description (one line) so AI can pick from a summary index without loading full files into context.

**System skills** (ship with context system):

```
context/skills/
    _index.md                       ← one-line description of each skill (AI reads this first)
    reviewer.md                     ← PR review criteria for decision records
    context-owner.md                ← drift triage, domain health assessment
```

**Project skills** (created per project, not part of context system):

```
context/skills/
    architect.md                    ← architecture review, system design patterns
    senior-dev.md                   ← code quality, technical debt assessment
    frontend-dev.md                 ← UI/UX implementation, component patterns
    backend-dev.md                  ← API design, data modeling, service patterns
    merge-helper.md                 ← conflict resolution guidance
    ... (project adds as needed)
```

**`_index.md` format** (AI reads this to choose skills):

```markdown
# Skill Index
- reviewer: PR review criteria for decision records and context quality
- context-owner: Drift triage, domain health assessment, weekly review
- architect: Architecture review, system design trade-offs, cross-domain impact
- senior-dev: Code quality, tech debt, implementation standards
- frontend-dev: UI component patterns, state management, accessibility
- backend-dev: API design, data modeling, service communication
- merge-helper: Conflict resolution, decision re-ordering, contradiction detection
```

### Skill File Structure

Each skill file follows a consistent structure:

```markdown
# Skill: Architect

## Role
You are reviewing/acting as a senior software architect.

## When This Skill Is Loaded
- Architecture review of a decision or proposal
- Evaluating system design trade-offs
- Assessing cross-domain impact of a change

## Criteria
[Domain-specific checklist, patterns, anti-patterns]

## Output Format
[What the skill produces — review comments, decision records, reports]
```

### Skills vs. BMAD Agents — What We Take, What We Don't

| BMAD Concept | Our Approach | Why |
|---|---|---|
| Specialized agents (PM, Architect, Dev) | **Loadable skill files** for one agent | We don't need separate agents. One agent loads the right skill for the task. Simpler. |
| Workflows (create-prd, create-architecture) | **CLI commands** that trigger agent actions | Same idea, different packaging. Our CLI is the workflow runner. |
| Party mode (multiple personas debate) | **Not adopted** | Interesting but adds complexity. A single agent with the right skill file is sufficient for our scope. |
| bmad-help (intelligent guide) | **`agent-context` command** | Same purpose: tell the agent what exists and what to do next. Ours is domain-scoped, not project-scoped. |
| Skill discovery by SKILL.md | **Adopted as `_index.md`** | Short descriptions in an index file. AI reads index first, loads full skill on demand. |
| Module system (BMM, TEA, etc.) | **Not adopted** | Overkill for a context tracking system. We don't need installable modules. |

### When Skills Are Used

| Task | Skill Loaded | Who Triggers |
|---|---|---|
| Reviewing a decision record PR | `reviewer.md` | Human asks, or AI selects (mode 2/3) |
| Triaging weekly health report | `context-owner.md` | Human asks agent to analyze drift |
| Architecture decision | `architect.md` (project skill) | Human asks, or AI selects for cross-domain decisions |
| Implementing a feature | `backend-dev.md` / `frontend-dev.md` (project) | AI selects based on file types, or human directs |
| Resolving merge conflicts | `merge-helper.md` (project skill) | Human loads when resolving conflicts |
| Writing decision records | None needed — base agent capability | Always active |

### Adding New Skills

Skills are just markdown files. To add a new skill:

1. Create `context/skills/{skill-name}.md`
2. Follow the structure (Role, When Loaded, Criteria, Output Format)
3. The agent discovers it by listing `context/skills/`

No registration, no config, no manifest. The file IS the skill.

---

## 4. Folder Structure

```
project-root/
│
├── context/
│   ├── timeline/                    ← one YAML file per decision, ordered by date
│   │   ├── 2025-04-25-001.yaml
│   │   ├── 2025-04-25-002.yaml
│   │   ├── 2025-04-28-001.yaml
│   │   └── ...
│   │
│   ├── current/                     ← generated domain views (committed, do not hand-edit)
│   │   ├── auth.md
│   │   ├── payments.md
│   │   └── ...
│   │
│   ├── skills/                      ← loadable expertise for AI agents
│   │   ├── _index.md                ← one-line descriptions (AI reads this first)
│   │   ├── reviewer.md              ← system skill: decision record review
│   │   ├── context-owner.md         ← system skill: drift triage, health
│   │   └── ... (project skills added as needed)
│   │
│   ├── agent-rules.md              ← precise instructions for how agents use this system
│   ├── review-config.yaml          ← per-domain review requirements
│   ├── drift-register.jsonl        ← log of [no-decision] commits (one JSON per line)
│   └── drift-config.yaml           ← per-domain file path tracking config
│
│   # GENERATED (gitignored, rebuilt by `build`):
│   # tensions/active.md          ← generated, available as CI artifact
│   # tensions/resolved.md        ← generated, available as CI artifact
│   # graph.json                  ← generated, available as CI artifact
│   # context-graph.html          ← generated, view locally after `build`
│
├── tools/                           ← Python tooling
│   ├── context_cli.py              ← CLI entry point
│   ├── ingest.py                   ← reads all YAML → builds in-memory graph
│   ├── validate.py                 ← schema + integrity checks
│   ├── render.py                   ← generates current/*.md, tensions/*.md, context-graph.html
│   ├── graph_ops.py                ← DAG queries (ancestry, point-in-time, etc.)
│   ├── merge_assist.py             ← ID collision resolution + conflict flagging
│   ├── drift.py                    ← drift detection against git history
│   ├── schema.json                 ← JSON Schema for decision YAML validation (versioned)
│   └── requirements.txt
│
└── hooks/
    ├── pre-commit                   ← checks context/timeline/ files are staged
    └── commit-msg                   ← checks [no-decision] and logs to drift register
```

### What's hand-written vs. generated

| Path | Written by | Edited by hand? |
|---|---|---|
| `context/timeline/*.yaml` | AI agents (draft), developers (review/approve) | Yes — this is the source of truth |
| `context/current/*.md` | `tools/render.py` | **No** — regenerated from graph, committed to repo |
| `context/tensions/*.md` | `tools/render.py` | **No** — regenerated, gitignored, CI artifact |
| `context/graph.json` | `tools/ingest.py` | **No** — rebuilt from YAML, gitignored, CI artifact |
| `context/context-graph.html` | `tools/render.py` | **No** — gitignored, view locally after `build` |
| `context/skills/_index.md` | Developers | Yes — skill summary index |
| `context/skills/*.md` | Developers | Yes — loadable expertise files |
| `context/agent-rules.md` | Developers | Yes — precise agent operating instructions |
| `context/review-config.yaml` | Developers | Yes — per-domain review policy |
| `context/drift-register.jsonl` | Hooks, weekly health job | Append-only |
| `context/drift-config.yaml` | Developers | Yes — path-based triggering config |

---

## 5. Decision Record Schema

### Design Goal: Minimum fields to be useful, maximum fields optional

The original design had 15+ fields. That's too many for daily use. This schema splits into **required** (you must fill these or the validator rejects) and **recommended** (fill when relevant, leave out when not).

### YAML Schema

```yaml
# File: context/timeline/YYYY-MM-DD-NNN.yaml

# === REQUIRED ===
id: "2025-04-25-001"            # must match filename
status: active                   # active | superseded
date: "2025-04-25"              # ISO date, matches the ID prefix
author: human                    # human | ai
domains:                         # at least one
  - auth

decision: >
  What was decided. One paragraph. Concrete and specific.

context: >
  Why this was needed. What situation or problem forced this decision.

# === RECOMMENDED (agents MUST fill all, humans SHOULD fill when relevant) ===
parents: []                      # IDs of decisions this causally follows from
                                 # empty for foundational/first decisions

alternatives_rejected:           # what else was considered and why not
  - option: "Session-based auth"
    reason: "Doesn't scale horizontally without sticky sessions"

assumptions:                     # what this decision depends on being true
  - "Tokens are stateless, no server-side revocation"
  - "Role assignments do not change mid-session"

tensions:                        # what this decision makes unstable or risky
  - "Session length now varies by role — mobile clients must handle differently"

resolves:                        # if this decision resolves a tension from a parent
  tension: "Single global expiry can't serve both admin and service accounts"
  from: "2025-04-25-001"

tags: []                         # free-form labels for search/filtering
                                 # e.g. [jwt, security, mobile, expiry]

# === OPTIONAL ===
reviewed_by: ""                  # filled when a human reviews an agent-authored decision
                                 # e.g. "deepan" or "senior-dev-name"

# === AUTO-POPULATED (by tooling, not by humans) ===
# These fields are computed by ingest.py and written into graph.json, NOT stored in YAML.
# children: [...]               ← computed: all decisions that list this ID as a parent
# inherited_assumptions: [...]  ← computed: recursive parent traversal collects all assumptions
# summary: "..."                ← computed: first 120 chars of decision text, for graph tooltips
```

### What changed from the original design

| Original | Now | Why |
|---|---|---|
| `children` field in YAML | Computed at ingest time | Eliminates sync problem — adding a child no longer requires editing the parent file |
| `assumptions.inherited` + `assumptions.new` | Single `assumptions` list (new only) | Inherited assumptions computed by traversal. Authors only write what's new. |
| `tensions_introduced` | `tensions` | Simpler name, same purpose |
| `resolves_tension` (free text) | `resolves` (structured: `tension` + `from`) | Tooling can match automatically. No free-text parsing needed. |
| No `tags` field | `tags` added | Cheap metadata for search and filtering without restructuring domains |
| No `reviewed_by` field | `reviewed_by` added | Tracks human review of agent-authored decisions |
| No `summary` in graph | `summary` computed in graph.json | Truncated decision text for graph tooltips without loading YAML |
| 15+ fields | 6 required, 6 recommended, 1 optional | Agents fill all. Humans fill required + what's relevant. |
| "Recommended" = optional for all | Agents MUST fill all. Humans SHOULD fill recommended. | Different rules for different actors. Agents have no excuse for empty fields. |

### Minimal Valid Decision Record

The smallest possible valid decision:

```yaml
id: "2025-04-25-001"
status: active
date: "2025-04-25"
author: human
domains:
  - auth
decision: >
  Use JWT tokens with RS256 signing for all API authentication.
context: >
  Need stateless auth that works across multiple service instances
  without shared session storage.
```

That's 8 lines of actual content. A developer can write this in under 2 minutes.

---

## 6. How Decisions Work as a Timeline

The decision ID format `YYYY-MM-DD-NNN` makes the timeline implicit in the file listing.

```
context/timeline/
├── 2025-04-25-001.yaml    ← day 1: chose JWT auth
├── 2025-04-25-002.yaml    ← day 1: chose PostgreSQL
├── 2025-04-28-001.yaml    ← day 4: added RBAC
├── 2025-05-02-001.yaml    ← day 8: per-role token expiry
├── 2025-05-02-002.yaml    ← day 8: refresh token rotation
├── 2025-05-15-001.yaml    ← day 21: split auth into auth + identity domains
└── ...
```

### Reading the timeline

**What happened this week?**

```bash
ls context/timeline/2025-04-2*.yaml
```

**What happened in a domain over time?**

```bash
grep -l "auth" context/timeline/*.yaml | sort
```

**What's the current state?**

```bash
grep -rl "status: active" context/timeline/*.yaml
```

These are instant, zero-tooling answers. The Python tooling makes them richer, but the raw files are usable without any tooling at all.

### Volume Projection

With AI agents drafting decision records, expect higher decision volume than a purely manual workflow:

- **Year 1:** 200-500 decisions (agents generate 5-10/week on active projects)
- **Year 2:** 500-1000 decisions
- **Year 3:** 1000-1500 decisions

At this scale, `ls` and `grep` still work. `networkx` handles graphs of this size in milliseconds. No performance concerns until 10,000+ nodes, which is years away for any single project.

### Point-in-time snapshots

"What did the system look like on April 28th?"

**Without tooling:** List all files with dates ≤ 2025-04-28. Among those, the ones with `status: active` (that haven't been superseded by a later decision) represent the state at that point.

**With tooling:** `python tools/context_cli.py snapshot --date 2025-04-28 --domain auth`

The tooling handles the edge case: a decision created on April 25 that was superseded on May 2 was still active on April 28. The tooling checks whether any child decision has a date ≤ April 28. If not, the parent is still active at that point.

---

## 7. The DAG — File-Based Graph

### How the graph is built

The graph is not stored as a primary artifact. It is **computed** from the YAML files.

```
YAML files (source of truth)
        │
        ▼
   ingest.py reads all YAML
        │
        ▼
   In-memory graph (networkx DiGraph)
        │
        ├──▶ graph.json (serialized for other tools / future frontend)
        ├──▶ current/*.md (domain views rendered from active leaf nodes)
        ├──▶ tensions/*.md (rendered from unresolved tensions)
        └──▶ Validation results (cycles, broken links, stale refs)
```

### What the graph captures

Every YAML file is a **node**. Every `parents` reference is a **directed edge** (parent → child, causality flows forward). The graph is a DAG — directed, acyclic.

```
2025-04-25-001 (JWT auth)
        │
        ├──────────────────────┐
        ▼                      ▼
2025-04-28-001 (RBAC)    2025-05-15-001 (auth/identity split)
        │
        ▼
2025-05-02-001 (per-role expiry)
        │
        ▼
2025-05-02-002 (refresh rotation)
```

### graph.json format

```json
{
  "generated_at": "2025-04-25T10:30:00Z",
  "schema_version": "1.0",
  "nodes": {
    "2025-04-25-001": {
      "status": "superseded",
      "domains": ["auth"],
      "parents": [],
      "children": ["2025-04-28-001", "2025-05-15-001"],
      "tags": ["jwt", "security"],
      "author": "ai",
      "reviewed_by": "deepan",
      "summary": "Use JWT tokens with RS256 signing for all API authentication"
    },
    "2025-05-02-001": {
      "status": "active",
      "domains": ["auth"],
      "parents": ["2025-04-28-001"],
      "children": [],
      "tags": ["jwt", "expiry", "rbac"],
      "author": "ai",
      "reviewed_by": "",
      "summary": "Per-role JWT expiry: admin 15min, user 1hr, service 30d"
    }
  },
  "edges": [
    {"from": "2025-04-25-001", "to": "2025-04-28-001"},
    {"from": "2025-04-25-001", "to": "2025-05-15-001"},
    {"from": "2025-04-28-001", "to": "2025-05-02-001"}
  ],
  "stats": {
    "total_decisions": 5,
    "active_decisions": 2,
    "superseded_decisions": 3,
    "domains": ["auth", "identity", "payments"],
    "unresolved_tensions": 3,
    "last_decision_date": "2025-05-15",
    "stale_domains": ["payments"],
    "ai_authored": 4,
    "human_authored": 1,
    "reviewed": 3,
    "unreviewed": 2
  }
}
```

### Graph queries (Python, not SQL)

These are implemented in `tools/graph_ops.py` using `networkx`:

| Query | What it answers | How |
|---|---|---|
| `active_for_domain(domain)` | Current state of a domain | Filter nodes: `domain ∈ domains AND status == active` |
| `ancestry(node_id)` | Full causal chain of a decision | `nx.ancestors(graph, node_id)` — returns all reachable parents |
| `snapshot(date, domain)` | State at a point in time | Filter nodes by date ceiling + check if superseded before that date |
| `orphaned_tensions()` | Unresolved tech debt | Active nodes with tensions that no child's `resolves` field references |
| `assumption_depth(node_id)` | Fragility of a decision | Count assumptions accumulated through ancestry chain |
| `domain_velocity(domain, days)` | How stable a domain is | Count decisions in domain within last N days |
| `coupling_map()` | Cross-domain risk | Nodes with `len(domains) > 1`, grouped by domain pairs |
| `impact(node_id)` | Downstream reach of a decision | `nx.descendants(graph, node_id)` — all decisions caused by this one |

---

## 8. Multi-Developer Merge Strategy

### The Problem

Two developers working in parallel may:

1. Create decisions with the same date-suffix (`2025-04-25-001`) — ID collision
2. Create decisions in the same domain that should reference each other but don't — missing links
3. Create decisions that contradict each other — conflicting directions

### The Strategy: AI-Assisted Merge + Senior Dev Review

```
Developer A (feature branch)         Developer B (feature branch)
creates 2025-04-25-001.yaml          creates 2025-04-25-001.yaml
        │                                     │
        ▼                                     ▼
    Opens PR to main                      Opens PR to main
        │                                     │
        └──────────┐         ┌────────────────┘
                   ▼         ▼
              CI detects conflict
                     │
                     ▼
         merge_assist.py runs (AI layer)
                     │
                     ├── ID collision? → auto-renumber the later PR's file
                     │                   (2025-04-25-001 → 2025-04-25-002)
                     │
                     ├── Same domain, no parent link? → suggest parent linkage
                     │                                  (flag for human review)
                     │
                     └── Contradicting decisions? → block merge, flag for
                                                    senior dev review
                     │
                     ▼
            Senior dev reviews flagged items
                     │
                     ▼
               Merge to main
```

### Three levels of merge conflict

**Level 1: ID Collision (auto-resolved by AI)**

Two files have the same name. This is mechanical.

Resolution: The tool resolves by **author + relevance** — not just "later PR gets bumped." If one decision is clearly more central to the domain (more parent references, broader scope), it keeps the earlier ID. The secondary decision gets its suffix incremented. All internal references (`id` field, any `parents` references in other files in the same PR) are updated.

```
Before: both PRs have 2025-04-25-001.yaml
After:  More relevant decision keeps 2025-04-25-001.yaml
        Other becomes 2025-04-25-002.yaml (all refs updated)
```

**Level 2: Missing Links (AI suggests, human approves)**

Two decisions in the same domain created independently. They may need a parent-child relationship or may be siblings under a common parent.

The AI reads both decisions and flags them for human review with a summary of what it found:

- "Same domain, possibly related — review before merge"
- "Same domain, same parent — likely needs coordination"

No LLM classification in v1. Heuristic flagging only. A developer reviews and decides.

**Level 3: Contradictions (Senior dev required)**

Two decisions that cannot both be active. Example:

- PR-A: "Use Redis for session storage"
- PR-B: "Use PostgreSQL for session storage"

The merge-assist tool detects same-domain decisions with overlapping tags or identical parents and **flags for senior dev review.** The senior dev:

1. Picks which decision wins
2. The losing decision gets `status: superseded` and the winning decision lists it as context in `alternatives_rejected`
3. Both decisions remain in the timeline — history is preserved

Note: LLM-based semantic contradiction detection is deferred to Phase 5. v1 uses heuristic rules only.

### When senior dev review is required on main merge

Not every merge needs a senior dev. The rules:

| Situation | Who reviews | Why |
|---|---|---|
| Clean merge, no conflicts | Any developer | Routine |
| ID collision only | AI auto-resolves, developer verifies | Mechanical fix |
| Missing links suggested | Any developer | Low-risk suggestion |
| Contradiction detected | **Senior dev / tech lead** | Architectural decision needed |
| Domain split or rename | **Senior dev / tech lead** | Structural change to the system |
| Foundational decision (no parents, new domain) | **Senior dev / tech lead** | Sets direction for future decisions |

### merge_assist.py — What it does

```
Input:  Two sets of YAML files from conflicting branches
Output: One of:
  - Auto-resolved files (ID renumbering) + commit
  - Flag comment on the PR (same-domain parallel decisions)
  - Senior dev review tag (same-domain + overlapping tags/parents)

Steps:
  1. Parse all YAML files from both branches
  2. Detect ID collisions → auto-renumber
  3. Group by domain → detect same-domain parallel decisions
  4. For same-domain pairs, apply heuristic rules:
     - Different tags, no shared parents → likely independent, low-priority flag
     - Overlapping tags or shared parents → flag for review
  5. Output resolution actions
```

LLM-based semantic classification is a Phase 5 enhancement. v1 heuristics are sufficient for teams of 2-5 developers.

---

## 9. Python Tooling

### CLI: `context_cli.py`

The single entry point for all operations.

```bash
# Create a new decision (generates skeleton YAML)
python tools/context_cli.py new \
  --domain auth \
  --parent 2025-04-25-001 \
  --author human

# Validate all decision files
python tools/context_cli.py validate

# Rebuild graph.json, generated markdown, and static visualization
python tools/context_cli.py build

# Show current state of a domain
python tools/context_cli.py show auth

# Show full ancestry of a decision
python tools/context_cli.py ancestry 2025-05-02-001

# Point-in-time snapshot
python tools/context_cli.py snapshot --date 2025-04-28 --domain auth

# List unresolved tensions
python tools/context_cli.py tensions

# Show decisions by tag
python tools/context_cli.py search --tag jwt

# Show domain health (velocity, tension count, assumption depth)
python tools/context_cli.py health

# Detect drift (requires git history)
python tools/context_cli.py drift

# Assist with merge conflicts
python tools/context_cli.py merge-assist --branch feature-x --target main

# Agent briefing — compact dump for LLM context (used by AI agents before starting work)
python tools/context_cli.py agent-context --domain auth
```

### Tool modules

**`ingest.py`** — The core engine

- Reads all `context/timeline/*.yaml` files
- Validates each against `schema.json`
- Builds a `networkx.DiGraph` in memory
- Computes derived fields: `children` (reverse of `parents`), `inherited_assumptions` (recursive traversal)
- Detects cycles (rejects if found)
- Checks link integrity (all `parents` references resolve to existing files)
- Checks stale references (domain files referencing superseded decisions)
- Serializes to `context/graph.json`

**`validate.py`** — Schema + integrity

- JSON Schema validation of each YAML file
- ID matches filename check
- Date in ID matches `date` field check
- All parent IDs exist check
- No cycles check
- Status consistency: superseded nodes must have at least one child referencing them as parent

**`render.py`** — Generates readable outputs

- Reads graph from `ingest.py` output
- For each domain: filters active nodes, renders `context/current/{domain}.md`
- Collects unresolved tensions, renders `context/tensions/active.md`
- Collects resolved tensions, renders `context/tensions/resolved.md`
- Generates `context/context-graph.html` — static DAG visualization (SVG via graphviz + HTML wrapper)

**`graph_ops.py`** — Query engine

- All graph queries from Section 7 table
- `agent_context(domain)` — compact dump of domain state for LLM consumption
- Returns structured data (dicts/lists) that CLI formats for terminal or that a future frontend can consume as JSON

**`merge_assist.py`** — Multi-developer merge support

- Reads YAML files from two branches
- Detects and resolves ID collisions (auto-renumber)
- Flags same-domain parallel decisions for review (heuristic rules)
- Outputs actions: auto-fix or flag for human review

**`drift.py`** — Staleness detection

- Reads `context/drift-config.yaml` for per-domain tracked paths
- Checks git log for changes to tracked paths since last decision in that domain
- Reports domains where code changed but no decision was recorded

### Dependencies

```
# tools/requirements.txt
pyyaml>=6.0               # YAML parsing
networkx>=3.0             # graph operations
jsonschema>=4.0           # YAML schema validation
click>=8.0                # CLI framework
graphviz>=0.20            # DAG → SVG rendering for static visualization
```

Optional (for future interactive frontend):

```
streamlit>=1.30           # if Python frontend chosen
# OR no Python dep — export graph.json for a lightweight JS frontend
```

---

## 10. Enforcement Layer

### Primary Path: CI Pipeline (for AI Agent Commits)

AI agents produce 80%+ of commits. CI is the enforcement that matters most.

```yaml
name: Context Integrity
on: [pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r tools/requirements.txt

      - name: Validate all decision records
        run: python tools/context_cli.py validate

      - name: Build graph and check integrity
        run: python tools/context_cli.py build

      - name: Check for merge conflicts (multi-dev)
        if: github.event.pull_request.base.ref == 'main'
        run: python tools/context_cli.py merge-assist --branch ${{ github.head_ref }} --target main

      - name: AI commit enforcement
        run: |
          # If commit has [ai-commit], timeline/ must have changes
          AI_COMMITS=$(git log --oneline origin/main..HEAD | grep -c "\[ai-commit\]" || true)
          if [ "$AI_COMMITS" -gt 0 ]; then
            CONTEXT_CHANGES=$(git diff --name-only origin/main..HEAD | grep -c "^context/timeline/" || true)
            if [ "$CONTEXT_CHANGES" -eq 0 ]; then
              echo "✗ AI commits detected but no context updates. AI must include decision records."
              exit 1
            fi
          fi

      - name: Skip enforcement for context-only PRs
        run: |
          # If PR only touches context/ files, skip context-update requirement
          NON_CONTEXT=$(git diff --name-only origin/main..HEAD | grep -cv "^context/" || true)
          if [ "$NON_CONTEXT" -eq 0 ]; then
            echo "✓ Context-only PR — no code changes to document"
          fi
```

### Secondary Path: Git Hooks (for Human Commits)

Humans make occasional commits. Two hooks handle enforcement:

**`hooks/pre-commit`** — checks that context/timeline/ files are staged:

```bash
#!/bin/bash
CONTEXT_TOUCHED=$(git diff --cached --name-only | grep -c "^context/timeline/" || true)

if [ "$CONTEXT_TOUCHED" -gt 0 ]; then
  CHANGED_YAMLS=$(git diff --cached --name-only | grep "^context/timeline/.*\.yaml$")
  if [ -n "$CHANGED_YAMLS" ]; then
    python tools/context_cli.py validate --files $CHANGED_YAMLS
    if [ $? -ne 0 ]; then
      echo "✗ Decision record validation failed. Fix the YAML before committing."
      exit 1
    fi
  fi
  echo "✓ Context updated and valid"
  exit 0
fi

# No context touched — commit-msg hook will handle [no-decision] check
exit 0
```

**`hooks/commit-msg`** — checks for [no-decision] and logs to drift register:

```bash
#!/bin/bash
COMMIT_MSG_FILE="$1"
COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")

CONTEXT_TOUCHED=$(git diff --cached --name-only | grep -c "^context/timeline/" || true)

if [ "$CONTEXT_TOUCHED" -gt 0 ]; then
  exit 0  # already handled by pre-commit
fi

if echo "$COMMIT_MSG" | grep -q "\[no-decision\]"; then
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  BRANCH=$(git branch --show-current)
  AUTHOR=$(git config user.name)
  FILES=$(git diff --cached --name-only | head -5 | tr '\n' ', ')
  echo "{\"timestamp\":\"$TIMESTAMP\",\"author\":\"$AUTHOR\",\"branch\":\"$BRANCH\",\"files\":\"$FILES\"}" >> context/drift-register.jsonl
  git add context/drift-register.jsonl
  echo "⚠ No decision — logged to drift-register.jsonl"
  exit 0
fi

# Check if changes touch paths that require decisions (path-based triggering)
SIGNIFICANT=$(git diff --cached --name-only | grep -f <(python tools/context_cli.py tracked-paths 2>/dev/null) | wc -l || echo 0)
if [ "$SIGNIFICANT" -gt 0 ]; then
  echo "✗ Changes touch tracked paths but no decision record found."
  echo "  Options:"
  echo "    1. Add/update a file in context/timeline/"
  echo "    2. Add [no-decision] to your commit message (logged, reviewed weekly)"
  echo ""
  echo "  Quick start: python tools/context_cli.py new --domain <domain>"
  exit 1
fi

# Non-significant paths — no context required
exit 0
```

### Rules Summary

| Actor | Must update context? | Classification | Enforcement point |
|---|---|---|---|
| AI agent | **Must** for structural changes | `[ai-commit]` in message | CI hard block |
| Human (tracked path) | Must, or classify as no-decision | `[no-decision]` — logged, reviewed weekly | Git hooks + CI |
| Human (non-tracked path) | No | No tag needed | None |
| Merge to main | Validated | N/A | CI pipeline |
| Senior dev merge | Reviews flagged conflicts | Can override heuristic flags | PR review |

### Weekly Health Job

A weekly CI job runs `python tools/context_cli.py health` and posts a summary (Slack, email, or CI dashboard). This replaces the "context owner" role with a lightweight mechanism:

- Correlates code commits vs decision records (what changed without a decision?)
- Lists `[no-decision]` commits since last report (developer reviews, updates drift if needed)
- Reports orphaned tensions, stale domains, assumption depth
- Developer takes responsibility to act on findings

---

## 11. Frontend — Static Viz in Phase 2, Interactive Deferred

### Phase 2: Static HTML+SVG Graph (generated by `render.py`)

A static HTML file containing an SVG rendering of the DAG, generated during `python tools/context_cli.py build`. Zero infrastructure — open in a browser.

**What it shows:**

- DAG with nodes as circles/boxes, edges as arrows
- Color-coded: green = active, grey = superseded, red outline = has unresolved tensions
- Node labels: decision ID + first line of summary
- Filterable by domain (generated as separate SVG views per domain + one combined view)

**How it's built:**

- `networkx` exports the graph to `graphviz` DOT format
- `graphviz` renders to SVG
- Python wraps it in an HTML page with minimal CSS
- Output: `context/context-graph.html`
- Total: ~50-80 lines of code in `render.py`

### Interactive Frontend (deferred until schema is stable)

Built only after 4-6 weeks of real use with the static visualization.

**What the frontend will consume:**
`graph.json` + raw YAML files. Any frontend that can read JSON and YAML can render the system.

**Constraints:**

1. Must read from files, not a database.
2. Three views minimum: graph explorer, domain dashboard, timeline view.
3. Technology options (decided later):
   - **Lightweight JS:** Preact/Alpine + D3.js for graph rendering. Reads `graph.json` directly.
   - **Static HTML:** Python generates a richer HTML report with embedded JS for interactivity.
   - **Python:** Streamlit or Panel, if the team prefers staying in Python.

4. `graph.json` is the frontend's API. It contains everything needed to render any view. YAML files are only needed for full decision text (lazy-loaded on click).

---

## 12. Build Order

Ordered by dependency. Each step is usable independently — you don't need step 5 to get value from steps 1-4.

### v0.1 — Minimal Viable Context System (1 week build + 2 weeks manual use)

**Goal:** Prove the system works on real decisions before building tooling. If the schema is wrong, or the workflow doesn't fit, find out before writing 1000 lines of Python.

**Build (1 week):**

1. Create folder structure: `context/timeline/`, `context/current/`, `context/skills/`
2. Write `tools/schema.json` (JSON Schema for decision YAML validation, with `version` field)
3. Write `context/agent-rules.md` (how agents discover and use this system)
4. Write 3-5 **real** decision records from the current project (not examples — real decisions that exist today)
5. Write `tools/validate.py` — schema validation, ID-filename match, parent reference check
6. Write minimal CLI: `context_cli.py new` (generate skeleton YAML) + `context_cli.py validate` (run validator)

**Manual use (2 weeks):**

- Use the system manually. Write decisions, validate them, see what's awkward.
- No hooks, no CI, no graph engine, no rendering.
- Evaluate: Is the schema right? Is the workflow tolerable? Are decisions being written?

**Decision gate:** After 2 weeks, evaluate whether to proceed to Phase 2 or redesign.

### Phase 2: Graph Engine + Visualization (after v0.1 proven)

**Step 1: Ingest + graph builder (`ingest.py`)**

- Reads all YAML → builds `networkx.DiGraph`
- Computes children, inherited assumptions, summaries
- Cycle detection
- Outputs `graph.json` (with schema_version, stats, summaries)

**Step 2: Full CLI (`context_cli.py`)**

- `new` — generates skeleton YAML with auto-incremented ID for today
- `validate` — runs validator
- `build` — runs ingest + graph build + render
- `show <domain>` — prints active decisions for domain
- `ancestry <id>` — prints causal chain
- `agent-context <domain>` — compact LLM-friendly domain briefing
  - Supports query flags: `--fields` (filter output fields), `--depth` (limit graph traversal), `--format compact` (minimal output for context window efficiency)
  - Two-layer architecture: full YAML storage + filtered query interface
- `tracked-paths` — outputs configured paths that require decision records
- `health` — weekly health report (drift, staleness, orphaned tensions)

**Step 3: Static HTML+SVG visualization (in `render.py`)**

- `networkx` → graphviz DOT → SVG → HTML wrapper
- Generated as `context/context-graph.html` (gitignored, view locally)
- Color-coded by status, per-domain views

### Phase 3: Rendering + Intelligence

**Step 4: Domain renderer (full `render.py`)**

- Generates `context/current/*.md` from active leaf nodes per domain (committed)
- Generates `context/tensions/active.md` from unresolved tensions (gitignored, CI artifact)
- Domain files stop being handwritten from this point

**Step 5: Graph queries (`graph_ops.py`)**

- Point-in-time snapshots
- Domain velocity
- Coupling map
- Assumption depth analysis

**Step 6: Skill files**

- Write `_index.md` with short descriptions
- Write initial system skill files: `reviewer.md`, `context-owner.md`
- Project skills added as needed

### Phase 4: Multi-Dev + Drift + Enforcement

**Step 7: Git hooks**

- `hooks/pre-commit` — checks context/timeline/ staged, validates YAML
- `hooks/commit-msg` — checks `[no-decision]`, logs to drift-register.jsonl

**Step 8: Merge assist (`merge_assist.py`)**

- ID collision auto-resolution by author + relevance
- Same-domain parallel decision flagging (heuristic, no LLM)
- PR comment generation

**Step 9: Drift detector (`drift.py`)**

- Reads `drift-config.yaml`
- Compares git history against decision dates per domain
- Reports stale domains
- Evaluate necessity after 4 weeks of use

**Step 10: CI pipeline**

- Wire all tools into GitHub Actions / GitLab CI
- Validate on every PR
- Merge assist on PRs targeting main
- `[no-decision]` classification enforcement
- Publish gitignored files (`graph.json`, `tensions/*.md`, `context-graph.html`) as PR artifacts
- Weekly health job: `context_cli.py health`

### Phase 5: Interactive Frontend + LLM Enhancements (when ready)

**Step 11: Choose frontend technology and build**

- Only after 4-6 weeks of real use with static visualization
- Graph explorer, domain dashboard, timeline view
- Lightweight JS (Preact + D3) or Streamlit — decided based on team needs

**Step 12: LLM-enhanced merge classification**

- Semantic contradiction detection in merge-assist
- Only when heuristic flagging proves insufficient

---

## Quick Reference

### File naming

```
YYYY-MM-DD-NNN.yaml
2025-04-25-001.yaml     ← first decision on April 25
2025-04-25-002.yaml     ← second decision on April 25
```

### CLI cheat sheet

```bash
python tools/context_cli.py new --domain auth          # create decision
python tools/context_cli.py validate                    # check all files
python tools/context_cli.py build                       # rebuild graph + viz
python tools/context_cli.py show auth                   # current state
python tools/context_cli.py ancestry 2025-04-25-001     # why chain
python tools/context_cli.py tensions                    # tech debt
python tools/context_cli.py health                      # weekly health report
python tools/context_cli.py drift                       # stale domains
python tools/context_cli.py agent-context --domain auth # agent briefing
python tools/context_cli.py agent-context --domain auth --fields decision,assumptions --depth 2 --format compact
python tools/context_cli.py tracked-paths               # paths requiring decisions
```

### Commit conventions

```
Normal commit:       git commit -m "feat: add token refresh"
                     (must touch context/timeline/ or hook blocks)

No decision needed:  git commit -m "fix: typo in readme [no-decision]"
                     (logged to drift register)

AI commit:           git commit -m "feat: add RBAC middleware [ai-commit]"
                     (MUST include context/timeline/ change — CI blocks otherwise)
```

### Status values

- `active` — current truth, represents how the system works now
- `superseded` — replaced by a later decision, kept for history

### Minimum viable decision record

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
```
