# Skill: Reviewer

## Role

You are reviewing a pull request that includes decision records.

## When This Skill Is Loaded

- PR review that includes `.cortex/timeline/*.yaml` changes
- Reviewing AI-authored decision records for accuracy
- Checking whether a code change needs a decision record

## Criteria

### Decision Record Quality

- [ ] `decision` is concrete and specific (not vague or aspirational)
- [ ] `context` explains the problem or situation, not just the solution
- [ ] `assumptions` are stated (not left empty)
- [ ] `alternatives_rejected` lists what was considered (for non-trivial decisions)
- [ ] `tensions` flags anything this makes unstable
- [ ] `parents` links to the causally relevant prior decisions
- [ ] `domains` correctly identifies all affected domains

### Cross-Reference Integrity

- [ ] Parent decisions exist and are relevant
- [ ] If this supersedes a prior decision, the parent's status should be updated
- [ ] Tensions from parent decisions are either resolved or carried forward

### Decision Necessity

- [ ] This change warrants a decision record (not a routine bug fix or refactor)
- [ ] The decision is at the right granularity (not too broad, not too trivial)
- [ ] Reviewers CAN reject records that aren't decision-worthy — this is curation

## Output Format

PR review comments on the decision record files, with specific feedback per field.
