# linus-review

A code-review skill for Claude Code and other agents that load `SKILL.md` skills. It reviews a diff, branch or
pull request, in any language, by the standards Linus Torvalds applies to code: what he refuses, what he sends
back, what he grumbles about and takes, and why.

It is built from what he wrote, not from his reputation. 55,689 of his public mails, commit messages, posts
and talk transcripts were gathered into a searchable corpus; eight theme reports were mined from it; and every
quote the skill uses was checked, verbatim, against the source.

This project is not affiliated with or endorsed by Linus Torvalds. The quoted words are his and are cited to
their public sources; everything else here is our reading of them.

## What a review looks like

The example is a fictional project, `taskq`, with one commit titled *refactor exporter, fix upload*
([the diff](examples/taskq/change.diff)). The skill's verdict, unedited:

```
## Verdict: do not merge. It changes the default export format from CSV to JSON, which breaks the
README's own `taskq export > tasks.csv`.

1. Default format flipped from CSV to JSON                          [reject]
2. upload() now reports every failure as success                    [reject]
3. JSON output turns missing fields from null into ""               [reject]
4. The commit fails its own test suite                              [reject]
5. The message calls two behaviour changes a "refactor"             [reject]
6. A registry and an abstract base class for two fixed formats      [rework]
```

It ran the tests (one fails), called the old and new code side by side to confirm the output changes, and
listed what it could not check. Finding 2, in each voice:

**`plain`** (default)

> A failed upload now looks the same as a successful one. After the fifth failure the loop ends and the
> function returns `None`, which is also what it returns on success. Before this commit a failed PUT raised.
> [...] An expired token, a wrong URL or a missing file now all look like a finished upload, and CI goes green
> with nothing uploaded.
>
> The comment says "flaky in CI" but not what fails there. Find that first. If it really is a transient
> network or server error, retry only that error and let everything else raise, including the last failure.
>
> Principle: Fix the root cause; delays, retries and special cases need a reason (`references/robustness.md` #7)
> "We don't "fix" things by papering over some symptom. We try to fix the _actual_ underlying problem." (2017-08-15)

**`classic`**

> Ugh. This isn't a retry, it's a way to make upload failures *invisible*. After five failures the loop ends
> and the function returns `None`, the same thing it returns on success. [...] It's like a smoke alarm that
> beeps five times and then decides the house is fine. Expired token, wrong URL, no file at all, and CI stays
> green with nothing uploaded. That is f\*cking broken.
>
> "Flaky in CI". Flaky *how*? Find that out first.

Same finding, same severity, same fix. Full output: [plain](examples/taskq/review-plain.md),
[classic](examples/taskq/review-classic.md). Both were produced by Claude Opus running the skill; the quoted
lines of his are from the skill's references.

| Severity | Meaning |
|---|---|
| `reject` | Would not take the change: it breaks users, is wrong, cannot be verified, or is not what it claims |
| `rework` | The approach needs redoing before it goes in |
| `grumble` | Worse than it should be, acceptable |
| `good` | Done well, said specifically |

## Two voices, one set of findings

| Mode | How it reads |
|---|---|
| `plain` (default) | His post-2018 register: direct, specific, no insults |
| `classic` | His earlier register: sarcasm, capitals, the occasional asterisked swear word |

`classic` changes wording only. The verdict, findings, severities and fixes are the same in both, and in both
the target is the code and the decision behind it, never the person who wrote it. The style sheet's limits
(no slurs, nothing about who someone is) are in `skills/linus-review/references/voice.md`.

## Install

**Claude Code, as a plugin**

```
/plugin marketplace add shanedertrain/linus-review
/plugin install linus-review@linus-review
```

**Any agent that reads skills from a folder** (Claude Code, Codex and others)

```sh
git clone https://github.com/shanedertrain/linus-review.git
ln -s "$PWD/linus-review/skills/linus-review" ~/.claude/skills/linus-review   # or ~/.codex/skills/
```

The skill is plain Markdown and needs nothing else. The corpus is optional and only adds precedent lookup.

## Use

```
/linus-review                    review uncommitted changes, or the branch against its base
/linus-review HEAD~3..HEAD       a commit range
/linus-review classic src/foo.rs the same review, in the earlier voice
```

Or ask in words: *give me a Linus review of this branch*.

## What is in the skill

| File | Holds |
|---|---|
| `skills/linus-review/SKILL.md` | The procedure: nine questions in priority order, how to check a finding, how to set severity, the output format |
| `references/compat.md` | Never breaking users: behaviour as contract, reverts, extensible interfaces, defaults, removal on evidence |
| `references/patches.md` | The change as a unit: messages that say why, one logical change, testing claims, churn |
| `references/design.md` | Real users today, smallest step, right layer, data model first |
| `references/taste.md` | Special cases, data structures, simple over clever, helpers, naming, comments |
| `references/robustness.md` | Fail the operation not the system, unwinding, boundary validation, root causes |
| `references/language.md` | Nothing hidden: allocation, control flow, conversions; warnings; C and Rust specifics |
| `references/perf.md` | Numbers from real loads, the common path, locking, races |
| `references/voice.md` | How to write the comment, severity wording, both style sheets |

Each principle carries its severity, the signs to look for, his reason, the exceptions, and one dated quote.

## How far to trust it

- **Kernel C is the source.** Almost everything he wrote is about the Linux kernel. Each principle has a
  **Basis** line saying whether he said it about application code (git, subsurface) or whether applying it
  elsewhere is our inference. He has written nothing about Python or TypeScript as languages; examples in
  those languages are ours.
- **Quotes are verified; judgements are not.** Every quoted line was checked verbatim against the corpus. The
  severity levels, the "outside the kernel" readings and the message counts in the reports are estimates made
  by the models that mined the corpus.
- **Coverage has holes.** The lore archive holds almost nothing of his before 1998. The Real World
  Technologies forum, where he has written a great deal about hardware and compilers, is not included because
  the site opts out of AI crawling. Google+ survives only in fragments.
- **It is a reviewer, not him.** It applies his stated standards to the code in front of it. It can be wrong
  about the code, and a finding is only as good as the check behind it; reviews list what was not verified.

## Rebuilding or extending the evidence

The mail and the database are not distributed. `CORPUS.md` describes the layout and how to rebuild the corpus
from the public sources with the scripts in `scripts/`, then search it with `bin/linus-search`. `analysis/`
holds the eight theme reports and the quote files behind the skill. To add or change a principle, find the
quote in your corpus and run both checkers:

```sh
python3 scripts/verify_quotes.py corpus.db analysis/ref-*.quotes.jsonl
python3 scripts/check_inline_quotes.py corpus.db skills/linus-review/references/*.md
```

## Licence

MIT for the code and the original text (see `LICENSE`). Quoted passages remain the work of their author and
are reproduced as short, cited excerpts for commentary.
