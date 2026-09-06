---
description: Code review on the current diff only
---

Review the current uncommitted changes. Delegate to the `code-reviewer` agent.

Scope: run `git diff` and `git diff --staged`. Review ONLY what appears there. Do not review the whole codebase, do not comment on files you were not shown.

Report findings in three buckets, in this order:
- **لازم يتصلح** — bugs, security holes, data-loss risks, broken types
- **يُفضّل** — real maintainability problems worth fixing now
- **ملاحظة** — everything else, one line each, no lecturing

For each finding: the file and line, what is wrong, and the concrete fix. No praise, no summary of what the code does. If the diff is clean, say so in one sentence.
