# Patches: the change as a unit of work

Load this when: you are judging a commit, branch or PR as a whole: its message or description, how it is split,
its size, its testing claims, its history (merges, rebases, fixups), its timing against a release, or its credits.

He stated these rules for patches and pull requests sent to him. Restatements for forge PRs, which are often
squash-merged, are marked `transfer inferred`. Every rule below serves one reader: someone with no context, whether
a reviewer, a bisector or a future `git blame` user.

## Quick scan

1. Does the message say *why*, and account for every hunk?
2. Fix or revert: does it say what the user saw and what was wrong?
3. One logical change, or is a refactor, reformat or feature hiding in a fix?
4. Is it touching code that didn't need touching? If a tool made it, does it say how?
5. Is it reviewable as working steps, or is it one big switchover?
6. Does the testing claim survive a look at the warnings and the code paths?
7. Does a performance claim come with numbers?
8. Does the message still make sense with every link dead?
9. Kept commits: does each one build, with the fixups folded in?
10. Is the history honest: no unexplained main-merges, no force-push just before merge?
11. In a freeze: is it a regression fix, and the smallest one?
12. Does the PR description summarise the change and flag what's odd?
13. Are author, reporter and tester credited?

## 1. The message explains why, and matches the diff
**Severity:** rework. Moves to reject when a semantic change has no message, or the message misrepresents the change.      **Basis:** his words
**Rule:** The diff shows what changed. The message has to give why, what was wrong before, and why this way. Every hunk must be covered, and every claim must be true.
**Look for:**
- The diff paraphrased in prose: *Use kvcalloc()*, *Add hook for Z*.
- A new flag, option or API with no named user.
- An unexplained odd construct: `READ_ONCE`, `#[allow(..)]`, `# type: ignore`, a retry loop.
- An unmentioned hunk, such as an extra early return.
- A root cause the evidence doesn't support, such as *compiler bug* or a blamed commit.
- Style, a nit only: a subject with no area prefix or not in the imperative (*net: fix X*, not *This patch fixes X*), *This PR...* in a squash message, a wall of text.
**Why:** A reviewer can't judge rightness without the reason. A wrong story misleads the next debugger, and a hidden hunk is where the next bug will be. He unpulls over misleading messages.
**Unless:** It is an obvious one-liner. The bar rises with how surprising the change is.
**He said:** "Again - you're explaining what it *does*.  I see what it does. That was never the issue." (2025-03-26, `CAHk-=wiH3hoPTxX3=xTRzRuCwktf3pNzFWP45-x6AwoVAjUsUQ@mail.gmail.com`)

## 2. Fixes say how it failed; reverts say what was wrong
**Severity:** rework. Taken with a complaint when the fix is small and urgent.      **Basis:** his words
**Rule:** A fix states what the user saw (crash, hang, wrong value, build break), the trigger, and how long it has been broken. A revert states what the reverted change broke and how that was noticed.
**Look for:**
- *Fix bug* or *breaks some platforms* with no failure mode.
- A bare `This reverts commit <sha>`.
- A years-old bug with no word on why nobody hit it.
- Details only in the linked issue.
**Why:** The reverted change had a reason. Without the symptoms, nobody knows when it is safe to reapply, and a bisector cannot match their failure to the commit.
**Unless:** It is a security fix. Then describe the bug, not the exploit.
**He said:** "the reason why that original change was wrong, and how it was noticed (ie what the symptoms of the reverted patch were) is important." (2021-07-22, `CAHk-=wirFvNqAvaNaABHc2mi7FKL4n6TEAwQ3WTyTJueJcHCvA@mail.gmail.com`)

## 3. One logical change per commit
**Severity:** rework. Moves to reject for a hotfix or release-branch PR carrying non-fixes.      **Basis:** his words
**Rule:** Keep these apart:
- moving code and editing it;
- reformatting and behaviour changes;
- a no-semantics refactor, which goes first;
- fixes and everything else, so a fixes branch carries fixes only.

A squash-merged PR counts as one commit.
**Look for:** Move plus edit in one commit; a reformat plus a logic change in one hunk; a fix that also renames things or rewrites error paths; a signature change bundled with new behaviour:
```ts
-function reserve(a, b, c, d, align, alignData)   // new calling convention...
+function reserve(req: Requirement)               // ...and new semantics, same commit
```
**Why:** A pure move can be shown to change nothing, and blame follows it. A cleanup that reorders IO and breaks a rare setup hides where the bug is. A change hidden in a fix makes the fix dangerous.
**Unless:**
- Many tiny same-kind commits should be one. Separation is conceptual, not a commit count.
- Don't split off code nothing uses yet, or a first half that makes no sense alone (he has asked for such halves to be combined).
- Small edits in a rename are fine.
**He said:** "So "many small patches" aren't automatically any better than one big one. The thing that matters is to keep things _conceptually_ separated." (2003-12-29, `Pine.LNX.4.58.0312291137021.2113@home.osdl.org`)

## 4. Churn and tool output need a human reason
**Severity:** rework. Moves to reject for a pure-churn PR that fixes nothing.      **Basis:** his words (checkpatch, scripts, AI as a tool); other linters and codemods are transfer inferred
**Rule:** Renames, API reshuffles, mass reformatting and linter-zero sweeps cost reviewers, blame and backports. They must fix something or clearly improve the code. A tool-made change (script, codemod, LLM, autofix) says so and includes the command or prompt. Auto-added metadata (link trailers, reviewer or Cc lists) must be curated.
**Look for:**
- *Fix lint warnings* or *modernise* across untouched files.
- A rename forcing dozens of call-site edits.
- Search-and-replace that hits correct code.
- Lint fixes that make code uglier.
- A sweep with no command; a big AI change with no disclosure.
**Why:** Churn is a real expense: blame noise, conflicts, and bugs from "cleanups" of fragile code. Checker rules are heuristics, and making code worse to satisfy them is wrong.
**Unless:**
- Whitespace-only or format-only commits are welcome, and better than mixing them into fixes. Run a formatter once, announced, and put it in the blame-ignore list.
- Planned, announced scripted churn is fine.
- Linting new code is fine.
- AI is a tool like any other: disclose it, verify the result, and apply the same bar.
**He said:** "The fact is, pointless churn is BAD. It's a real expense." (2020-04-27, `CAHk-=wi2bdXuYhC9bd9FShtcf_u-6RUb3Qr_aXq3XtbCxR5NGQ@mail.gmail.com`)

## 5. Reviewable steps, no flag days
**Severity:** rework. Moves to reject for a huge undivided rewrite with a one-line explanation.      **Basis:** his words
**Rule:** Land big changes as small, explained steps that each leave the system working, so each step can be reviewed, blamed and reverted alone.
**Look for:**
- Thousands of lines with one sentence of description.
- A wholesale replacement with no side-by-side path (a flag, an adapter).
- A last commit that switches everything over.
**Why:** The bug a patch adds is usually unrelated to its purpose, and in one big patch wrong details don't stand out. A flag day has no point where the problem started.
**Unless:** The switchover is unavoidable. The test is verifiability, not size: a huge mechanical change that tooling can check is fine.
**He said:** "there can be large and invasive patches that are easy to verify with tooling, so it's not necessarily about the size per se" (2026-07-22, `CAHk-=wgbGarE7Ozw4VG6oUKDj9pk-8DRoDiX00bo1MwEMm9UWQ@mail.gmail.com`)

## 6. Testing claims must be real
**Severity:** reject when code visibly never compiled cleanly or never ran; rework otherwise.      **Basis:** his words
**Rule:** A build test includes reading the compiler and linter output. A path that cannot work was never run. Untested work is fine if it is labelled, as he labels his own.
**Look for:**
- New warnings or suppressed type errors in the diff's build output.
- Code that could never have worked: swapped arguments, use before assignment.
- *Tested* claimed on commits force-pushed an hour ago.
- A sketch presented as finished.
**Why:** Without checking the result, a build test is just a build.
**Unless:** Real testing is impossible (no hardware, rare config) and the PR says exactly what was and wasn't tested.
**He said:** "Without the checking of the result, "build-testing" is just "building", and completely irrelevant." (2020-02-12, `CAHk-=wh8eYt9b8SrP0+L=obHWKU0=vXj8BxBNZ3DYd=6wZTKqw@mail.gmail.com`)
"This is entirely untested, thus the "Not-yet-signed-off-by"." (2024-05-03, `20240503211129.679762-2-torvalds@linux-foundation.org`)

## 7. Performance claims need numbers
**Severity:** rework. Moves to reject when complexity is added with no data.      **Basis:** his words
**Rule:** Measure the improved case and the normal case, and show that the code matters (it appears in profiles). The numbers go in the commit message. Handwaved worst cases are no argument either way.
**Look for:**
- *Optimise* or *faster* with no before and after.
- A new cache, a lock split or manual inlining with no profile.
- Objections based on imagined load.
**Why:** A micro-optimisation without numbers is a random code change. Complexity costs, so it needs a measured benefit.
**Unless:** The change also simplifies or obviously improves the code; then numbers are welcome but may be impossible. Synthetic benchmarks are fine when labelled.
**He said:** "Micro-optimizations need numbers. Otherwise they aren't micro-optimizations, they are just "change code randomly"." (2018-06-05, `CA+55aFxTve6FxLuvWyyD88ACOg+3eHKbpWUeuvNZMSB=AFfuqg@mail.gmail.com`)

## 8. The message stands alone; links add to it
**Severity:** grumble. Moves to rework when a link replaces the explanation.      **Basis:** his words; trackers and PR links are transfer inferred
**Rule:** Everything needed to understand the change is in the message. A link earns its place by leading to more: the bug report, the design discussion, CI results. A bare ticket number, or a bot link back to the change's own review, adds nothing.
**Look for:**
- *See #1234* as the whole explanation.
- Credits reachable only through a link.
- A bot adding link trailers to every commit.
**Why:** Trackers move and links rot. A link to the change itself makes readers chase an explanation that isn't there.
**Unless:** The link goes to the original report or the fix discussion. He loves those.
**He said:** "but the commit message also has to stand on its own, even _without_ the pointer." (2006-11-22, `Pine.LNX.4.64.0611211843010.3338@woody.osdl.org`)
"Add the link if it has *ADDITIONAL* information." (2025-09-05, `CAHk-=wjamixjqNwrr4+UEAwitMOd6Y8-_9p4oUZdcjrv7fsayQ@mail.gmail.com`)

## 9. Kept commits each build; fold fixups in
**Severity:** rework.      **Basis:** his words; the squash-merge case is transfer inferred
**Rule:** When commits are kept (a merge or rebase merge), each must build and pass on its own so that bisect works. Fold a fix for an unmerged commit into that commit. Never merge a fix without the change it fixes.
**Look for:**
- Commit 1 changes a signature, and commit 3 fixes the callers.
- *Fix build* or *address review* commits in a kept series.
- A follow-up fix landed before its prerequisite.
**Why:** A broken middle commit means the series wasn't a series, and bisect needs a human. A buggy commit plus a later fix traps bisectors in between.
**Unless:**
- The PR is squash-merged: only the end state must build, though the split still helps review.
- The commit is already on a shared branch: fix it on top and reference it.
- The change won't split cleanly: convert the callers with no behaviour change first, then do the cleanups, and add the new behaviour last.
**He said:** "This kind of "split up one large patch into many small patches THAT DON'T ACTUALLY WORK INDIVIDUALLY" model is pure and utter garbage." (2014-01-20, `CA+55aFxLD4dPnQjb85LkB5eW24XsoUQD8n9XP9i-Oy2xM0iQKA@mail.gmail.com`)

## 10. Honest history: explained merges, no last-minute rewrites
**Severity:** grumble. Moves to rework when shared history is rewritten or tested commits are swapped out.      **Basis:** his words about maintainer trees; the forge restatement is transfer inferred
**Rule:**
- Don't merge main into a feature branch to sync up or to test. Use a throwaway branch for integration.
- If you need something from main, say why.
- Rebasing your own branch before review is good. Rewriting a branch others build on is not.
- Retest after a force-push just before merge: it throws away the old testing.
- A merge commit, or a squash message, needs a real summary, never the forge default alone.
**Look for:**
- Repeated *Merge branch 'main' into feature* commits with no reason.
- A post-approval force-push that changes more than the reviewed diff.
- A rewritten release branch.
- A squash message that is only a list of fixup subjects.
**Why:** Pointless merges hide the line of development and base the work on random untested points. A rebase destroys history: a bug's cause vanishes from it. A merge has no diff, so its message is its only explanation.
**Unless:**
- Rewriting is fine when the branch isn't public yet, when something really went wrong (a commit that breaks bisect), or for unshared work in progress.
- A back-merge or rebase with a stated reason is fine.
- A tiny merge needs only a short message.
**He said:** "I repeat: if you cannot explain a merge, then JUST DON'T DO IT." (2023-02-21, `CAHk-=wgw++ccN-Pd1npZsBSDD3z6EGUSKsWuAEh5YC-TmfJAug@mail.gmail.com`)

## 11. Late in a release: regression fixes, smallest version
**Severity:** reject (defer) during a freeze, unless it is a regression fix or the failure is severe.      **Basis:** his words about the merge window and -rc weeks; code freezes and release or hotfix branches are transfer inferred
**Rule:** During stabilisation, take only fixes for regressions, crashes and security problems, in their minimal form. New work, cleanups and fixes for long-standing issues wait for the next cycle. A late change must say why it can't wait. Fixes carry risk too.
**Look for:**
- A large *fix* PR aimed at a release branch.
- Refactors or hardening labelled as urgent.
- A clean 150-line rework where a 5-line fix exists.
- A years-old bug fixed in the last days of a freeze.
- No time in staging.
**Why:** Fixes add bugs at a high rate. A bug that went unnoticed for years is subtle, so its fix probably is too. Work should be ready before the window, not developed in it.
**Unless:**
- A small, obvious fix that would be backported anyway is fine.
- Security fixes and severe crashes are always in.
- A new isolated component that can't break existing users can come in.
- For continuous deployment, only the smallest-fix rule carries over.
**He said:** "if you can make an obvious fix in 5 lines, do it.  Don't try to make a clean fix that fixes the problem the clever way in 150 lines." (2001-01-06, `937neu$p95$1@penguin.transmeta.com`)

## 12. The PR description summarises, and flags what's odd
**Severity:** rework. Moves to reject when the description doesn't match the branch.      **Basis:** his words about pull requests; the forge restatement is transfer inferred
**Rule:** Say what the change does and why to take it. Name anything unusual: files outside the author's area, a recent rebase, a known conflict, odd timing. A squash merge often turns the description into the commit message, so it must read as a record.
**Look for:**
- Background with no statement of what the change does.
- A pasted commit list instead of a summary.
- Unmentioned edits to other teams' code.
- Contents that differ from the description.
**Why:** If the reviewer has to read the code to guess what's being asked, the description failed. An unexplained oddity draws suspicion; an explained one is fine.
**Unless:** The PR is small. Then a list of the details is the summary.
**He said:** "The code looks fine, but I had to *look* at the code to try to even guess at what the hell you asked me to pull, and that's not fine." (2026-10-26, `CAHk-=wh0gCvsC7A9z_H7her218kSCmd16dqtd9uMfO5ZrSvxLw@mail.gmail.com`)

## 13. Credit the right people; nobody certifies for another
**Severity:** rework. Moves to reject for a forged sign-off or approval.      **Basis:** his words; `Co-authored-by` is transfer inferred
**Rule:** Keep the real authorship through cherry-picks and squashes. Credit the reporter, the tester and whoever root-caused the bug in the commit itself. Never add a sign-off or approval for someone else, or add one afterwards.
**Look for:**
- A squash that drops co-authors.
- The committer shown as the author.
- A reported bug fixed with no reporter credit.
- Root-cause credit swallowed by a one-line fix.
**Why:** Reporting and testing are part of the record, and finding the cause is often the hard part. A faked sign-off is like a faked signature.
**Unless:** The author waives credit for a throwaway sketch. The credit then goes to whoever tested it or found the bug.
**He said:** "bug reporting and testing is a fundamental part of commit logs, not some secondary thing." (2021-09-17, `CAHk-=wgE+ngSaKxv1MW+un1f=N4QnC0jFC46b3nNZinQRnZj0g@mail.gmail.com`)

## Model: one of his commits, verbatim

The commit below has:
- an area prefix and an imperative subject;
- the problem first;
- the wrong use shown against the correct form;
- an honest note on impact;
- a `Fixes:` line naming the culprit.

(2024-07-29, `9f499b8c791d2983c0a31a543c51d1b2f15e8755`; *ddid* is his typo.)

```
minmax: scsi: fix mis-use of 'clamp()' in sr.c

While working on simplifying the minmax functions, and avoiding
excessive macro expansion, it turns out that the sr.c use of the
'clamp()' macro has the arguments the wrong way around.

The clamp logic is

	val = clamp(in, low, high);

and it returns the input clamped to the low/high limits. But sr.c ddid

	speed = clamp(0, speed, 0xffff / 177);

which clamps the value '0' to the range '[speed, 0xffff / 177]' and ends
up being nonsensical.

Happily, I don't think anybody ever cared.

Fixes: 9fad9d560af5 ("scsi: sr: Fix unintentional arithmetic wraparound")
Cc: Justin Stitt <justinstitt@google.com>
Cc: Kees Cook <keescook@chromium.org>
Cc: Martin K. Petersen <martin.petersen@oracle.com>
Signed-off-by: Linus Torvalds <torvalds@linux-foundation.org>
```

## Position changes

- **Links:** since 2022 he opposes links back to the change's own submission. Add a link only when it carries more information.
- **Style checkers:** fine for new code, but no reason to edit existing code (2023, 2025).
- **AI:** since 2025, AI-assisted changes are tool output. Disclose the tool, verify the result, and apply the same bar. He is not anti-AI.
