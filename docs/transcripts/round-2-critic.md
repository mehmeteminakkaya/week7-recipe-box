# Part II — generator–critic loop, round 2 (critic verdict: REVISE, tests only)

The generator's v2 addressed all four round-1 findings. The critic re-verified each one
against the new code and ran its own probes; this round found **no source defect**, only two
gaps that a mutation would survive. Verbatim verdict below.

---

**CRITIC round 2 — task #3 "Ingredient scaling"** (branch `task/scaling`, 2 commits). Ran
`pytest -q`: 41 passed (19 in `tests/test_scaling.py`). No source edits.

**Round-1 findings, verified against the new code:**

1. **`%g` identity/truncation — RESOLVED:** Decimal + `format(..., 'f')` (`main.py:192-193`);
   `tests/test_scaling.py:34-48` assert factor=1 preserves `"1000000"` / `"123.4567"` and
   factor=2 scales a 7-digit number exactly.
2. **factor validation — RESOLVED:** `Query(2, gt=0, le=100)` (`main.py:197`); 0/-1/101/inf/nan
   → 422 (`tests/test_scaling.py:83-87`); I also got 422 for `"2abc"`, `"NaN"`, `"1e-999"`,
   `"100.0001"`.
3. **"1/2 cup" / "2,5 kg" — RESOLVED:** standalone-token lookahead (`main.py:33`) leaves them
   untouched; `tests/test_scaling.py:67-80`.
4. **missing tests — RESOLVED** for the five named cases (default 28-31, 422 83-97, 404
   detail 100-104, shape 107-116, no persistence 119-124). Two residual coverage gaps remain
   (below).

**1. Correctness — PASS** — `TASKS.md:8-9` met: `_scale_ingredient` scales the leading
standalone quantity with Decimal (`main.py:181-193`) and `scale_recipe` returns the recipe
with scaled ingredients (`main.py:209`); probed `factor=0.1` on `"0.1 kg sugar"` → `"0.01 kg
sugar"`, `factor=0.333` on `"100 g flour"` → `"33.3 g flour"`, `"0.001 g"` × 0.1 → `"0.0001
g"`, factor=1 keeps `"1000000"` / `"123.4567"`.

**2. Edge cases and error handling — PASS** — unknown id → 404 `{"detail":"unknown recipe"}`
(`tests/test_scaling.py:100-104`, same detail as `get_recipe` at `main.py:112/207`); factor
omitted → 2 (28-31); 0/-1/101/inf/nan → 422 (83-87); `"abc"`/blank → 422 with detail (90-97);
I also probed `"2abc"`/`"NaN"`/`"1e-999"`/`"100.0001"` → 422, and signed (`"-5 g"`, `"+5 g"`),
whitespace-only and empty ingredients are returned unchanged with no exception; bare `"200"`
→ `"400"`.

**3. Tests — FAIL** — no test puts the quantity at end of string (every quantity test has a
unit after the number: `tests/test_scaling.py:20-56`) and no test uses a fractional factor
(only 1/2/3: 34-56), so deleting the `|$` from `_QUANTITY` (`main.py:33`) or replacing
`Decimal(str(factor))` with `Decimal(factor)` (`main.py:192`) leaves all 41 tests green — I
simulated both; the latter renders `"0.01000000000000000055511151231"` for factor=0.1.

**4. Clarity — PASS** — `scale_recipe`/`_scale_ingredient`/`_QUANTITY` names are clear;
docstrings (`main.py:181-188`, `main.py:198-203`) state the token rule, the (0,100] range,
the 422 path and no persistence; the helper is small.

**5. API shape — PASS** — reuses `_row_to_recipe` and matches `get_recipe`'s 404 detail
(`main.py:112` vs `main.py:207`); shape and no-persistence tests (`tests/test_scaling.py:107-124`);
diff adds only the endpoint + imports, existing endpoints unchanged.

**REVISE:**
1. Add a test for the end-of-string boundary — POST `"200"`, GET `?factor=2` → `["400"]` — so
   the `(?=\s|$)` `$` branch documented at `main.py:30-33` is covered.
2. Add a test with a fractional factor (e.g. `?factor=0.1` on `"0.1 kg sugar"` → `"0.01 kg
   sugar"`, or `?factor=0.333` on `"100 g flour"` → `"33.3 g flour"`) so the
   `Decimal(str(factor))` exactness at `main.py:192` is pinned.
