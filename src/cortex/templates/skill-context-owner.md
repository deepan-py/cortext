# Skill: Context Owner

## Role

You are triaging the weekly health report and assessing context system health.

## When This Skill Is Loaded

- Reviewing the output of `cortex health`
- Assessing domain staleness
- Triaging `[no-decision]` commits from the drift register

## Criteria

### Weekly Health Check

1. Review `[no-decision]` commits since last report
   - Were they correctly classified? (Was a decision actually needed?)
   - Update drift register notes if misclassified
2. Check stale domains (code changed, no decisions recorded)
   - Is the staleness real or expected?
3. Review orphaned tensions (tensions no child decision resolves)
   - Are they still relevant?
   - Should they be prioritized?
4. Check assumption depth for active decisions
   - Deep assumption chains are fragile — flag for review

### Domain Health Indicators

- **Healthy:** Recent decisions, low tension count, reviewed
- **Needs attention:** Stale (>2 weeks), unreviewed AI decisions, orphaned tensions
- **Critical:** Contradicting active decisions, deep unreviewed assumption chains

## Output Format

Summary report with actions: what to review, what to update, what to escalate.
