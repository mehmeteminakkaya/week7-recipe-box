# Week 7 writeup — two agents in parallel, then a generator–critic loop

Three independent tasks from `docs/TASKS.md` were done in two very different ways. Part I ran
two agents **at the same time** in separate git worktrees on tasks 1 and 2. Part II ran task 3
through a **generator–critic loop** with a written rubric and three critic rounds. Everything
is merged into `main`; 43 tests pass.

## Part I — concurrent agents

### Setup

```bash
git worktree add ../wt-task-a -b task/shopping-list
git worktree add ../wt-task-b -b task/tag-filter
```

Two agents were started in the same minute, one per worktree, each with the task text, the
repo context and three rules: stay inside your worktree, put your tests in a **new** file
(never `test_main.py`), and do not push, merge, rebase or touch the other branch. Neither
agent could see the other's work, and neither knew which task the other had.

| | Agent A | Agent B |
| --- | --- | --- |
| Task | 1 — shopping list (`GET /shopping-list?ids=…`) | 2 — tag filter (`GET /recipes?tag=…`) |
| Worktree | `wt-task-a` | `wt-task-b` |
| Branch | `task/shopping-list` | `task/tag-filter` |
| Commit | `9fa4268` | `74fbd36` |
| Merge | `7722df7` | `411f7eb` |
| Tests added | 11 | 8 |

Both reports are verbatim in [`docs/transcripts/part-i-agent-reports.md`](docs/transcripts/part-i-agent-reports.md).

### Did they collide?

Not with each other, and the reason is structural rather than lucky:

- **Different regions of the same file.** A appended a new endpoint at the end of `main.py`
  (+65 lines, zero existing lines changed); B changed the signature and body of the existing
  `list_recipes` (+16/−2). Git merged both cleanly.
- **Different test files.** Both were told to create `tests/test_<task>.py`; `test_main.py`
  stayed untouched. Test collisions would have been the most likely conflict.
- **One database each.** `DB_PATH` is relative to `main.py`, so each worktree has its own
  `recipes.db`; the per-test `conftest.py` fixture then gives every test a temp file. Two
  agents running `pytest` at once never share state.

The collision that *did* happen came later, from Part II: its branch also appends at the end
of `main.py`, and rebasing it onto the merged `main` produced a real conflict exactly there —
both sides added a preamble (`_today`, imports) at the same anchor. Resolved by keeping one
copy of the preamble and both endpoints. **Lesson:** "independent features" does not mean
"independent diffs"; two tasks that both append at EOF will conflict even when their
behaviour does not overlap. The worktree isolation protects the working tree, not the merge.

### Autonomy and supervision

- Each agent had **full autonomy inside its worktree**: read the code, choose the design,
  write the endpoint and tests, run `pytest`/`black`/`ruff`, and commit. No human steering
  between start and report.
- Neither had **write access beyond its branch**: no push, no merge, no rebase, no edits
  outside its worktree.
- I acted as the only integrator: read both diffs line by line, re-ran each worktree's suite
  (11 and 8 new tests), then merged each with `--no-ff` and re-ran the full suite on the
  merged tree (22 passed). Both agents' contracts were honoured as written; the two
  ambiguities they resolved themselves (`ids=1,,2` → 400, strip tag before matching) were
  checked and kept.

## Part II — generator–critic loop

### The loop

| Round | Artifact | Verdict | What changed |
| --- | --- | --- | --- |
| generator v1 | `745fb0f` | — | 3 tests, `%g` formatting, no factor validation, half-parsed "1/2 cup" |
| critic round 1 | [`round-1-critic.md`](docs/transcripts/round-1-critic.md) | **REVISE** (4 findings) | — |
| generator v2 | `e613673` | — | `Decimal` arithmetic, `Query(2, gt=0, le=100)`, standalone-token lookahead, 19 tests |
| critic round 2 | [`round-2-critic.md`](docs/transcripts/round-2-critic.md) | **REVISE** (no source defect; 2 mutation-surviving test gaps) | — |
| generator v3 | `78a5330` | — | end-of-string and fractional-factor tests added |
| critic round 3 | [`round-3-critic.md`](docs/transcripts/round-3-critic.md) | **SIGN OFF** | docstring nit fixed, merged `76bd3c1` |

The rubric ([`docs/RUBRIC.md`](docs/RUBRIC.md)) is what made the loop terminate: each axis is
PASS/FAIL with evidence, and the verdict is a single line. Without it the critic could always
produce "one more finding"; with it, a PASS on all five axes plus no blocking finding is a
defined exit.

### What the critic caught that I would have shipped

- **`%g` silently broke the contract.** Scaling by 1 rendered `1000000` as `1e+06` and
  `1234567 × 2` as `2.46913e+06`. The happy-path tests (small integers, factor 2) never saw
  it.
- **No bound on `factor`.** `factor=0` returned `"0 g flour"`, `-1` returned a negative
  quantity, `inf`/`nan` produced literal `"inf g flour"`. FastAPI's `Query` constraints fixed
  it in three characters.
- **Half-parsing corrupted real recipes.** My v1 regex saw the `1` in `"1/2 cup milk"` and the
  `2` in `"2,5 kg salt"` and produced `"2/2 cup milk"` / `"4,5 kg salt"`. The fix was to make
  the rule explicit — a quantity is only a quantity when it stands alone — and to document
  what is *not* scaled.
- **Two test gaps that survived mutation.** Round 2 deleted the `|$` branch of the lookahead
  and swapped `Decimal(str(factor))` for `Decimal(factor)`; all 41 tests stayed green. Round 3
  re-ran both mutations and confirmed exactly one test fails for each. That is the difference
  between "tests pass" and "tests protect the behaviour".

### Autonomy and supervision

- **Generator:** full write access to `main.py` and its test file, no access to the rubric
  beyond reading it, and no ability to approve its own work.
- **Critic:** read-only, rubric-bound, blind to the generator's reasoning (it was told to
  judge the diff, not the author). It ran its own probes and mutations; it never edited code.
- **Human (me):** decided which findings to fix, which to defer (none were rejected this
  round), and merged. The critic's "at least log the skipped rows" style suggestions were
  weighed and implemented as documentation instead of code where a log would not change
  behaviour.

## What I learned

Running agents concurrently is mostly an exercise in **bounding their blast radius**: the
worktrees, the separate test files and the no-push rule did the real work, and the merge was
boring until a branch touched the same anchor as another. The generator–critic loop was the
more surprising half: a critic that can *run mutations* is qualitatively different from one
that reads a diff, because it asks whether the tests would notice a regression — which is the
question I usually skip when I am the one who wrote them. And the rubric mattered more than the
model: five explicit axes turned "review this" into a decision I could act on, and made the
loop stop at a defined point instead of running forever. I will keep the worktree + separate
test file convention for any parallel agent work, and I will keep a written sign-off rubric for
anything a second model reviews.
