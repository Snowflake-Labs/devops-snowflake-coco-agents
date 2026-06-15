# Issue Scoring

Every finding from a scan is scored on three dimensions before a fix decision is made.

## Dimensions

| Dimension | Values | What it measures |
|-----------|--------|-----------------|
| **SEVERITY** | critical / high / medium / low | How dangerous is this issue if left unfixed |
| **COMPLEXITY** | high / medium / low | How much code changes, how many files, how deep the logic change |
| **CONFIDENCE** | high / medium / low | How certain the AI is about the correct fix |

### Complexity definitions

| Level | Criteria |
|-------|----------|
| low | Single file, 1–5 lines changed, no branching logic change |
| medium | 1–2 files, 5–20 lines, or conditional logic change |
| high | 3+ files, 20+ lines, or architectural/async change |

## Routing policy

| Ceiling | Auto-fix when | Otherwise |
|---------|--------------|-----------|
| `off` | Never | Always `needs-review` |
| `conservative` | SEVERITY=low AND COMPLEXITY=low AND CONFIDENCE=high | `needs-review` |
| `aggressive` | CONFIDENCE >= medium | `needs-review` |

## What appears in the issue

Every issue body ends with a scoring footer:

```
---
_Severity: HIGH | Complexity: LOW | Confidence: HIGH | Fix mode: auto_
```

For `needs-review` issues:

```
---
_Severity: HIGH | Complexity: HIGH | Confidence: MEDIUM | Fix mode: needs-review_
_To trigger fix: comment `@coco fix` on this issue._
```

## Labels applied

| Decision | Labels |
|----------|--------|
| auto-fix | `coco:auto-fix` + `coco-agent` + `coco-agent-security` or `coco-agent-correctness` |
| needs-review | `coco:needs-review` + `coco-agent-security` or `coco-agent-correctness` |
