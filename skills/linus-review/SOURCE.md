# linus-review: where it came from

Written 2026-11-25. Edit it in this folder; paths below are relative to the repository root.

## Evidence base

55,689 documents of Linus Torvalds's public writing, built into `corpus.db` (SQLite, FTS5) by the scripts in
`scripts/` and searchable with `bin/linus-search`. The database is not distributed; `CORPUS.md` says how to
rebuild it from the public sources.

| Source | Documents | Notes |
|---|---|---|
| lore.kernel.org mail, all lists | 43,922 | 1998 to 2026-11; lore holds almost nothing of his before 1998 |
| Commit messages | 9,030 | linux, BitKeeper-era history, git, sparse, subsurface; merges only where he wrote his own note |
| Usenet and early lists | 2,553 | 1991 to 1995, plus curated later posts from yarchive |
| Google+, blog, talks, interviews, kernel docs | 184 | Google+ is a small fraction; talk transcripts are auto-captions |

Not in the corpus: Real World Technologies forum posts (the site's `robots.txt` disallows AI crawlers), whole
books, anything paywalled.

## How the references were made

1. Eight Opus agents each mined one theme from the corpus into a report with verbatim quotes:
   `analysis/<theme>.md` and `<theme>.quotes.jsonl` (1,019 quotes in total).
2. The same agents condensed each report into `skills/linus-review/references/<theme>.md`.
3. Two checks, both of which every reference file passes:
   - `scripts/verify_quotes.py corpus.db analysis/ref-<theme>.quotes.jsonl`: every quote is verbatim, in his
     own text (not text he was quoting), under the cited id.
   - `scripts/check_inline_quotes.py corpus.db references/<theme>.md`: nothing else in the file sits in quote
     marks.

## Limits to keep in mind when editing

- Almost all of it was said about kernel C. Each principle's **Basis** line records whether the application
  to other code is his or inferred. He has written nothing on Python or TypeScript as languages.
- Message counts and severity levels in the reports are the miners' estimates, not measurements.
- Add a quote only by finding it in `corpus.db` and re-running both checks.

## Updating

Re-run `scripts/lore_fetch.py`, `scripts/lore_normalise.py` and `scripts/build_db.py` to
pull new mail (the fetcher re-reads the current and previous month). The references do not regenerate
themselves; a changed position needs a hand edit with a verified quote.
