<!-- Output of the linus-review skill (plain mode) on examples/taskq/change.diff, run by Claude Opus on 2026-11-25. Unedited. -->

## Verdict: do not merge. It changes the default export format from CSV to JSON, which breaks the README's own `taskq export > tasks.csv`.

### 1. Default format flipped from CSV to JSON   [reject]
`taskq/export.py:60`
```
-def run(tasks, fmt="csv", out=sys.stdout, upload_to=None, token=None, path=None):
-    """`taskq export [--format csv|json]`. CSV is the default."""
+def run(tasks, fmt="json", out=sys.stdout, upload_to=None, token=None, path=None):
```
This breaks everyone who relies on the default. Anyone running `taskq export` or calling `run()` without a format now gets JSON where they used to get CSV. The README was not touched and still says CSV is the default. Its example `taskq export > tasks.csv` now puts JSON in a `.csv` file, and anything that reads that file as CSV breaks. The test that pinned the old default was renamed and rewritten to accept the new one, so the change knows it is visible. The commit message does not mention it.

Put back `fmt="csv"`, the "CSV is the default." docstring and `test_csv_is_default`. JSON is already available with `--format json`. If someone wants JSON as their own default, that needs a new opt-in (a config key or an environment variable), not a changed default for everyone.
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
A failed upload now looks the same as a successful one. After the fifth failure the loop ends and the function returns `None`, which is also what it returns on success. Before this commit a failed PUT raised. With `requests.put` stubbed to return a 401, `upload()` made five attempts and raised nothing. A missing file raises inside the `try` and is swallowed the same way, after five 2-second sleeps. So does `path=None`, which is what `run()` passes when the caller does not set `path`. An expired token, a wrong URL or a missing file now all look like a finished upload, and CI goes green with nothing uploaded. The loop also retries errors that can never succeed (401, 403, 404, `FileNotFoundError`) and sleeps after the last attempt.

The comment says "flaky in CI" but not what fails there. Find that first. If it really is a transient network or server error, retry only that error and let everything else raise, including the last failure. Something like this (untested):
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
The comment should name the CI failure the retry waits out.
Principle: Fix the root cause; delays, retries and special cases need a reason (`references/robustness.md` #7); Check the errors that matter (`references/robustness.md` #4); basis: his words; the retry part rests on about seven remarks, so treat it as a strong default.
"We don't "fix" things by papering over some symptom. We try to fix the _actual_ underlying problem." (2017-08-15)

### 3. JSON output turns missing fields from `null` into `""`   [reject]
`taskq/export.py:30`
```
        return [{k: t.get(k, "") for k in FIELDS} for t in tasks]
```
The JSON output changed for any task with a missing field. The old JSON writer used `t.get(k)`, so a task without `due` was written as `"due": null`. The new shared `rows()` writes `"due": ""`. I checked this: `{'id': 1, 'title': 'x'}` gives `null` before the commit and `""` after it. A downstream `jq 'select(.due == null)'` or `if task["due"] is None` now silently stops matching. An empty CSV cell and a JSON null are different things that happened to look alike, and sharing one helper between them is what changed the output.

Give JSON its own rows:
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
This commit fails its own tests: `python3 -m pytest -q` gives 1 failed, 1 passed. The old code wrote the header for an empty list by hand, ending in `"\n"`. `csv.DictWriter.writeheader()` ends it with `"\r\n"`, so `run([], fmt="csv")` now produces `'id,title,state,due\r\n'`. This test was edited in this same commit and it fails, so nobody ran it. Anything that compares an empty export byte for byte, or splits it on `"\n"`, now gets a different file.

Run the tests before sending. Then choose one:
- keep the old bytes for an empty list by restoring that branch, or
- if CRLF everywhere is the goal (non-empty CSV is already CRLF), make that a separate commit that changes the test and says why.

Principle: Testing claims must be real (`references/patches.md` #6); Behaviour users depend on is the contract (`references/compat.md` #1); basis: his words.

### 5. The message calls two behaviour changes a "refactor"   [reject]
`d959416`
```
refactor exporter, fix upload
```
The message does not describe the change. The commit does four things: a class and registry rewrite, a new default format (#1), different JSON output (#3) and a retry loop (#2). The message names two of them, gives no reason for either, and calls a change with visible output differences a refactor. Someone bisecting the CSV breakage, or reading `git log`, gets no hint that it happened here.

Split it into two commits:
- the refactor alone, with byte-identical output and the tests untouched;
- the upload change alone, saying what fails in CI and why a retry addresses it.

Do not resend the default change (#1).
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
This is a lot of machinery for one caller. `run()` is the only caller, and there are still only the two formats there were before. The old if/elif did the same job in six lines. The docstring now invites outside code to subclass and register. Once anyone does, `BaseExporter`, `rows()` and `register` become an interface that has to be kept. The shared `rows()` that came with this machinery is also what caused #3.

If a lookup table is wanted, keep plain functions (untested):
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
