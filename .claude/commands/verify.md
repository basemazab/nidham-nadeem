---
description: Prove it works before calling it done
---

Verify the current state of the work. Do not fix anything in this turn — report only.

Run, in order, and show the real output of each:
1. `npx tsc --noEmit`
2. `npm run lint`
3. `npm run test`

Then produce a manual checklist for anything the automated checks cannot catch:
- Does the Arabic/RTL layout still render correctly?
- Was any payroll or tax number changed? If so, state the old value, the new value, and the legal source.
- Was any migration added? If so, is it reversible?
- Does the feature behave correctly for a company with zero employees, and for one with 500?

Finish with a one-line verdict: **جاهز** or **مش جاهز — والسبب**.

If a command fails, stop and report the failure. Do not attempt a fix unless asked.
