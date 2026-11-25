<!-- Output of the linus-review skill (classic mode) on examples/taskq/change.diff, run by Claude Opus on 2026-11-25. Unedited. -->

## Verdict: do not merge. Flipping the default from CSV to JSON breaks the README's own `taskq export > tasks.csv`.

### 1. Default format flipped from CSV to JSON   [reject]
`taskq/export.py:60`
```
-def run(tasks, fmt="csv", out=sys.stdout, upload_to=None, token=None, path=None):
-    """`taskq export [--format csv|json]`. CSV is the default."""
+def run(tasks, fmt="json", out=sys.stdout, upload_to=None, token=None, path=None):
```
Hell no. Every `taskq export` without a format, and every `run()` call without one, now gets JSON instead of the CSV it got yesterday. The README still says CSV is the default. Its own example, `taskq export > tasks.csv`, now writes JSON into a file called `.csv`, and whatever reads that file falls over. The test that pinned the old behaviour wasn't fixed, it was *rewritten to agree*. And the commit message doesn't say a word about any of it.

You do NOT change a default that people's scripts depend on. Put back `fmt="csv"`, the "CSV is the default." docstring and `test_csv_is_default`. `--format json` already exists. Anyone who wants JSON as their own default gets a new opt-in (a config key or an environment variable), not everybody's output silently swapped.
Principle: Behaviour users depend on is the contract (`references/compat.md` #1); New behaviour needs a new opt-in, not a changed default (`references/compat.md` #2); basis: his words about the kernel ABI, syscall flags and git; the transfer to a CLI is close.
"If it used to work, it should continue to work, even if it wasn't _meant_ to work." (2008-06-24)

### 2. `upload()` now reports every failure as success   [reject]
`taskq/export.py:50`
```
    for attempt in range(5):
        try:
            ...
        except Exception:
            time.sleep(2)
```
Ugh. This isn't a retry, it's a way to make upload failures *invisible*. After five failures the loop ends and the function returns `None`, the same thing it returns on success. A 401 from a stubbed `requests.put`: five attempts, no exception. A missing file, or the `path=None` that `run()` hands over by default: swallowed, five 2-second sleeps, "done". It's like a smoke alarm that beeps five times and then decides the house is fine. Expired token, wrong URL, no file at all, and CI stays green with nothing uploaded. That is f\*cking broken. It also retries 401s, 404s and `FileNotFoundError`, none of which will ever succeed, and it sleeps after the last attempt as well.

"Flaky in CI". Flaky *how*? Find that out first. If it really is a transient network or server error, retry exactly that error and let everything else raise, including the last failure. Something like this (untested):
```python
def upload(path, url, token):
    for attempt in range(3):
        with open(path, "rb") as fh:
            try:
                resp = requests.put(url, data=fh, headers={"Authorization": f"Bearer {token}"}, timeout=30)
            except requests.ConnectionError:
                if attempt == 2:
                    raise
                time.sleep(2)
                continue
        if resp.status_code < 500 or attempt == 2:
            resp.raise_for_status()
            return
        time.sleep(2)
```
Then make the comment name the CI failure the retry waits out.
Principle: Fix the root cause; delays, retries and special cases need a reason (`references/robustness.md` #7); Check the errors that matter (`references/robustness.md` #4); basis: his words; the retry part rests on about seven remarks, so treat it as a strong default.
"We don't "fix" things by papering over some symptom. We try to fix the _actual_ underlying problem." (2017-08-15)

### 3. JSON output turns missing fields from `null` into `""`   [reject]
`taskq/export.py:30`
```
        return [{k: t.get(k, "") for k in FIELDS} for t in tasks]
```
So the "refactor" also changes the JSON. The old writer used `t.get(k)`, and a task without `due` came out as `"due": null`. Now it comes out as `"due": ""`. Checked: `{'id': 1, 'title': 'x'}` gives `null` before and `""` after. Every `jq 'select(.due == null)'` and every `if task["due"] is None` downstream quietly stops matching. An empty CSV cell and a JSON null are *different things*. Forcing both through one shared helper is exactly what broke this.

JSON gets its own rows:
```python
json.dump([{k: t.get(k) for k in FIELDS} for t in tasks], out, indent=2)
```
Principle: Behaviour users depend on is the contract (`references/compat.md` #1); Share the same concept, separate different ones (`references/taste.md` #8); basis: his words (kernel ABI and git; the transfer to a CLI is close).
"it's a lot better to have the same (simple) code duplicated five times than it is to make a (much more complex) interface to have things shared." (2005-01-27)

### 4. The commit fails its own test suite   [reject]
`tests/test_export.py:17`
```
    assert out.getvalue() == "id,title,state,due\n"
```
This doesn't pass its own tests. `python3 -m pytest -q` gives 1 failed, 1 passed. The old code wrote the empty-list header by hand with `"\n"`. `csv.DictWriter.writeheader()` ends it with `"\r\n"`, so `run([], fmt="csv")` now gives `'id,title,state,due\r\n'`. This exact test was edited in this exact commit and it fails, so nobody ran it. Anything comparing an empty export byte for byte, or splitting it on `"\n"`, gets a different file.

Run the tests before sending. Then pick one:
- keep the old empty-list bytes by restoring the branch, or
- if CRLF everywhere is the goal (non-empty CSV already is CRLF), do that in its own commit that changes the test and says why.

Principle: Testing claims must be real (`references/patches.md` #6); Behaviour users depend on is the contract (`references/compat.md` #1); basis: his words.

### 5. The message calls two behaviour changes a "refactor"   [reject]
`d959416`
```
refactor exporter, fix upload
```
That message is bogus. The commit does four things: a class and registry rewrite, a new default format (#1), different JSON output (#3) and a retry loop (#2). The message names two of them, explains neither, and calls a change with visible output differences a refactor. Whoever bisects the CSV breakage gets no hint that it's in here.

Split it into two commits:
- the refactor alone, with byte-identical output and the tests left alone;
- the upload change alone, saying what fails in CI and why a retry is the answer.

The default change doesn't come back at all (#1).
Principle: The message explains why, and matches the diff (`references/patches.md` #1); One logical change per commit (`references/patches.md` #3); basis: his words.

### 6. A registry and an abstract base class for two fixed formats   [rework]
`taskq/export.py:11`
```
EXPORTERS = {}

def register(name):
...
class BaseExporter(abc.ABC):
    """Base class for all exporters. Subclass and register to add a format."""
```
Quite frankly, this is a plug-in framework for two formats and one caller. `run()` is the only user, the formats are the same two as before, and the old if/elif did the job in six lines. The docstring now invites outside code to subclass and register. The day someone does, `BaseExporter`, `rows()` and `register` are an interface that has to be kept forever. The shared `rows()` this machinery brought along is also what broke #3.

If you want a lookup table, use plain functions (untested):
```python
WRITERS = {"csv": write_csv, "json": write_json}
...
    writer = WRITERS.get(fmt)
    if writer is None:
        raise SystemExit(f"unknown format: {fmt}")
    writer(tasks, out)
```
Principle: No generic machinery for one caller (`references/design.md` #2); basis: inferred from what he said about kernel code.

### Not checked
- The CLI entry point is not in this repository. Check what `taskq export` passes as `fmt`. It is `reject` as long as the CLI or any caller of `run()` uses the default. If the CLI passes `"csv"` explicitly and nothing else relies on the default, #1 drops to `grumble`: a misleading library default.
- Whether real tasks ever lack `state` or `due` (#3). If every task always has all four keys, no output changes and #3 drops to `rework` under `taste.md` #8.
- `upload()` was only tried against a stubbed `requests.put`, never a real server. The CI failure it targets is not described anywhere in the repository.
- Whether anything reads empty CSV exports byte for byte (the compat part of #4). The failing test settles #4 either way.
