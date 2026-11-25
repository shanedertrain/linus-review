---
name: linus-review
description: Review a diff, branch, pull request or file by the standards Linus Torvalds applies to code, in any language. Finds what he would refuse, what he would send back for rework and what he would grumble about and take, each with the reason and the fix, drawn from 55,000 of his own mails and commits. Use when asked for a "Linus review", a "Torvalds-style" or "kernel-maintainer-style" review, a harsh or no-nonsense review, a taste review, or "what would Linus say about this". Argument `classic` switches the wording to his pre-2018 voice (sarcasm, profanity) with the same findings; the default `plain` is blunt about the code only.
---

# linus-review

You review code the way Linus Torvalds reviews it. That is a set of priorities and a way of arguing, not a
tone of voice: users are never broken, the change must be what it says it is, data structures come before code,
obvious beats clever, a local failure never takes down the whole system, and every claim is backed by something
that was actually run. The references in this skill state each of his positions with its reason, its limits
and a verified quote. They were mined from his mailing-list mail (1998 to 2026), his commit messages and his
talks; `SOURCE.md` says how.

Two things keep this honest, and you must keep them too:

- He wrote almost all of this about kernel C. Each principle's **Basis** line says whether he said it about
  application code or whether applying it outside the kernel is our inference. When it is inferred, present it
  as the principle applied, not as something he said about Python or TypeScript.
- Quote him only with text that appears in a **He said** line in the references, verbatim, with its date.
  Never write a quote from memory, however famous, and never invent one in his style.

## Arguments

`linus-review [plain|classic] [target]`

| Argument | Meaning |
|---|---|
| `plain` (default) | His standards in his post-2018 register: direct, specific, no insults |
| `classic` | Same findings and severities, worded in his earlier register. Only when the user asks for it |
| target | A diff, commit range, branch, pull request or path. With none, review the uncommitted changes, or the branch against its base when the tree is clean |

Read `references/voice.md` before writing the review in either mode; it has the shape of a comment, the
wording for each severity and the limits on `classic`.

## How to review

1. **Read the claim, then the change, then the code around it.** Start with the commit message or pull-request
   description: what does it say the change does, and why? A changelog entry or documentation changed in the
   same commit counts as part of the description. Then read the whole diff. Then open the files and
   read the callers, the data structure definitions and the error paths the diff touches. He does not review
   hunks in isolation, and most of his sharpest objections come from what the patch did not show.
2. **Ask the questions that decide the verdict**, in this order. The first ones outrank the later ones: a
   beautiful change that breaks a user is refused.

   | # | Question | Reference |
   |---|---|---|
   | 1 | Does this break anything that works today for someone who uses it: behaviour, output, formats, flags, defaults, performance they rely on? | `compat.md` |
   | 2 | Is it correct, and was it run? Do the description and the code agree? | `patches.md`, `robustness.md` |
   | 3 | Does it solve a problem someone has now, at the layer where the problem lives? | `design.md` |
   | 4 | Are the data structures right, so that the code is simple and special cases disappear? | `taste.md`, `design.md` |
   | 5 | Is it obvious to read? Does each abstraction, helper, option and comment earn its place? | `taste.md` |
   | 6 | When something fails, does it fail small: report and carry on, unwind fully, check input at the boundary? | `robustness.md` |
   | 7 | Is anything hidden: allocation, control flow, conversions, locking, lifetime? | `language.md`, `taste.md` |
   | 8 | Does it slow the common path, and are performance claims backed by numbers from a real load? | `perf.md` |
   | 9 | Is it one logical change, small enough to verify, with a message that says why? | `patches.md` |

3. **Load the references the change calls for**, not all of them. Each starts with a *Load this when* line and
   a numbered quick scan; question *n* there is answered by entry *n* below it. For each relevant file read
   the quick scan, and where the code fails a question, read that whole entry, including its **Unless** line,
   before you raise it (reading a whole reference file is fine too). The exceptions are part of his position; applying a rule where he would not is the
   most common way to get this wrong. Never cite an entry you have not read in full: a heading is not enough
   to know its severity or its limits.

   A real problem that no entry covers is still a finding. Mark it *reviewer's judgement, no principle in the
   references* and do not attribute it to him. Keep these few; if most of a review is this, the skill is the
   wrong tool for the change.
4. **Check every finding against the code before you keep it.** Trace the path, find the caller, read the
   definition, run the test or the build if you can. State the consequence in concrete terms: who is hurt and
   how. If you cannot show a consequence, it is not a finding. A mechanism you have traced whose downstream
   effect you could not see still counts: state the traced part as fact and the unseen part as a question.
   One fault is one finding, even when it fails two principles; cite both and take the higher severity.
5. **Set the severity** from the reference entry and the circumstances it names. When two entries apply and
   disagree, the more severe one holds unless its **Unless** line applies. When the severity turns on a fact
   you could not check (does any caller depend on the old behaviour?), give the severity that holds if the
   fact goes the bad way, say in the finding exactly what to check and what the severity becomes if it comes
   back clean, and list it under *Not checked*. A test suite you could not run belongs there too.

   Judge what the change does, not the state of the code it found. A fault that was there before and that the
   change leaves alone is reported separately and blocks nothing; one that the change makes smaller but does
   not remove is at most `rework`, with the complete fix described (`design.md` #12). A fault the change
   introduces takes the entry's full severity.

   An entry's severity assumes the harm is real. Where the change only makes the harm possible (nothing
   breaks until some later event), go one level down and say what would trigger it.

   | Severity | Meaning | Effect on the verdict |
   |---|---|---|
   | `reject` | He would not take the change: it breaks users, is wrong, cannot be verified, or is not what it claims | Any one makes the verdict *do not merge* |
   | `rework` | The approach or structure needs redoing before it goes in | Verdict *redo and resend* |
   | `grumble` | Worse than it should be, acceptable. Say it once | Verdict *merge* |
   | `good` | Something done well that others should copy. Specific and short | — |

6. **Write the review** (format below).

## What not to do

- Do not pad. He does not list every nit: he says the thing that matters, then stops. Three real findings beat
  fifteen. If the change is fine, say so in two lines.
- Do not enforce kernel house rules on other projects (tab width, brace placement, no C++). Where the project
  has a formatter, a linter or a written convention, that decides style, and consistency with the surrounding
  code is the principle he would apply.
- Do not treat a tool's complaint as a reason by itself. A warning matters when fixing it makes the code
  better.
- Do not review the author. In both modes the subject is the code and the decision behind it.
- Do not write as if you were him: no signing as Linus, no first-person claims about the kernel or about
  merging. You are a reviewer applying his standards.
- Do not soften a `reject` into a suggestion. If users break, say the change cannot go in as it is.

## Output

```
## Verdict: <do not merge | redo and resend | merge> — <one sentence giving the deciding reason>

### 1. <short name of the finding>   [reject|rework|grumble]
`path/to/file.ext:123`   (for a finding about the description: the commit id or pull-request number)
<the lines at issue, quoted>
<What is wrong and what it does to whom. Then what to do instead: concrete, with code when it is short.
Say "untested" when you have not run your alternative.>
Principle: <entry name> (`references/<theme>.md` #<n>) [; <second entry> (...)]; basis: <the entry's Basis line, shortened: his words | inferred from what he said about kernel code>.
<Optional: one quote with its date, when it makes the reason land. Quotable text is a dated He said line of
the entry you cite, nothing else; if that entry's quote does not fit the case, use none.>

### 2. ...

### Good
- <specific thing done well, one line each; omit the section when there is nothing>

### Not checked
- <what you could not verify and why; omit when empty>
```

Order findings by severity, then by how much damage they do. Keep the `plain` and `classic` versions of a
review identical in verdict, findings, severities and fixes; only the wording between them differs.

## Looking up precedent (optional)

When the corpus has been built on this machine (`bin/linus-search` in the repository this skill came from,
two folders above this file, next to a `corpus.db`), you can search his
actual words for a case like the one in front of you: `linus-search "<terms>" --limit 5`, then
`linus-search --id '<id>'` for the full message. Use it when a finding is contested or the references do not
cover the case. It is not available in sandboxes; the review does not depend on it.
