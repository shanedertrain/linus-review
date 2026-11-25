# The corpus

Everything Linus Torvalds has said in public about code, gathered in one place and searchable. It is the
evidence base for the `linus-review` skill (`skills/linus-review`), which an
agent uses to review code the way he does.

## Layout

| Path | Holds |
|---|---|
| `raw/<source>/` | Downloads exactly as fetched (mbox.gz, HTML, git clones). Never edited. Not in git |
| `docs/<source>.jsonl` | Normalised documents, one JSON object per line (schema below). Not in git |
| `scripts/` | One fetch/normalise script per source, Python standard library only, re-runnable and resumable |
| `corpus.db` | SQLite with FTS5 built from `docs/*.jsonl` by `scripts/build_db.py`. Not in git |
| `bin/linus-search` | Query tool over `corpus.db` |
| `analysis/` | Theme reports mined from the corpus (principle, reasoning, verbatim quotes with ids) |

## Document schema (`docs/<source>.jsonl`)

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Unique and stable: the Message-ID for email, the commit sha for commits, the URL otherwise |
| `source` | string | `lore`, `git`, `kernel-docs`, `usenet`, `blog`, `talk`, `interview`, `gplus` |
| `kind` | string | `email`, `commit`, `merge`, `doc`, `forum`, `usenet`, `post`, `transcript` |
| `date` | string | ISO 8601, UTC where known |
| `title` | string | Subject line, commit summary or page title |
| `url` | string | Where a person can read the original (lore permalink, git.kernel.org commit, page URL) |
| `venue` | string | Mailing list name, repository, site or event |
| `in_reply_to` | string or null | Parent Message-ID or parent post URL |
| `body` | string | Full plain text as he wrote it, quoted context included. Never summarised or trimmed |
| `reviews_code` | bool | True when the text quotes a patch or code and responds to it (`> +`, `> -`, `> @@`, quoted C) |

Only text written by Linus Torvalds goes in `docs/`. In a transcript or interview keep the question with his
answer so the answer makes sense, and mark other speakers by name.

## Rules

- Public sources only. No paywalled text and no whole books (`Just for Fun` is out; short quoted passages that
  appear in public articles are fine).
- Be polite to servers: one request at a time per host, at least one second apart, a descriptive generic
  User-Agent with no personal email, back off on 429/503. Resume from what is already in `raw/`.
- Every quote used downstream must be findable verbatim in `corpus.db` by its `id`.

## Rebuilding

Run from the repository root, with Python 3 and git; nothing else is needed for mail. Each script is
resumable and keeps its downloads in `raw/`.

| Step | Command | Notes |
|---|---|---|
| Mail | `python3 scripts/lore_fetch.py` then `python3 scripts/lore_normalise.py` | About 430 requests to lore.kernel.org, 20 minutes, 63 MB. This is 79% of the corpus and the part the skill rests on |
| Commits | `sh scripts/git_fetch.sh` then `python3 scripts/git_normalise.py` | Commit-only clones, about 1.4 GB |
| Kernel docs | `python3 scripts/kernel_docs_fetch.py` | |
| Usenet and early lists | `sh scripts/oldlinux_fetch.sh`, `python3 scripts/usenet_fetch.py`, `python3 scripts/activists_fetch.py`, `python3 scripts/yarchive_fetch.py` | |
| Blog, Google+, interviews, talks | `python3 scripts/blog_fetch.py`, `gplus_fetch.py`, `interview_fetch.py`, `talk_fetch.py` | `talk_fetch.py` needs `yt-dlp`; YouTube rate-limits caption downloads |
| Database | `python3 scripts/build_db.py` | Rebuilds `corpus.db` from every `docs/*.jsonl`, a few seconds |

The mail pipeline was run end to end and checked (no download cap, zero parse failures). The other scripts
each ran once when the corpus was first built and have not been re-run from a clean checkout, so expect to
adjust them. Document ids in `analysis/*.quotes.jsonl` are Message-IDs, commit hashes and URLs, so quotes
verify against any rebuild that contains the same documents.
