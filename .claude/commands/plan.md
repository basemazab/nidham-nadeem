---
description: Write a reviewable plan before any code is touched
---

Plan the following task. Do NOT write or edit any code in this turn.

Task: $ARGUMENTS

Steps:
1. Read only the files you actually need to understand the current behaviour. Name each file you read and why.
2. State the goal in one sentence, in the user's own terms.
3. List what you are NOT going to change (scope fence).
4. Produce the plan as numbered steps. For each step: the file(s) touched, what changes, and how it will be verified.
5. Call out risks explicitly, especially:
   - anything touching `company_id`, RLS policies, or the service_role key
   - anything touching payroll calculation, tax rates, or social insurance
   - anything that changes an existing database column or migration
   - anything that changes RTL/Arabic rendering
6. List open questions you need answered before starting.

End with: "اكتب /tdd أو وافق على الخطة عشان أبدأ" and stop. Do not start implementing.
