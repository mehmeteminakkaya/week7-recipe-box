# Week 7 — Recipe Box Sprint: concurrent agents + a generator–critic loop

A small FastAPI + SQLite recipe service from the course starter. Two parts:

- **Part I — concurrency:** two independent tasks were implemented by **two agents running
  at the same time**, each in its own **git worktree**, then merged.
- **Part II — generator–critic loop:** a third task was built by a generator, reviewed by a
  separate critic against a written rubric, and revised until the critic signed off
  (two revision rounds + a sign-off round).

## Quickstart

```bash
pip install -r requirements.txt
python -m pytest          # 43 tests
uvicorn main:app --reload # http://localhost:8000/  (UI at /, docs at /docs)
```

Python 3.10+.

## Endpoints

Starter:

- `POST /recipes` `{ "title": ..., "ingredients": [...], "tags": [...] }`
- `GET /recipes`, `GET /recipes/{id}`

From Part I (tasks 1 and 2):

### `GET /shopping-list?ids=1,2,3` — task 1

Merges the ingredients of the requested recipes into `{"items": [...]}`: first-seen order,
de-duplicated case-insensitively while keeping the first spelling. Blank or non-integer
`ids` → 400; unknown ids → 404 naming them; repeated ids count once.

### `GET /recipes?tag=breakfast` — task 2

Filters the list by one **exact** tag, case-insensitively (`break` does not match
`breakfast`). No `tag` → unchanged list; blank tag → 400; a tag nobody has → `[]`.

From Part II (task 3):

### `GET /recipes/{id}/scaled?factor=2` — task 3

Returns the recipe with the leading quantity of each ingredient multiplied by `factor`.

- `factor` must be in `(0, 100]`; missing → 2; out-of-range, `inf`, `nan` or non-numeric →
  422.
- Arithmetic is `Decimal`, so `factor=1` is an identity and `1234567 × 2 = 2469134` (no
  `1e+06`, no 6-significant-digit truncation).
- A quantity is only scaled when it is a **standalone leading token** (a number followed by
  whitespace or the end of the string). `"1/2 cup"`, `"2,5 kg"` and `"200g flour"` are left
  untouched instead of being half-parsed.
- Unknown recipe → 404; nothing is persisted; the response shape matches `GET /recipes/{id}`.

## Part I — how the concurrency was run

```bash
git worktree add ../wt-task-a -b task/shopping-list
git worktree add ../wt-task-b -b task/tag-filter
# two agents started in the same minute, one per worktree
```

| Agent | Worktree / branch | Task | Commit | Merge |
| --- | --- | --- | --- | --- |
| A | `wt-task-a` / `task/shopping-list` | task 1, shopping list | `9fa4268` | `7722df7` |
| B | `wt-task-b` / `task/tag-filter` | task 2, tag filter | `74fbd36` | `411f7eb` |

Both agents edited `main.py`, but in different regions: A appended a new endpoint at the end
of the file, B modified the existing `list_recipes`. Both merges applied cleanly and the
suite went from 3 to 22 tests. The collision that *did* happen came later: Part II's branch
also appends at the end of `main.py`, and rebasing it onto the merged main conflicted exactly
there. See [`writeup.md`](writeup.md) for the concurrency notes and risks.

## Part II — how the loop was run

- `docs/RUBRIC.md` — five axes (correctness, edge cases, tests, clarity, API shape) and the
  exact verdict format (`SIGN OFF` / `REVISE: …`).
- The critic was a separate agent with read-only access: it saw the diff, the spec and the
  rubric, never the generator's intentions, and never edited code.
- Rounds: v1 → critic round 1 (**REVISE**, 4 findings) → v2 → round 2 (**REVISE**, 2
  mutation-surviving test gaps, no source defect) → v3 → round 3 (**SIGN OFF**).

Transcripts are in [`docs/transcripts/`](docs/transcripts/).

## Layout

```
main.py                     app: starter + shopping list + tag filter + scaling
tests/test_shopping_list.py  agent A's tests (11)
tests/test_tag_filter.py     agent B's tests (8)
tests/test_scaling.py        generator–critic task's tests (21)
test_main.py                 starter tests
conftest.py                  per-test SQLite isolation
docs/TASKS.md                course task list
docs/RUBRIC.md               critic rubric
docs/transcripts/            agent reports and critic rounds, verbatim
writeup.md                   concurrency notes, loop transcript, autonomy, lessons
```
