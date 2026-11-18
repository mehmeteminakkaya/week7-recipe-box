# Part I — agent reports (verbatim)

Two agents were started in the same minute, each in its own worktree, each given one task
and told not to push, merge or touch the other worktree. These are their closing reports,
lightly trimmed of tool narration; the content is unchanged.

## Agent A — task 1, shopping list (`wt-task-a`, branch `task/shopping-list`)

> Task 1 (shopping list) complete — worktree branch `task/shopping-list`, commit `9fa4268`
> ("feat(shopping-list): merge and de-duplicate ingredients for requested recipes"). Not
> pushed; no merge/rebase.
>
> **Files changed:** `main.py` (append-only, +65 lines after `get_recipe`; zero existing
> lines modified); `tests/test_shopping_list.py` (new file, 11 tests). `test_main.py`
> untouched.
>
> **Final test count:** 14 passed (3 existing + 11 new).
>
> **Contract implemented:** `GET /shopping-list?ids=1,2,3` → 200 `{"items": [...]}`:
> ingredients in first-seen order across recipes in the order given, de-duplicated
> case-insensitively (casefold) keeping the first spelling; duplicate/whitespace-padded ids
> count once. Missing or blank ids → 400. Non-integer token → 400 naming it. Unknown ids →
> 404 `"unknown recipe ids: 9"`, in first-seen order. Integer ids outside SQLite's 64-bit
> range are classified as unknown → 404 (no 500). Existing endpoints untouched.
>
> **Ambiguities resolved:** `ids=1,,2` (empty token inside a non-blank list) → 400 rather
> than silently skipping; out-of-range integers → 404 rather than 400 since they are
> integers; token whitespace stripped, ingredient strings stored as-is.
>
> **Risk/note:** route appended after `/recipes/{recipe_id}` and does not collide.

## Agent B — task 2, tag filter (`wt-task-b`, branch `task/tag-filter`)

> Task 2 (tag filter) complete — worktree branch `task/tag-filter`, commit `74fbd36`. Not
> pushed/merged.
>
> **Files changed:** `main.py` (existing `list_recipes` only; +16/−2);
> `tests/test_tag_filter.py` (new, 8 tests). `test_main.py` and `conftest.py` untouched.
>
> **Contract implemented:** `list_recipes(tag: str | None = None)`. No `tag` param → all
> recipes, unchanged JSON list, `ORDER BY id`. `?tag=breakfast` → exact case-insensitive
> match against parsed JSON tags; only matching recipes, original id order, same JSON shape.
> Blank or whitespace-only `?tag=` → 400 `{"detail": "tag must not be blank"}`. Unknown tag
> → 200 `[]`. `?tag=break` → `[]` (exact equality, casefold; no substring).
>
> **Ambiguity resolved:** nonblank query values are stripped before matching; documented in
> the endpoint docstring.
>
> **Tests:** 11 passed (3 starter + 8 new).
>
> **Collision avoidance:** only modified the existing `list_recipes` block mid-file; no code
> appended at end of `main.py`, no shared edits to `test_main.py`, dedicated new test
> filename.

## Supervisor checks

After each report: read the diff, ran the worktree's suite, then merged into `main` with
`--no-ff` and re-ran the full suite on the merged tree (22 passed). Neither merge conflicted;
the two edits landed in different regions of `main.py`.
