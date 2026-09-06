---
description: Failing test first, then the smallest code that passes it
---

Implement the following using strict TDD. Delegate to the `tdd-guide` agent.

Task: $ARGUMENTS

Rules (do not skip a step, do not reorder):
1. Write ONE failing test that describes the desired behaviour. Show it to the user.
2. Run the test. Confirm it fails for the right reason (not a typo, not a missing import).
3. Write the smallest amount of production code that makes it pass. No extra features, no speculative abstraction.
4. Run the test again. Confirm it passes.
5. Refactor only if there is real duplication. Re-run tests after.
6. Repeat from step 1 for the next behaviour.

If the task has no testable behaviour (pure styling, copy change, config), say so plainly and switch to a normal edit — do not fake a test.

For Nidham specifically, tests must cover the multi-tenant case: a row belonging to company A must never be readable or writable from company B's session.
