# Format for skill reference files

Your theme report is the evidence record and stays as it is. Now write the version a reviewing agent will
load while reviewing code: `skills/linus-review/references/<theme>.md`.

## Who reads it

An agent in the middle of reviewing a diff, in any language, that has decided this theme is relevant. It has
not read your report and has no access to the corpus. It needs to recognise a problem in the code in front of
it, know how seriously to take it, know when the rule does not apply, and be able to say why in Linus's
terms. It does not need the history of how the position was established. Aim for 10 to 16 KB; a principle
that would not change a review of ordinary code does not belong.

## What to keep and drop

- Keep principles that apply to a change in an ordinary codebase (service, library, CLI, firmware, application),
  and kernel-specific ones only when they have a clear counterpart there. Drop the rest; they remain in your
  report.
- Merge principles that a reviewer would apply as one check.
- Order by how often a reviewer will need them, most frequent first.
- Keep every limit and exception that stops a false alarm. These matter as much as the rules.

## Layout

```
# <Theme title>

Load this when: <one or two sentences: what in a diff makes this theme relevant>

## Quick scan
<one line per principle: the question a reviewer asks of the code, e.g. "Does a special case exist only
because of how the data is laid out?">

## 1. <Principle name>
**Severity:** reject | rework | grumble      **Basis:** his words | his words about kernel code, transfer inferred
**Rule:** <one or two sentences>
**Look for:** <bullets: concrete signs in a diff; give them language-neutrally, with a short example in
C, Rust, Python or TypeScript where that helps recognition>
**Why:** <his reasoning, one to three sentences>
**Unless:** <the exceptions>
**He said:** "<verbatim>" (<YYYY-MM-DD>, `<id>`)
```

Severity is what he does about it: `reject` (would not take the change: it breaks users, is wrong, is
unverifiable, or misrepresents itself), `rework` (take it after it is redone), `grumble` (says so and takes it).
Where it depends on circumstances, give the default and say what moves it.

"Basis" must be honest. If he said it about kernel C and the application to other code is our reading, say
`transfer inferred`, and where you give a Rust, Python or TypeScript example that he never discussed, that is
part of the inference; do not put words in his mouth.

"He said": one quote per principle, two at most, chosen because it states the reason memorably. Each must be
a line already in your verified `analysis/<theme>.quotes.jsonl`, or a contiguous sub-passage of one. No quote
marks around anything else in the file: paraphrases, made-up reviewer phrases and labels go without quote
marks (use italics or a code span if you need to set a phrase apart).

End with a short `## Position changes` section only if a reviewer would otherwise apply an outdated rule.

## Check before you finish

1. Write the quotes you used to `analysis/ref-<theme>.quotes.jsonl` (same line format as before) and run
   `python3 scripts/verify_quotes.py corpus.db analysis/ref-<theme>.quotes.jsonl` until clean.
2. Run `python3 scripts/check_inline_quotes.py corpus.db <your reference file>` and bring it to zero unmatched.
3. Report the file size, the number of principles kept and dropped (name the dropped ones), and both
   checkers' last lines.

Write only those two files. No git commits.
