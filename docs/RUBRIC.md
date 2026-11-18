# Critic rubric — generator–critic loop

The critic reviews the diff and the tests against these five axes. Every axis gets
**PASS** or **FAIL** with one line of evidence (file:line or test name). The verdict is the
last line of the review:

- `SIGN OFF` — every axis PASS, no blocking findings.
- `REVISE: <numbered findings>` — otherwise, each finding phrased as a change the
  generator can act on.

## Axes

1. **Correctness** — the endpoint does what `docs/TASKS.md` says, with the documented
   rounding/edge behaviour. Check the spec line by line, not the implementation's
   intentions.
2. **Edge cases and error handling** — unknown id, missing/blank parameter, out-of-range
   value, input that does not match the expected pattern. Every one must have a defined
   answer and a test.
3. **Tests** — each risky branch has a test that fails when the code is wrong (not a test
   that just calls the happy path). Assertions are specific.
4. **Clarity** — names say what they do, the function is small, the docstring states the
   contract. A reader should not need the tests to understand the endpoint.
5. **API shape** — status codes and JSON match the rest of the app (`404 unknown recipe`,
   `{"id", "title", ...}`), and the change does not alter existing endpoints' behaviour.

## Rules for the critic

- Judge the diff, not the author. No praise padding: a PASS needs evidence.
- Do not propose rewrites beyond the finding; the generator decides how to fix.
- If a finding contradicts the written spec, quote the spec line.
- The critic never edits code.
