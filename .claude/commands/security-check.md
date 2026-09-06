---
description: Targeted security review for Nidham's real risk areas
---

Run a focused security review. Delegate to the `security-reviewer` agent.

Scope: $ARGUMENTS (if empty, review the current `git diff`).

Check these in order — they are Nidham's actual attack surface, not a generic OWASP recital:

1. **Tenant isolation.** Every query against an operational table must be constrained by `company_id`. Any use of the `service_role` key bypasses RLS by design — flag every occurrence and confirm there is a `WITH CHECK` policy or an explicit company_id filter in the code path.
2. **RLS policies.** New or changed tables: is RLS enabled? Are there both USING and WITH CHECK clauses? Is there a policy that accidentally allows `true`?
3. **PII.** Salaries, national IDs, biometric records, contact details. Is anything new being logged, returned in an API response, or written to a report file unencrypted?
4. **Auth boundaries.** Route handlers and server actions: is the session checked before the data access, or after?
5. **Secrets.** Any key, token, or connection string in source, in a client component, or in a `NEXT_PUBLIC_` variable.
6. **Input.** User-supplied values reaching a query, a file path, or a shell command.

Report only real, reachable issues with the file and line. Do not pad the report. If something is a theoretical risk that is not reachable in this codebase, say that explicitly instead of listing it as a finding.
