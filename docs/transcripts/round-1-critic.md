# Part II — generator–critic loop, round 1 (critic verdict: REVISE)

Critic: a separate agent, read-only, given the diff, `docs/TASKS.md` and
`docs/RUBRIC.md`. It did not see the generator's intentions. Verbatim verdict below.

---

**CRITIC VERDICT: REVISE** (worktree `wt-task-c`, branch `task/scaling`; suite 6/6 passes:
3 existing + 3 new).

**Axis 1 Correctness — FAIL.** `main.py:106` formats with `f"{amount:g}"` (6 significant
digits). Probe with temp DB: factor=1 turns `"1000000 g water"` → `"1e+06 g water"` and
`"123.4567 g yeast"` → `"123.457 g yeast"`; factor=2 turns `"1234567 g rice"` →
`"2.46913e+06 g rice"` (2469130, loses 4). Scaling by 1 is not identity.

**Axis 2 Edge cases — FAIL.** `main.py:110` puts no constraint on factor. factor=0 → 200
`["0 g flour", "0 eggs"]`, factor=-1 → `"-200 g flour"`, factor=inf → `"inf g flour"`,
factor=nan → `"nan g flour"`. `"1/2 cup milk"` → `"2/2 cup milk"`; `"2,5 kg salt"` →
`"4,5 kg salt"`. Omitted factor defaults to 2 (returns 2x); blank factor → 422. Neither
default nor blank has a test.

**Axis 3 Tests — FAIL.** `tests/test_scaling.py:19-36` only covers factor=2 happy path,
no-quantity pass-through, and 404 status. Missing: default factor, factor=0/-1/inf/nan,
factor=abc/blank 422 body, decimal/precision formatting, fraction/comma inputs, id/title/tags
preservation, and proof that `GET /recipes/{id}` is unchanged after scaling. 404 test does not
assert detail.

**Axis 4 Clarity — PASS.** `main.py:100-106` is a small helper with a docstring example;
`main.py:29` named regex constant; endpoint docstring `main.py:111`.

**Axis 5 API shape — PASS.** Response keys id/title/ingredients/tags match
`GET /recipes/{id}` (probe; `_row_to_recipe` reused `main.py:116`); 404 detail "unknown
recipe" matches `main.py:96/115`; diff only adds a route and existing tests still pass.
factor=abc → 422 FastAPI default list-detail, consistent with the existing POST validation
path (but untested).

**REVISE:**
1. Validate factor (reject non-finite and <=0 or define an allowed range) with the app's
   error shape; test 0/-1/inf/nan.
2. Stop using `%g` formatting; emit exact plain decimals so factor=1 is identity and
   1234567x2 = 2469134; test large/precise quantities.
3. Do not corrupt `"1/2 cup"` / `"2,5 kg"`: treat non-standalone leading tokens as unchanged
   or support them; test.
4. Add tests for omitted factor (=2), blank/non-numeric factor 422 body, 404 detail, and
   id/title/tags preservation with no persistence.
