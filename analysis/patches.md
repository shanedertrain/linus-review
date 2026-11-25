# Theme: patches (the change as a unit of work)

What Linus Torvalds demands of a commit, a patch series, a merge and a pull request, apart from the quality of the
code inside them. Every quote below is in `patches.quotes.jsonl` and passes `scripts/verify_quotes.py`.

The one idea under almost all of it: **a change is a message to a future reader who has no context**: a maintainer
deciding whether to take it, someone bisecting a regression, someone running `git blame` years later. Everything he
demands (the why, the symptoms, one change per commit, every step building, no meaningless merges, honest test
claims) serves that reader. Everything he rejects (noise links, auto-generated merge text, churn, rebased-yesterday
trees) wastes that reader's time or destroys information.

Kernel-specific terms used below: *merge window* = the two weeks when new work goes in; *-rc* = the weeks after,
when only fixes do; *linux-next* = the integration tree where branches are tested together before he pulls them.

---

## 1. The commit message must say why, not only what

**Principle.** The diff shows what changed. The message has to supply what the diff cannot: why the change is
needed, what was wrong before, and why this way. A message that only restates the diff in English fails.

**What triggers it in a review.**
- A message that paraphrases the code: "Switch X to pass dentry and inode separately", "Use kvcalloc()", "Add policy
  hook for firmware load".
- New interfaces, hooks, flags or config options with no stated user or need.
- A non-obvious construct in the diff (an `#ifndef __clang__`, a `READ_ONCE()`, a lock taken in teardown) that the
  message never mentions.
- No message at all on a change that alters semantics.

**His reasoning.** He reviews explanations more than code (he says in interviews that by the time a pull reaches
him the code has been reviewed; he looks at "the explanations, and the history of how the patch came to me"). A
reviewer who can see what the code does but not why cannot judge whether it is right. His test is "lack of
surprise": the message should prepare you for what the diff does.

**How serious.** Grounds for a NAK on a semantic change with no message (2021). For pulls, a missing why gets
a grudging pull, an unpull, or a demand for a re-send, depending on how odd the change looks.

**Limits and exceptions.** A truly obvious one-liner ("Fix typo in xyz") needs only a trivial message: the code
explains itself. The bar rises with how non-obvious the change is, and merges have the highest bar of all (see 6).

**Outside the kernel.** Transfers unchanged. In a review of any PR: if you can only describe the commit by reading
the diff, the message is deficient. Ask "why is this needed?" and "what was broken?" when the message only says what.

**Evidence.**
- "Again - you're explaining what it *does*.  I see what it does. That was never the issue." (`CAHk-=wiH3hoPTxX3=xTRzRuCwktf3pNzFWP45-x6AwoVAjUsUQ@mail.gmail.com`, 2025-03-26, https://lore.kernel.org/all/CAHk-%3DwiH3hoPTxX3%3DxTRzRuCwktf3pNzFWP45-x6AwoVAjUsUQ%40mail.gmail.com/)
- "Please add a _why_ something is done, not just what it does." (`CA+55aFx8J1sTuWjb9N9n7=WbHtr-aBEdWbb5qaf=rd598aUYHA@mail.gmail.com`, 2016-05-27, https://lore.kernel.org/all/CA%2B55aFx8J1sTuWjb9N9n7%3DWbHtr-aBEdWbb5qaf%3Drd598aUYHA%40mail.gmail.com/)
- "The fact that this has no commit message at all to explain what it is doing and why is also a grounds for just NAK." (`CAHk-=wjsg0Lgf1Mh2UiJE4sqBDDo0VhFVBUbhed47ot2CQQwfQ@mail.gmail.com`, 2021-01-18, https://lore.kernel.org/all/CAHk-%3Dwjsg0Lgf1Mh2UiJE4sqBDDo0VhFVBUbhed47ot2CQQwfQ%40mail.gmail.com/)
- Limit: "A normal commit that does an obvious one-liner fix? It really may not need more than a trivial commit message saying "Fix typo in xyz". The rest of the commit explains it well enough." (`CA+55aFyMw63bV+KOOiP9MbXF=BU8mHYEzBYsNH=xrVWxO=rzKg@mail.gmail.com`, 2017-07-18, https://lore.kernel.org/all/CA%2B55aFyMw63bV%2BKOOiP9MbXF%3DBU8mHYEzBYsNH%3DxrVWxO%3DrzKg%40mail.gmail.com/)
- Talk (auto-caption): "lack of surprise is probably the best single sign of a good commit" (`https://www.youtube.com/watch?v=PVDsnK_8QdQ`, 2018-07-26)

**How well supported.** Very strong: 30+ messages read, 2006 to 2026, plus 2018 and 2025 talks. Never contradicted.

---

## 2. The message must match the patch; a misleading message is worse than a thin one

**Principle.** Everything the diff does must be covered by the message, and nothing the message claims may be false.
An unexplained extra hunk, or a wrong story about the cause ("this was a compiler bug", "commit X caused this"),
is a serious defect in its own right.

**What triggers it in a review.**
- A hunk that the message never mentions (an extra `if (... I_FREEING) { ... return; }` in a "one fix" patch).
- A message that blames the wrong commit or the toolchain, or a revert whose subject line has been mangled.
- Two unrelated changes where the message describes one.

**His reasoning.** History is read later, by people trusting the message to tell them what a commit did. A wrong
explanation sends a future debugger down the wrong path, and a hidden hunk is exactly where the next bug will be.

**How serious.** He unpulled a whole media tree in 2015 over corrupted revert subjects and unpulled the 2022
writeback fix over a message that did not match the change. One of the few things that reliably costs a pull.

**Limits and exceptions.** Inaccuracies in his own merge summaries he simply fixes himself (2017, "Fixing that up in
my merge commit message"). The severity is about misleading the reader, not about prose quality.

**Outside the kernel.** Transfers fully. Read the message, then the diff: every file and hunk must be accounted for.
Flag claims about root cause that the diff or the bug report does not support.

**Evidence.**
- "I unpulled this, because I think misleading commit messages is a serious problem" (`CA+55aFzNkvRYbhfiwOOC+_okHKN+Hf93bTF0fpiEqn6fYtLmEw@mail.gmail.com`, 2015-08-18, https://lore.kernel.org/all/CA%2B55aFzNkvRYbhfiwOOC%2B_okHKN%2BHf93bTF0fpiEqn6fYtLmEw%40mail.gmail.com/)
- "Fix the damn explanation to actually match the change." (`CAHk-=wgqkWVi3nm6HJvOOy+GUVmPt9Wun+_ZVp47wZU43FET9w@mail.gmail.com`, 2022-12-10, https://lore.kernel.org/all/CAHk-%3DwgqkWVi3nm6HJvOOy%2BGUVmPt9Wun%2B_ZVp47wZU43FET9w%40mail.gmail.com/)
- "It isn't obvious why this is mixed up with the Kconfig changes, and somebody already asked about it." (`CA+55aFyJg=-PfrVV1kw_bqKKd9Uk+q2FS4pqPp-og_DDbhhaFw@mail.gmail.com`, 2017-12-27, https://lore.kernel.org/all/CA%2B55aFyJg%3D-PfrVV1kw_bqKKd9Uk%2Bq2FS4pqPp-og_DDbhhaFw%40mail.gmail.com/)
- "I'm not complaining about the fix. I'm complaining about how the fix was claimed to be due to a compiler bug." (`CA+55aFyud32TExCVaL-k5dCPqrEBD9AZd-st6ooziwZCy9HZDg@mail.gmail.com`, 2013-10-27, https://lore.kernel.org/all/CA%2B55aFyud32TExCVaL-k5dCPqrEBD9AZd-st6ooziwZCy9HZDg%40mail.gmail.com/)

**How well supported.** Strong: about 12 messages, 2009 to 2024 (including the 2009 futex "commentary is also TOTAL
CRAP" case and the 2024 "commit message is actively misleading" overflow case).

---

## 3. Say how the bug shows up, and why a revert is needed

**Principle.** A fix should say what the user saw (oops, hang, data corruption, build failure, wrong value), on what,
and how long it has been broken. A revert must say what was wrong with the reverted commit and how it was noticed.
"Fix bug", "breaks some platforms" and a bare "This reverts commit X" are not enough.

**What triggers it in a review.**
- A revert with only the generated "This reverts commit ..." line.
- "Fixes a crash" or "breaks X" with no mode of failure.
- Fixes for long-standing bugs that never say why nobody noticed (he asks this explicitly).
- The detail exists in a linked thread but not in the message.

**His reasoning.** The reverted change "was done for a reason"; without the symptoms, the next person cannot tell
whether re-applying it is safe, and a bisector cannot match their symptom to the commit. He wants to stop having to
"go look for it".

**How serious.** Mostly pulled with a request to do better next time. He rarely refuses over it alone, but it compounds
other doubts about a late or odd fix.

**Limits and exceptions.** For security bugs, describe the bug but not the exploit: "Should I document the exploit in
the commit message? Hell no." (2008). The exploit goes to the private list.

**Outside the kernel.** Transfers fully. A bug-fix PR should state the user-visible failure and the trigger; a revert
PR should say what the original broke and how that was found.

**Evidence.**
- "The "breaks a number of PPC platforms" is not actually saying what went wrong. Breaks how? Does it stop booting, does it not build, or what?" (`CAHk-=wix=qQ79=fqgSy8Fc9jenRG8HoUp3VZs=Ek+PGz7d+13g@mail.gmail.com`, 2020-04-05, https://lore.kernel.org/all/CAHk-%3Dwix%3DqQ79%3DfqgSy8Fc9jenRG8HoUp3VZs%3DEk%2BPGz7d%2B13g%40mail.gmail.com/)
- "that "something" was done for a reason, and the reason why that original change was wrong, and how it was noticed (ie what the symptoms of the reverted patch were) is important." (`CAHk-=wirFvNqAvaNaABHc2mi7FKL4n6TEAwQ3WTyTJueJcHCvA@mail.gmail.com`, 2021-07-22, https://lore.kernel.org/all/CAHk-%3DwirFvNqAvaNaABHc2mi7FKL4n6TEAwQ3WTyTJueJcHCvA%40mail.gmail.com/)
- "I think that info should have been in the commit message rather than me having to go look for it" (`CAHk-=wiLi2_JJ1+VnhZ3aWr_cag7rVxbhpf6zKVrOuRHMsfQ4Q@mail.gmail.com`, 2022-01-17, https://lore.kernel.org/all/CAHk-%3DwiLi2_JJ1%2BVnhZ3aWr_cag7rVxbhpf6zKVrOuRHMsfQ4Q%40mail.gmail.com/)
- Limit: "Should I document the exploit in the commit message? Hell no." (`alpine.LFD.1.10.0807151716510.2867@woody.linux-foundation.org`, 2008-07-16, https://lore.kernel.org/all/alpine.LFD.1.10.0807151716510.2867%40woody.linux-foundation.org/)

**How well supported.** Moderate to strong: about 10 messages, 2008 to 2022. His own commits show the same pattern
constantly (see 19).

---

## 4. The message stands on its own; links add to it, never replace it, and a link to the patch itself is noise

**Principle.** Everything needed to understand the commit goes in the message. A link is welcome only when it leads to
something extra: the bug report, the long discussion, the test results. A `Link:` to the posting of the same patch adds
nothing, and he calls it actively harmful because readers follow it hoping for an explanation.

**What triggers it in a review.**
- `Link:` pointing at the submission email of the same patch (typically added automatically by `b4 -l`).
- A message that is a one-liner plus "see <url>".
- Invented tag names (`BugLink:`, CamelCase tags) used to tell useful links apart from useless ones.
- Credits (reporter, tester) only reachable by following a link.

**His reasoning.** Web servers move or vanish, people read history offline, and git works disconnected (2006). A
useless link is "reliably NEGATIVE information that wastes peoples time" (2025). The useful context about a commit is
the discussion that caused it or the reports it later caused, which cannot be linked when the commit is created; so
an automatically added link is "by definition" noise.

**How serious.** Complaints in many pulls 2020 to 2025. He unpulled the 2022 writeback fix and the 2025 io_uring fix,
with the useless link as part of the reason. His frustration has grown over the years (see "Changes of position").

**Limits and exceptions.** He "absolutely adore[s]" links to the original problem or the discussion of how to fix it.
A link to a public Gerrit review that shows who approved what is fine (2022). He proposes keeping submission
references as comments added by a hook, not as tags (2025).

**Outside the kernel.** Transfers directly to "Closes #123", Jira keys and PR links. The commit should make sense if
the tracker is gone. Flag commits whose whole explanation is a ticket number, and auto-added links that carry nothing.

**Evidence.**
- "but the commit message also has to stand on its own, even _without_ the pointer." (`Pine.LNX.4.64.0611211843010.3338@woody.osdl.org`, 2006-11-22, https://lore.kernel.org/all/Pine.LNX.4.64.0611211843010.3338%40woody.osdl.org/)
- "They are completely useless when they link to "this is the patch submission of the SAME DAMN PATCH THAT THE COMMIT IS"." (`CAHk-=wj9zKJGA_6SJOMPiQEoYke6cKX-FV3X_5zNXOcFJX1kOQ@mail.gmail.com`, 2022-05-11, https://lore.kernel.org/all/CAHk-%3Dwj9zKJGA_6SJOMPiQEoYke6cKX-FV3X_5zNXOcFJX1kOQ%40mail.gmail.com/)
- Limit, same message: "They are *really* wonderful when they link to some long discussion about how to solve the problem."
- "Add the link if it has *ADDITIONAL* information." (`CAHk-=wjamixjqNwrr4+UEAwitMOd6Y8-_9p4oUZdcjrv7fsayQ@mail.gmail.com`, 2025-09-05, https://lore.kernel.org/all/CAHk-%3DwjamixjqNwrr4%2BUEAwitMOd6Y8-_9p4oUZdcjrv7fsayQ%40mail.gmail.com/)
- "We are not going to replace good commit messages with links to external things, and as such those links should never be important on their own." (`CAHk-=wgzRUT1fBpuz3xcN+YdsX0SxqOzHWRtj0ReHpUBb5TKbA@mail.gmail.com`, 2022-06-15, https://lore.kernel.org/all/CAHk-%3DwgzRUT1fBpuz3xcN%2BYdsX0SxqOzHWRtj0ReHpUBb5TKbA%40mail.gmail.com/)

**How well supported.** Very strong: about 20 messages, 2006, then a dense run 2020 to 2025.

---

## 5. Write for an outsider: subject line, area prefix, imperative mood, paragraphs, no boilerplate

**Principle.** The subject is read in one-line logs by people who do not know your subsystem: name the area, say what
the change does, no SHA-only subjects. Use imperative mood ("Fix X", not "This patch fixes X" or "Five patches fixing
X"). Break long explanations into short paragraphs. Notes for the maintainer only go below the `---`. Don't add
fixed-format boilerplate fields that compress the explanation into one line.

**What triggers it in a review.**
- Subjects like "Bugfix to commit <sha>", "Fix execve() argument handling" for a one-architecture fix, or a subject
  repeated as the first body line.
- "This patch ...", "This series ...", "X did Y, fixing Z", "N-patch series to ...".
- One unbroken wall of text.
- Version-change notes or "I'm working on a better patch" inside the committed message.
- Mandatory one-line summary fields (the 2009 `Impact:` lines).

**His reasoning.** "make sense for a *reader*, not for yourself". Present tense reads oddly two years later, "This
pull request does..." makes no sense once it is a merge. He edited "about half of all the commit messages" he got by
email in 2007, and still edits pull text in 2026.

**How serious.** Low: he fixes these himself and grumbles; he says outright that it is "not a big deal" (2026). It
never costs a pull alone.

**Limits and exceptions.** Taste, not law: "I guess it's a matter of taste" (2026). Short is fine when the change is
small; he says long changelogs should be technical, not "a fluffy novella".

**Outside the kernel.** Transfers fully: conventional "area: imperative summary" subjects, imperative body, no "this
PR" phrasing, no ticket-number-only subjects. Treat as a nit, not a blocker.

**Evidence.**
- "if it's not fairly generic, specify the area (architecture, subsystem, driver) that the fix is for in the subject line." (`alpine.LFD.0.999.0710230839120.30120@woody.linux-foundation.org`, 2007-10-23, https://lore.kernel.org/all/alpine.LFD.0.999.0710230839120.30120%40woody.linux-foundation.org/)
- Same message: "write the commit message for an outsider, and use whitespace."
- "This is why I much prefer imperative voice (ie "Fix XYZ"), because it's neutral." (`CAHk-=wgDJ=uKf99U0Fxcii5=qE_Gk-AgR0Uh9G0o0eQ-9HDf7w@mail.gmail.com`, 2026-08-24, https://lore.kernel.org/all/CAHk-%3DwgDJ%3DuKf99U0Fxcii5%3DqE_Gk-AgR0Uh9G0o0eQ-9HDf7w%40mail.gmail.com/)
- "Note that after the "---" you can have any amount of explanations that are not to be committed as comments on why." (`Pine.LNX.4.64.0510021158260.31407@g5.osdl.org`, 2005-10-02, https://lore.kernel.org/all/Pine.LNX.4.64.0510021158260.31407%40g5.osdl.org/)
- Against boilerplate: "ALL of the commit message is (hopefully) about important things. If you want to narrow it down to one single line, that's just WRONG." (`alpine.LFD.2.00.0904151607010.4042@localhost.localdomain`, 2009-04-15, https://lore.kernel.org/all/alpine.LFD.2.00.0904151607010.4042%40localhost.localdomain/)

**How well supported.** Strong: about 15 messages, 2005 to 2026. Imperative-mood demands are mostly 2020 to 2026.

---

## 6. Merge commits need real explanations, more than normal commits; auto-generated merge text is not one

**Principle.** A merge is a commit. Its message must say what is being merged and why the merge exists. "Merge branch
'x' into y" alone, "Merge tag v4.20-rc1", or pasted email noise (greetings, `base-commit:`, signatures) is unacceptable.
Merges need *more* explanation than ordinary commits because there is no diff to read.

**What triggers it in a review.**
- A one-line merge message, or `git merge`'s default text left unedited.
- Merge messages built by a script from the incoming email.
- Pull-request descriptions that are just a reformatted shortlog.

**His reasoning.** "In a merge commit, the _only_ explanation you have is basically the commit message". He admits the
default merge text is his own git usability mistake: he designed it for his own merges, where the message already
says enough (2011).

**How serious.** One of his most repeated complaints ("literally hundreds of times"). Usually pulled with a complaint;
in 2018 he refused a gfs2 pull outright and threatens to stop pulling.

**Limits and exceptions.** For a tiny pull, an automated shortlog "maybe" suffices; "sometimes the message might be
just "Small x86 fixes"" (2021). A plain branch-and-source line beats an information-free one (2014).

**Outside the kernel.** Transfers to merge commits and squash-merge PR titles and bodies. On GitHub-style flows the
equivalent is the PR description that becomes the merge or squash message: it should be a human summary, not the
default "Merge pull request #123 from user/branch".

**Evidence.**
- "Merge commits are to some degree *more* important, because they do odd things and the reason is not obvious from the code" (`CAHk-=wi1f2tTnHe_DoMBsoj7v38G746Kk=tpouGg0_Y3fUFqKA@mail.gmail.com`, 2018-11-15, https://lore.kernel.org/all/CAHk-%3Dwi1f2tTnHe_DoMBsoj7v38G746Kk%3DtpouGg0_Y3fUFqKA%40mail.gmail.com/)
- "In a merge commit, the _only_ explanation you have is basically the commit message, and when the commit message is garbage, the merge is garbage." (`CAHk-=wgJx0FKq5FUP85Os1HjTPds4B3aQwumnRJDp+XHEbVjfA@mail.gmail.com`, 2019-09-19, https://lore.kernel.org/all/CAHk-%3DwgJx0FKq5FUP85Os1HjTPds4B3aQwumnRJDp%2BXHEbVjfA%40mail.gmail.com/)
- "Merge messages need to be meaningful, and no amount of auto-generation will ever make them so." (`CAHk-=whZMDmgs3+djfUoVrx8jj7DwGOJvLWC=vw1dCMicqHJ1g@mail.gmail.com`, 2021-10-01, https://lore.kernel.org/all/CAHk-%3DwhZMDmgs3%2BdjfUoVrx8jj7DwGOJvLWC%3Dvw1dCMicqHJ1g%40mail.gmail.com/)
- "are just complete noise that seems to indicate that you automate your merges with garbage, instead of actually editing them and making them be meaningful." (`CAHk-=whxDHD7PFLdtS_am8ta5uqyBnjhkQTcRLtPN6-3K+TuRg@mail.gmail.com`, 2021-11-02, https://lore.kernel.org/all/CAHk-%3DwhxDHD7PFLdtS_am8ta5uqyBnjhkQTcRLtPN6-3K%2BTuRg%40mail.gmail.com/)

**How well supported.** Very strong: 25+ messages, 2011 to 2026.

---

## 7. No pointless merges: if you cannot explain a merge, do not make it

**Principle.** Do not merge upstream into your branch "to sync", to test against latest, or because "that's how we
work". A back-merge needs a real reason (a conflict you must resolve, a dependency on a specific fix), and then you
should merge the specific commit you need and say why. Keep your branch about your work; integration testing belongs
in a separate throwaway branch.

**What triggers it in a review.**
- `Merge branch 'main' into feature` commits with no stated reason, especially several of them.
- Merges of a random mid-cycle upstream point.
- A feature branch that is used to test against everything else.

**His reasoning.** Extraneous merges "mix up different branches" and hide the line of development; they make history
"look worse and harder to read"; they base your work on an untested random point; and they make the merge message
the only explanation, which is usually empty.

**How serious.** Constant complaints; he has refused branches over them and asks people to drop the merge. With
established maintainers, usually pulled with a complaint.

**Limits and exceptions.** "Sometimes you need to do back-merges" (2026), with a reason stated in the message. A merge
of an explicit commit ("git merge <sha>") with a message is the right shape (2011). A separate integration branch
for your own testing is fine as long as it is not what you ask to have pulled (2024).

**Outside the kernel.** Transfers well to any team that keeps merge history. "Update branch" merge commits are the
GitHub version; a reviewer should ask the author to rebase their *unpublished* branch or drop the merge, and should
never accept "merged main to test it" as part of the deliverable. Teams that squash-merge mostly avoid the issue.

**Evidence.**
- "I repeat: if you cannot explain a merge, then JUST DON'T DO IT." (`CAHk-=wgw++ccN-Pd1npZsBSDD3z6EGUSKsWuAEh5YC-TmfJAug@mail.gmail.com`, 2023-02-21, https://lore.kernel.org/all/CAHk-%3Dwgw%2B%2BccN-Pd1npZsBSDD3z6EGUSKsWuAEh5YC-TmfJAug%40mail.gmail.com/)
- "And if the only reason for that merge is "sync with upstream", then no, that is not a sufficient reason." (`CA+55aFyMw63bV+KOOiP9MbXF=BU8mHYEzBYsNH=xrVWxO=rzKg@mail.gmail.com`, 2017-07-18, https://lore.kernel.org/all/CA%2B55aFyMw63bV%2BKOOiP9MbXF%3DBU8mHYEzBYsNH%3DxrVWxO%3DrzKg%40mail.gmail.com/)
- "Extraneous merge commits that have no actual reason for development are bad. They make it much harder to see what the actual development thread was, because they mix up different branches." (`CA+55aFyzq+EBHiKYyEw3OXWKeeTbwt1sCYACfD4YsOWCBBZTVQ@mail.gmail.com`, 2013-05-02, https://lore.kernel.org/all/CA%2B55aFyzq%2BEBHiKYyEw3OXWKeeTbwt1sCYACfD4YsOWCBBZTVQ%40mail.gmail.com/)
- Limit: "Sometimes you have to rebase because of a mistake. Sometimes you need to do back-merges. But you should damn well have *reasons* for both that aren't "that's just how we work"." (`CAHk-=whwq2_iaf7pTuzVXEcJmng_exwae_bKtgSDdm4BQivGHg@mail.gmail.com`, 2026-05-20, https://lore.kernel.org/all/CAHk-%3Dwhwq2_iaf7pTuzVXEcJmng_exwae_bKtgSDdm4BQivGHg%40mail.gmail.com/)
- "Your development branch IS NOT FOR TESTING OTHER RANDOM THINGS." (`CAHk-=wgzMxdCRi9Fqhq2Si+HzyKgWEvMupq=Q-QRQ1xgD_7n=Q@mail.gmail.com`, 2024-07-18, https://lore.kernel.org/all/CAHk-%3DwgzMxdCRi9Fqhq2Si%2BHzyKgWEvMupq%3DQ-QRQ1xgD_7n%3DQ%40mail.gmail.com/)

**How well supported.** Very strong: about 20 messages, 2009 to 2026.

---

## 8. Do not rebase published history, and never rebase just before asking for a pull

**Principle.** Rebasing private, unpublished work is good (it is how you split, reorder and clean up a series). Once
others have seen or built on a branch, rewriting it is "lesser of two evils" territory. Rebasing right before a pull
throws away the testing the old commits had and hands over commits nobody has run. If you had to, say so and why.
Base work on a stable known point (a release), not the upstream tip of the day.

**What triggers it in a review.**
- A pull or PR whose commits all have commit dates from the last day, during or just before the merge.
- Commits whose IDs differ from what was tested in CI or staging.
- A branch rebased "to avoid a small conflict".
- A base that is a random mid-development upstream commit.
- A rebase that silently rewrote someone's fix (2026: a bad rebase "destroy[s] history").

**His reasoning.** Downstream users of the branch get the rug pulled out from under them; testing is invalidated;
the cause of a rebase-introduced bug disappears from history. For maintainers it also blocks others from working
with the tree (2008).

**How serious.** Refuses late pulls that were rebased without explanation (2016 Ceph, 2022 ata, 2026 KEYS). Accepts
with explanation.

**Limits and exceptions.** Three allowed reasons (2014): not public yet; you "*really* screwed up" (a commit that
breaks bisect); a work in progress nobody depends on. A rebase that is explained ("this was around in linux-next for a
week before that") removes his worry (2018, 2023).

**Outside the kernel.** Transfers to any shared branch: don't force-push shared branches; a PR force-pushed minutes
before merge should be re-tested; explain unusual rebases in the PR. On a personal feature branch before review,
rebasing is encouraged, not discouraged.

**Evidence.**
- "The rules have been pretty clear: "don't rebase public trees"." (`CA+55aFy0OFQ5ncwHwpah4xwxuOuMEWL+w6Dv-akTFnogpLo1yA@mail.gmail.com`, 2014-08-07, https://lore.kernel.org/all/CA%2B55aFy0OFQ5ncwHwpah4xwxuOuMEWL%2Bw6Dv-akTFnogpLo1yA%40mail.gmail.com/)
- Same message: "In general, "rebase just before asking somebody to pull" is just a bad idea."
- "When  you rebase, you are throwing your old testing away, and you're also making me get new commits that are different from the linux-next commits." (`CA+55aFyXACVwL6inthTv=Orvp_6wDaA1c_BLvwJTYBORQTXa+w@mail.gmail.com`, 2016-03-26, https://lore.kernel.org/all/CA%2B55aFyXACVwL6inthTv%3DOrvp_6wDaA1c_BLvwJTYBORQTXa%2Bw%40mail.gmail.com/)
- "They destroy history, and when bugs happen, it's really hard to see *why* the bug happened because the actual cause of the bug has disappeared and no longer exists after the rebase." (`CAHk-=whyYBFw+o9RRyGXvfS+ipQgGAM1oHFL9KXFoCCkRvrTfA@mail.gmail.com`, 2026-07-22, https://lore.kernel.org/all/CAHk-%3DwhyYBFw%2Bo9RRyGXvfS%2BipQgGAM1oHFL9KXFoCCkRvrTfA%40mail.gmail.com/)
- Limit: "Rebasing branches is absolutely not a bad thing for individual developers." (`alpine.LFD.1.10.0805161933240.3020@woody.linux-foundation.org`, 2008-05-17, https://lore.kernel.org/all/alpine.LFD.1.10.0805161933240.3020%40woody.linux-foundation.org/)
- Limit (an explained rebase): "tells me not only why the times are so recent, but also tells me that I really shouldn't worry because so-and-so." (`CA+55aFwvKerkzigZmm0zrUTnsqDpJs0XBtX72Ltmek+_ic-KmA@mail.gmail.com`, 2018-07-25, https://lore.kernel.org/all/CA%2B55aFwvKerkzigZmm0zrUTnsqDpJs0XBtX72Ltmek%2B_ic-KmA%40mail.gmail.com/)
- "If you start development, or if you have to rebase (for some *good* reason) you need to do so on a good stable base, not on the quick-sand that is "random kernel of the day during the busiest merge activity"." (`CAHk-=whY1J-LFvTa8ihiPNRSv1dwxPk9ycPCEhdcjsk7c=tGAw@mail.gmail.com`, 2019-07-16, https://lore.kernel.org/all/CAHk-%3DwhY1J-LFvTa8ihiPNRSv1dwxPk9ycPCEhdcjsk7c%3DtGAw%40mail.gmail.com/)

**How well supported.** Very strong: about 20 messages, 2008 to 2026, consistent throughout.

---

## 9. One logical change per commit: never mix cleanup, code movement, whitespace and fixes

**Principle.** Each commit does one conceptual thing. Code movement is separate from changes to the moved code;
whitespace and style are separate from behaviour; preparatory refactoring that changes no semantics comes first as its
own commit; a "fixes" branch contains only fixes.

**What triggers it in a review.**
- A file move plus edits in the same commit; a reformat of a function plus a logic change in it.
- A "fix" commit that also renames variables, reorders functions or rewrites error paths.
- A fixes PR or hotfix branch that includes new features or cleanups.
- Infrastructure change (new struct, new calling convention) and semantic change bundled in one patch:

```diff
-int foo(a, b, c, d, alignf, alignf_data)   // signature change ...
+int foo(struct requirement *req)           // ... and new behaviour in the same hunk
```

**His reasoning.** A pure move can be proven to change nothing and `git blame -C` can follow it; a move-plus-edit
cannot (2007). If a cleanup reorders register writes and breaks rare hardware, "now you cannot tell where the bug is"
(2007). Separated preparatory work can even be merged early (2011). A hidden change in a fix is what makes a late
fix scary (2010).

**How serious.** Rejecting a "fixes" pull mixed with cleanups is common and harsh (2017 block: "Stop this fuckery
already"; 2020 block: "Real fixes, and fixes ONLY"). For ordinary patches, a request to split.

**Limits and exceptions.** Not "many small patches are automatically better": a dozen tiny "fix bug on line 50" commits
of the same kind should be one commit; what matters is conceptual separation (2003). He dislikes patches that add code
nothing uses yet, and accepts a bigger patch over a split that introduces dead code (2007, 2009). He asked in 2026 for
two patches to be *combined* because the first alone was "just ugly" without the reason the second supplies.
"Impure" renames (small edits to the moved file's header) are fine in a rename commit (2007).

**Outside the kernel.** Transfers fully. Ask for refactor-only commits ahead of behaviour changes, formatter runs in
their own commit, and hotfix PRs that are minimal. Do not demand splitting a change whose parts make no sense apart.

**Evidence.**
- "So do cleanups _separately_ from movement." (`alpine.LFD.0.98.0706231113200.3593@woody.linux-foundation.org`, 2007-06-23, https://lore.kernel.org/all/alpine.LFD.0.98.0706231113200.3593%40woody.linux-foundation.org/)
- "This isn't fixes. This is new code that does new things, or cleanups, or other random things mixed up with some fixes." (`CA+55aFzXDzoMqHic3RxUzyYzxDkHB1sr_oHJTEv2k4V1wjOa=g@mail.gmail.com`, 2017-09-23, https://lore.kernel.org/all/CA%2B55aFzXDzoMqHic3RxUzyYzxDkHB1sr_oHJTEv2k4V1wjOa%3Dg%40mail.gmail.com/)
- "And that cleanup/re-organization would be prime material for a totally independent patch that changes no semantics at all, just prepares for the other changes." (`CA+55aFwo-48yKu+raRF3B9n1mqd1qV35eDq56Yi+erPygkuTvA@mail.gmail.com`, 2011-07-03, https://lore.kernel.org/all/CA%2B55aFwo-48yKu%2BraRF3B9n1mqd1qV35eDq56Yi%2BerPygkuTvA%40mail.gmail.com/)
- "But those hardware interface changes are easily the things that can break, where some cleanup results in register writes being done in a different order or something, and so if there's a bug there (and it's not visible on most setups), now you cannot tell where the bug is." (`alpine.LFD.0.999.0707111524510.20061@woody.linux-foundation.org`, 2007-07-11, https://lore.kernel.org/all/alpine.LFD.0.999.0707111524510.20061%40woody.linux-foundation.org/)
- Limit: "So "many small patches" aren't automatically any better than one big one. The thing that matters is to keep things _conceptually_ separated." (`Pine.LNX.4.58.0312291137021.2113@home.osdl.org`, 2003-12-29, https://lore.kernel.org/all/Pine.LNX.4.58.0312291137021.2113%40home.osdl.org/)
- "and that there wasn't some other change hidden in the same commit." (`alpine.LFD.2.00.1006071436160.4506@i5.linux-foundation.org`, 2010-06-07, https://lore.kernel.org/all/alpine.LFD.2.00.1006071436160.4506%40i5.linux-foundation.org/)

**How well supported.** Very strong: about 20 messages, 2003 to 2026.

---

## 10. Size and reviewability: small, explained steps; avoid one-shot rewrites and flag days

**Principle.** Large changes should arrive as a sequence of small, individually explained steps that keep the system
working, so each can be reviewed and each can be blamed or reverted alone. One huge undivided patch with a one-line
explanation is not reviewable. "Flag day" switchovers, where everything changes at once, are a last resort.

**What triggers it in a review.**
- A multi-thousand-line diff with a one-line message.
- A rewrite that replaces a module wholesale with no incremental path or A/B option.
- A series whose last patch "switches everything over".
- Large invasive changes from an unknown contributor.

**His reasoning.** Small patches are easier to review and the inevitable bugs are easier to find ("try reverting that
one patch"), because the bug a patch introduces is usually unrelated to what it fixes (2005). In one big patch the
details that are wrong do not stand out (2012). Flag days leave no "this is where the problem started" (2021).

**How serious.** From a request to split it to non-acceptance (the 2000 IrDA 330kB patch; the 2015
"flag-day things" refusal).

**Limits and exceptions.** Sometimes a big switch "is unavoidable" (2009 workqueue). Splitting must not create dead
code or non-working intermediate steps (see 9 and 11). In his preference order a total rewrite beats keeping dead code
around (2021). His 2026 definition of "invasive" is about verifiability, not size: a huge mechanical change that tools
can verify is acceptable.

**Outside the kernel.** Transfers fully: stacked PRs, feature flags or parallel implementations instead of big-bang
rewrites; a PR too large to review should be split. Apply the "hard to verify" test, not a line count.

**Evidence.**
- "it's a damn lot easier to review 100 small patches that do simple things and that have been split up and explained individually byt he submitter than it is to review 10 big ones." (`Pine.LNX.4.58.0501251054400.2342@ppc970.osdl.org`, 2005-01-25, https://lore.kernel.org/all/Pine.LNX.4.58.0501251054400.2342%40ppc970.osdl.org/)
- "10,000+ lines of diff, with _no_ effort to split it up, or explain it with anything but" (`Pine.LNX.4.10.10011072316180.15590-100000@penguin.transmeta.com`, 2000-11-08, https://lore.kernel.org/all/Pine.LNX.4.10.10011072316180.15590-100000%40penguin.transmeta.com/)
- "Details like this would possibly stand out a bit more if it wasn't one big patch." (`CA+55aFyE41U9OPr7mrAA2ZJKuQ2jvH-KmusUNyfYbH8tOm6yiQ@mail.gmail.com`, 2012-04-06, https://lore.kernel.org/all/CA%2B55aFyE41U9OPr7mrAA2ZJKuQ2jvH-KmusUNyfYbH8tOm6yiQ%40mail.gmail.com/)
- "(a) actual incremental changes where the code keeps working all the time, and no flag days" (`CAHk-=wg2LQtWC3e4Z4EGQzEmsLjmk6jm67Ga6UMLY1MH6iDcNQ@mail.gmail.com`, 2021-10-22, https://lore.kernel.org/all/CAHk-%3Dwg2LQtWC3e4Z4EGQzEmsLjmk6jm67Ga6UMLY1MH6iDcNQ%40mail.gmail.com/)
- Limit: "Maybe it's inevitable, but if this one could be split up a bit more, I'd find the series less scary." (`alpine.LFD.2.01.0910011008210.6996@localhost.localdomain`, 2009-10-01, https://lore.kernel.org/all/alpine.LFD.2.01.0910011008210.6996%40localhost.localdomain/)
- Limit (his own patch): "I could have split out "hash.[ch]" as a separate patch just to introduce the infrastructure, but I hate patches that add code that isn't used at all." (`alpine.LFD.0.999.0710251120590.30120@woody.linux-foundation.org`, 2007-10-25, https://lore.kernel.org/all/alpine.LFD.0.999.0710251120590.30120%40woody.linux-foundation.org/)
- Limit: "(Here I define "invasive contribution" as something that is hard to verify as a patch - there can be large and invasive patches that are easy to verify with tooling, so it's not necessarily about the size per se)." (`CAHk-=wgbGarE7Ozw4VG6oUKDj9pk-8DRoDiX00bo1MwEMm9UWQ@mail.gmail.com`, 2026-07-22, https://lore.kernel.org/all/CAHk-%3DwgbGarE7Ozw4VG6oUKDj9pk-8DRoDiX00bo1MwEMm9UWQ%40mail.gmail.com/)

**How well supported.** Strong: about 15 messages, 2000 to 2026.

---

## 11. Bisectability: every commit builds and works; fold fixes into unpublished originals

**Principle.** Each commit in a series must compile and work on its own, so `git bisect` can run unattended over it.
Splitting a change into pieces that only work together is worse than not splitting it. A fix for a bug in a commit
that is not yet published should be folded into that commit, not stacked on top. A fix must not be merged without
the change it fixes.

**What triggers it in a review.**
- Patch 1 changes a function's signature; callers are updated in patch 3.
- "Fix build" or "fix typo in previous commit" commits inside the same unmerged series.
- A follow-up fix merged on its own while the commit it fixes is still elsewhere (his own 2021 revert of a clang fix,
  merged without "gcov: use kvmalloc()", which broke the build).

**His reasoning.** A non-compiling commit means "the series wasn't a series" and bisect needs manual intervention
(2007). A buggy patch plus its fix adds "unnecessary bisection issues" for anyone who lands between them (2022).

**How serious.** "A big NAK on this series as being completely broken" (2014). He also complains when the build
breaks with another compiler because of it (2022 clang).

**Limits and exceptions.** Once a commit is public, the fix goes on top (with `Fixes:`) rather than rewriting history;
folding is for when the branch is being rebased anyway (2022). He offers a way out for an unsplittable
change: first convert all callers with no change in behaviour, then the cleanups, then the new behaviour last (2014).

**Outside the kernel.** Transfers fully to any repo where history is kept (not squash-merged): every commit should
pass CI. During review, ask for fixup commits to be squashed into the commit they fix before merge.

**Evidence.**
- "This kind of "split up one large patch into many small patches THAT DON'T ACTUALLY WORK INDIVIDUALLY" model is pure and utter garbage." (`CA+55aFxLD4dPnQjb85LkB5eW24XsoUQD8n9XP9i-Oy2xM0iQKA@mail.gmail.com`, 2014-01-20, https://lore.kernel.org/all/CA%2B55aFxLD4dPnQjb85LkB5eW24XsoUQD8n9XP9i-Oy2xM0iQKA%40mail.gmail.com/)
- Same message, the remedy: "that way, all patches compile cleanly and should each work individually, and they all do clearly just one thing."
- "if you have something that doesn't compile in the middle, not only does it show that the series wasn't a series, it also means that you cannot automate the bisect and you need manual intervention." (`Pine.LNX.4.64.0703140837300.9690@woody.linux-foundation.org`, 2007-03-14, https://lore.kernel.org/all/Pine.LNX.4.64.0703140837300.9690%40woody.linux-foundation.org/)
- "please just fold this fix into the original commit, so that we don't have unnecessary bisection issues." (`CAHk-=whUy_cuJsVeob4zDnK5sWpE3U2EjVbnR2xobqgx7DOp4g@mail.gmail.com`, 2022-05-11, https://lore.kernel.org/all/CAHk-%3DwhUy_cuJsVeob4zDnK5sWpE3U2EjVbnR2xobqgx7DOp4g%40mail.gmail.com/)
- "just fold the thing into the original patch rather than carry a buggy patch and the fix around." (`CA+55aFzMP3oYV9G8bzskkyNEpqcHGSBR3rWCF_TWF4QhOMmR8A@mail.gmail.com`, 2011-07-19, https://lore.kernel.org/all/CA%2B55aFzMP3oYV9G8bzskkyNEpqcHGSBR3rWCF_TWF4QhOMmR8A%40mail.gmail.com/)
- His own revert: "It was a fix for "gcov: use kvmalloc()", which is still in -mm/-next. Merging it alone has broken the build." (`7af08140979a6e7e12b78c93b8625c8d25b084e2`, 2021-04-19, https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=7af08140979a6e7e12b78c93b8625c8d25b084e2)

**How well supported.** Strong: about 12 messages, 2007 to 2022. "Fixes stacked on unmerged work" specifically is
backed by 4 messages; thinner than the rest.

---

## 12. Timing and risk: development before the release window, regression fixes after; "it's a fix" is not enough

**Principle.** New work, cleanups, conversions and large "fixes" for old problems belong in the development window,
having been in integration testing. After that, only regression fixes, serious crashes and security problems go in,
and they should be minimal. The later in the cycle, the higher the bar. Fixes themselves add bugs. A late or out-of-
window change must say why it cannot wait.

**What triggers it in a review.**
- A large "fix" PR against a release or stabilization branch.
- Hardening, conversions, test-suite expansions or "noticed a long-standing problem" fixes sent as urgent.
- A clean 150-line fix where a 5-line fix exists.
- Work sent on the last day of the window that was never in integration testing.
- A pull whose late arrival is not explained.

**His reasoning.** The 2001 "think like a release manager" policy: .1 releases were always worse than .0 because of
pent-up patches. "The number of bugs that happen in "bug fixes" is in fact quite high" (2024). A bug that sat
unnoticed for years is rare and subtle, so its fix is likely to be subtly buggy too (2026). The window exists for
merging and slack in people's lives, "not for development" (2025).

**How serious.** One of the commonest reasons he refuses or delays a pull ("Feel free to submit this for 5.2 after it
has actually seen testing", 2019; "I'm ignoring it", 2015). In 2026 he took a 41,197-insertion rc5 update under
protest with a warning that next time he will ignore it.

**Limits and exceptions.** A small obvious fix that would go to stable anyway is taken at any time (2024). New
drivers can come outside the window when they improve someone's life (2010), and "small and trivial" late pulls are
acceptable (2016). A planned scripted conversion just after rc1, agreed beforehand, is fine (2026). Security issues
and major oopses are always in scope (2010).

**Outside the kernel.** Transfers to any release-train or code-freeze process: during stabilisation, accept only fixes
for regressions or severe user impact, prefer the minimal fix, and require the author to justify why a change cannot
wait. For projects that deploy continuously, the transferable part is "fixes carry risk too; the smallest fix wins
when the system must stay stable".

**Evidence.**
- "Obviously, the size of the patch matters too: if you can make an obvious fix in 5 lines, do it.  Don't try to make a clean fix that fixes the problem the clever way in 150 lines." (`937neu$p95$1@penguin.transmeta.com`, 2001-01-06, https://lore.kernel.org/all/937neu%24p95%241%40penguin.transmeta.com/)
- Same message: "try to think like a release manager and explain to me why the patch really makes sense to apply now."
- "The fixes after the merge window are supposed to be fixes for regressions, not "oh, I noticed a long-standing problem, and now I'm fixing that"." (`CAHk-=wjwn-YAJpSNo57+BB10fZjsG6OYuoL0XToaYwyz4fi1MA@mail.gmail.com`, 2024-08-24, https://lore.kernel.org/all/CAHk-%3Dwjwn-YAJpSNo57%2BBB10fZjsG6OYuoL0XToaYwyz4fi1MA%40mail.gmail.com/)
- Limit, same message: "if it's a small obvious fix that would be stable material *anyway*, then there is no reason to wait for the next release"
- "This whole notion of "anything that is a fix goes in -rc" is bogus." and "And that makes the *fixes* possibly buggy." (`CAHk-=whyUfwzMDMTpih8Xs1MxmhwTCDAc_YwUSZG79vXFMLU=Q@mail.gmail.com`, 2026-11-24, https://lore.kernel.org/all/CAHk-%3DwhyUfwzMDMTpih8Xs1MxmhwTCDAc_YwUSZG79vXFMLU%3DQ%40mail.gmail.com/)
- "You say it fixes a problem - but does it fix a REGRESSION?" (`AANLkTik1HCrAus2Rv29EK_vGDf9d2m0E=cAuvF6LEQiQ@mail.gmail.com`, 2011-03-25, https://lore.kernel.org/all/AANLkTik1HCrAus2Rv29EK_vGDf9d2m0E%3DcAuvF6LEQiQ%40mail.gmail.com/)
- "In contrast, as a 5.18 merge window pull request, this makes complete sense." (`CAHk-=wi3fRiQXynJrLvaD5DDqF0MzgX1xSGFSJS_2frwXT1E5Q@mail.gmail.com`, 2022-02-08, https://lore.kernel.org/all/CAHk-%3Dwi3fRiQXynJrLvaD5DDqF0MzgX1xSGFSJS_2frwXT1E5Q%40mail.gmail.com/)
- "Multi-hundred-line pull requests that come in this late had better look a bit more serious than that." (`CA+55aFzo-sA4P_rMC1wWfLp50QswfP0GdLxMQ+Wbw8ArK5capw@mail.gmail.com`, 2013-10-23, https://lore.kernel.org/all/CA%2B55aFzo-sA4P_rMC1wWfLp50QswfP0GdLxMQ%2BWbw8ArK5capw%40mail.gmail.com/)
- "The code should be ready *BEFORE* the merge window starts." (`CAHk-=wh-LQTLhD-vOqHfhb3cyust1aeU4UPmTyGkaD5kgDFLzg@mail.gmail.com`, 2025-12-12, https://lore.kernel.org/all/CAHk-%3Dwh-LQTLhD-vOqHfhb3cyust1aeU4UPmTyGkaD5kgDFLzg%40mail.gmail.com/)

**How well supported.** Very strong: 35+ messages, 2001 to 2026.

---

## 13. Testing claims must be real: building means reading the warnings; untested work is labelled as such

**Principle.** "Tested" has to mean something. Compile-testing includes reading the compiler output; code that does
not compile cleanly was not tested; code that obviously never ran should never have been merged. Late work should
have sat in integration testing. When you send something untested (he does, often), say so plainly.

**What triggers it in a review.**
- New compiler warnings in the diff's build output (format mismatches, uninitialised variables).
- Code paths that cannot have worked (wrong argument order, use before initialisation, a function that never handled
  its partial case).
- A PR description claiming testing that the branch's history contradicts (all commits from today).
- A patch sent as a proposal that carries a final sign-off.

**His reasoning.** Without reading the result, "build-testing" is just building. Warnings mean the code "hasn't even
seen a compiler". He wants the "warm fuzzy feeling" of linux-next for late pulls. For his own patches he uses
`Not-yet-signed-off-by:` so nobody mistakes a sketch for a tested change.

**How serious.** Pulled, test-built, unpulled (2020 block). Refused and told to come back next window (2019 AFS,
2011 NOMMU). "Dropped as crap" (2008).

**Limits and exceptions.** "Reported-and-compile-tested-by" is acceptable for a fix where real hardware testing is
not possible, with that limitation stated (2010). He accepts reasonable confidence where testing is impractical,
with the honesty intact.

**Outside the kernel.** Transfers fully. Build warnings and linter errors introduced by the diff are a testing failure,
not a style nit. Ask "did this path ever run?" when a diff fixes or adds code that cannot have worked. Welcome a PR
honestly marked draft or untested; distrust one claiming tests its own content contradicts.

**Evidence.**
- "Without the checking of the result, "build-testing" is just "building", and completely irrelevant." (`CAHk-=wh8eYt9b8SrP0+L=obHWKU0=vXj8BxBNZ3DYd=6wZTKqw@mail.gmail.com`, 2020-02-12, https://lore.kernel.org/all/CAHk-%3Dwh8eYt9b8SrP0%2BL%3DobHWKU0%3DvXj8BxBNZ3DYd%3D6wZTKqw%40mail.gmail.com/)
- "It means "look at what the compiler says" too." (`CAHk-=wiFwUUEpCQ2FDWxBFb3XSxu=+yODHGfLPncvTQa9BeP9w@mail.gmail.com`, 2020-08-21, https://lore.kernel.org/all/CAHk-%3DwiFwUUEpCQ2FDWxBFb3XSxu%3D%2ByODHGfLPncvTQa9BeP9w%40mail.gmail.com/)
- "The thing hasn't even seen a compiler, and when you *do* show the code to a compiler, said compiler correctly warns" (`CAHk-=wisFUf55wZ3o5pv8ZY5st9utSdWELAofsJ6AwAwYByPPg@mail.gmail.com`, 2019-03-16, https://lore.kernel.org/all/CAHk-%3DwisFUf55wZ3o5pv8ZY5st9utSdWELAofsJ6AwAwYByPPg%40mail.gmail.com/)
- "Code that simply has never had any testing AT ALL should not have gotten in." (`CA+55aFwe3HrgMBUhyHC7kAOCvp31S4kpAqDSFQ+BQY6r=WBiiA@mail.gmail.com`, 2018-07-08, https://lore.kernel.org/all/CA%2B55aFwe3HrgMBUhyHC7kAOCvp31S4kpAqDSFQ%2BBQY6r%3DWBiiA%40mail.gmail.com/)
- "In particular, if people send me pull requests late, I had better get the warm fuzzy feeling of "at least it's been tested in linux-next"." (`CA+55aFyoY+cOrU1BnZwu8ytWKuCOfPaxziynAMDSe0dwR-PaGQ@mail.gmail.com`, 2018-04-13, https://lore.kernel.org/all/CA%2B55aFyoY%2BcOrU1BnZwu8ytWKuCOfPaxziynAMDSe0dwR-PaGQ%40mail.gmail.com/)
- His own practice: "This is entirely untested, thus the "Not-yet-signed-off-by"." (`20240503211129.679762-2-torvalds@linux-foundation.org`, 2024-05-03, https://lore.kernel.org/all/20240503211129.679762-2-torvalds%40linux-foundation.org/)
- "That's purely because I wanted it to be obvious that this needs a lot more testing" (`CAHk-=wi4Rgo7f17AwYduEPKr6SEVq-mxRJiZ5S5X0hQ9RWmkYA@mail.gmail.com`, 2021-05-03, https://lore.kernel.org/all/CAHk-%3Dwi4Rgo7f17AwYduEPKr6SEVq-mxRJiZ5S5X0hQ9RWmkYA%40mail.gmail.com/)

**How well supported.** Very strong: 25+ messages, 2008 to 2025. A SQL count found 337 lore messages from 2000 to 2025
using "Totally untested"-style wording or "Not-yet-signed-off-by", most of them his own patches.

---

## 14. Performance claims need numbers, and the numbers belong in the commit message

**Principle.** An optimisation or a complexity-for-speed trade needs measurements: for the case it improves *and* for
the normal case, and evidence that the code matters at all (it shows in profiles). Handwaving ("this could be bad
under heavy load") is not an argument, for or against. Put the numbers in the commit.

**What triggers it in a review.**
- "Optimize", "speed up", "reduce overhead" in a message with no measurements.
- Added inlining, caching, lock splitting, or a new tunable with no profile showing the code is hot.
- Objections to a change based on imagined worst cases with no data.

**His reasoning.** "Micro-optimizations need numbers. Otherwise they aren't micro-optimizations, they are just
"change code randomly"" (2018). Complexity is a real cost and needs a measured benefit to pay for it.

**How serious.** Refuses to pull optimisation work without numbers from a submitter who has burned him (2024 "New
rule"); refuses to bring back removed complexity "before _you_ start posting numbers" (2016).

**Limits and exceptions.** When the change makes the code simpler or the generated code obviously better, he accepts
it even if a measurement "simply may not be possible" (2022). He states his own beliefs as unmeasured when they are
(2023 "I have no numbers to back that up"). Numbers from an artificial benchmark are acceptable if labelled as such
(his own 2010 commit).

**Outside the kernel.** Transfers fully. Ask for before/after benchmarks and a profile for any performance PR; reject
added complexity justified by speed with no data; accept simplifications on their own merit.

**Evidence.**
- "If you have performance improvement numbers for just this one patch, I have no objections (but it would be good to then make those numbers part of the commit message)." (`Pine.LNX.4.64.0607091646210.5623@g5.osdl.org`, 2006-07-09, https://lore.kernel.org/all/Pine.LNX.4.64.0607091646210.5623%40g5.osdl.org/)
- "Micro-optimizations need numbers. Otherwise they aren't micro-optimizations, they are just "change code randomly"." (`CA+55aFxTve6FxLuvWyyD88ACOg+3eHKbpWUeuvNZMSB=AFfuqg@mail.gmail.com`, 2018-06-05, https://lore.kernel.org/all/CA%2B55aFxTve6FxLuvWyyD88ACOg%2B3eHKbpWUeuvNZMSB%3DAFfuqg%40mail.gmail.com/)
- "Some kind of "look, this code is visible in profiles, so we actually care"." (`CAHk-=wiUTXC452qbypG3jW6XCZGfc8d-iehSavxn5JkQ=sv0zA@mail.gmail.com`, 2024-06-20, https://lore.kernel.org/all/CAHk-%3DwiUTXC452qbypG3jW6XCZGfc8d-iehSavxn5JkQ%3Dsv0zA%40mail.gmail.com/)
- "The numbers I want is performance numbers, not handwave numbers. Both for the bad case that it's supposed to fix, *and* for "normal load"." (`alpine.LFD.0.999.0710091955100.3838@woody.linux-foundation.org`, 2007-10-10, https://lore.kernel.org/all/alpine.LFD.0.999.0710091955100.3838%40woody.linux-foundation.org/)
- "We don't add crazy complexity without numbers." (`CA+55aFxoT82RocOCZ9+k7_NZ+KZNtCQrwzNd=reB0n03xDj4-A@mail.gmail.com`, 2016-11-04, https://lore.kernel.org/all/CA%2B55aFxoT82RocOCZ9%2Bk7_NZ%2BKZNtCQrwzNd%3DreB0n03xDj4-A%40mail.gmail.com/)
- Limit: "It would be particularly nice if you can also see any change in performance numbers - but that simply may not be possible." (`CAHk-=wiEQeRuAwHYOS6oBmewLBXg6Nd6xMPmMz2E75f660TDSA@mail.gmail.com`, 2022-09-10, https://lore.kernel.org/all/CAHk-%3DwiEQeRuAwHYOS6oBmewLBXg6Nd6xMPmMz2E75f660TDSA%40mail.gmail.com/)

**How well supported.** Strong: about 18 messages, 2002 to 2026.

---

## 15. Churn is a real cost: don't touch code that does not need touching

**Principle.** Renames, interface reshuffles, mass style conversions, "add missing newline" sweeps, and repeated
rework of the same interface all cost reviewers, mergers, `git blame` users and people backporting fixes, even when
each change is harmless. A churn patch has to fix a real problem or clearly make the code better.

**What triggers it in a review.**
- Tree-wide or repo-wide mechanical edits with no functional reason (SPDX style, adding `\n`, renaming for taste).
- An API change that forces 150 mechanical call-site edits.
- Repeated reshuffles of the same area across releases.
- "Cleanups" of fragile low-level code with no test coverage.

**His reasoning.** "pointless churn is BAD. It's a real expense" (2020): it pollutes `get_maintainer` and `git blame
-C`, causes merge conflicts, confuses people who instrument or depend on the interfaces, and buggy cleanups break
things (2015, 2017).

**How serious.** Refuses trivial-tree pulls of churn (2016); demands people "put your foot down" on more churn
(2017); threatened to stop taking low-level cleanups (2015).

**Limits and exceptions.** Whitespace-only patches are welcome, and preferable to whitespace mixed with fixes,
especially as preparation for real work on neglected code (2004). Scripted churn is fine when planned and announced,
typically just after rc1 (2026). Churn bundled with a change that needs the rename anyway is easier to justify (2013).

**Outside the kernel.** Transfers fully. Push back on drive-by reformatting, mass renames and "modernisation" PRs that
fix nothing; if a formatter must be adopted, do it once in its own announced commit (and add it to the blame-ignore
list).

**Evidence.**
- "The fact is, pointless churn is BAD. It's a real expense. The whole "get it over with once" argument is simply completely wrong." (`CAHk-=wi2bdXuYhC9bd9FShtcf_u-6RUb3Qr_aXq3XtbCxR5NGQ@mail.gmail.com`, 2020-04-27, https://lore.kernel.org/all/CAHk-%3Dwi2bdXuYhC9bd9FShtcf_u-6RUb3Qr_aXq3XtbCxR5NGQ%40mail.gmail.com/)
- Same message: "Or "git blame -C" things that I have to ignore and go past that history because the scripted change showed an (uninteresting) change."
- "Here's a hint: if some stupid change requires you to mindlessly do 150 changes using a wrapper helper, it's churn." (`CA+55aFwrpd+fz3jxK3d6dckFcApc=aCZOrsKogxRYZozwUdHrg@mail.gmail.com`, 2017-09-07, https://lore.kernel.org/all/CA%2B55aFwrpd%2Bfz3jxK3d6dckFcApc%3DaCZOrsKogxRYZozwUdHrg%40mail.gmail.com/)
- "It's bogus stupid churn that doesn't actually make the source code better, and it also doesn't actually seem to fix any behavioral issues." (`CA+55aFyMPLmxKdYK70Omhpq3SehHqdA3L97mM5dsiw-OTnhG8Q@mail.gmail.com`, 2016-10-07, https://lore.kernel.org/all/CA%2B55aFyMPLmxKdYK70Omhpq3SehHqdA3L97mM5dsiw-OTnhG8Q%40mail.gmail.com/)
- "These "cleanups" have been buggy as hell, and test coverage for the compat case is clearly lacking." (`CA+55aFyhOgoZRGemkda5igTdqyOSrb-hP1nAmCcfMbtFUmq5HQ@mail.gmail.com`, 2015-08-13, https://lore.kernel.org/all/CA%2B55aFyhOgoZRGemkda5igTdqyOSrb-hP1nAmCcfMbtFUmq5HQ%40mail.gmail.com/)
- Limit: "So I don't have any real issues with applying whitespace-only patches, and I much prefer them to patches that mix whitespace and bugfixes." (`Pine.LNX.4.58.0401200953470.2123@home.osdl.org`, 2004-01-20, https://lore.kernel.org/all/Pine.LNX.4.58.0401200953470.2123%40home.osdl.org/)
- Limit: "I like things like automated churn at the end - IF I HAVE BEEN TOLD ABOUT AHEAD OF TIME and know to expect it" (`CAHk-=wimz+APb9hGEry+vHDLB5D7WZvNGWU89HjGw7wH15KGHg@mail.gmail.com`, 2026-08-28, https://lore.kernel.org/all/CAHk-%3Dwimz%2BAPb9hGEry%2BvHDLB5D7WZvNGWU89HjGw7wH15KGHg%40mail.gmail.com/)

**How well supported.** Strong: about 18 messages, 2004 to 2026.

---

## 16. Tool output is not a reason: mechanical changes say how they were made, and tool-added metadata must be conscious

**Principle.** A change produced by a tool (checkpatch, coccinelle, sed, an LLM, `b4`) must still be justified by a
human, and the commit should say which tool was used and include the script or prompt. Style-checker warnings are not
a reason to edit existing code. Automatically added tags (Link, Cc) must be curated, not copied.

**What triggers it in a review.**
- "Fix checkpatch warnings" or "make linter happy" patches on existing, working code, especially ones that make the
  code uglier (wrapped strings, contorted macros).
- Search-and-replace patches that also touch entirely correct code.
- Mechanical sweeps with no script in the message.
- Trailers or Cc lists that are obviously auto-generated.
- AI-assisted changes with no disclosure of the tool or how it was used.

**His reasoning.** Checkpatch rules are heuristics, "Not things that then cause people to make code worse." (2025),
and "Just because you can reliably automate it doesn't make it relevant information" (2025). For tools, the existing
rule for scripts already covers AI: describe the tool and the script, because the reader needs to know how a change
was produced to judge it.

**How serious.** Mostly a refusal to apply or a strong objection; he has repeatedly floated removing checkpatch
(2007, 2008). For AI, a statement of policy, not a rejection.

**Limits and exceptions.** Checkpatch is "probably fine for new patches" (2023). Mechanical patches done with a script
are fine, and his own commits include the script (2018 `chmod -x` commit). AI is "a tool, just like other tools we
use" (2026) and he treats LLM-written text as "perfectly acceptable use of tooling" (2026). A targeted subset of an
automated change is welcome where the blanket version is not (2021).

**Outside the kernel.** Transfers fully: reject lint-driven churn on untouched code; require codemod scripts or
generator commands in the commit; treat AI-generated changes like any generated change (disclose, explain, verify);
check that auto-generated trailers and reviewers lists mean something.

**Evidence.**
- "running checkpatch on pre-existing code and making "trivial changes" based on it, and trying to get the warnings down to zero is THE WRONG THING TO DO." (`CAHk-=wgfzPOao+Rbq4aSitQ2gPaZ9PPGbR290X4BikD_W8ZcUg@mail.gmail.com`, 2023-02-22, https://lore.kernel.org/all/CAHk-%3DwgfzPOao%2BRbq4aSitQ2gPaZ9PPGbR290X4BikD_W8ZcUg%40mail.gmail.com/)
- "People seem to get way too hung up on ".. but at least it passes checkpatch"." (`alpine.LFD.2.00.0912170816210.15740@localhost.localdomain`, 2009-12-17, https://lore.kernel.org/all/alpine.LFD.2.00.0912170816210.15740%40localhost.localdomain/)
- "IOW, this should all be about "tool-assisted patches should be described as such, and should explain how the tool was used"." (`CAHk-=wgEPve=BO=SOmgEOd4kv76bSbm0jWFzRzcs4Y7EedpgfA@mail.gmail.com`, 2025-11-10, https://lore.kernel.org/all/CAHk-%3DwgEPve%3DBO%3DSOmgEOd4kv76bSbm0jWFzRzcs4Y7EedpgfA%40mail.gmail.com/)
- Same message: "If people send in patches that have been generated by tools, we already ask people to just include the script in the commit message."
- "it seems to be a mindless "just search-and-replace everything", very much for initializers that didn't complain even with gcc-4.9, and that were entirely correct." (`CAHk-=wiyq84MKRd1F4d8SGTcTgdd3ktwPr7_9s8tjgKRx_+2kA@mail.gmail.com`, 2021-09-13, https://lore.kernel.org/all/CAHk-%3Dwiyq84MKRd1F4d8SGTcTgdd3ktwPr7_9s8tjgKRx_%2B2kA%40mail.gmail.com/)
- "Just because you can reliably automate it doesn't make it relevant information." (`CAHk-=wjcTwA5E7YT8KT6=87nQaJ78A0hqUAVGo9bYRWt9dTe3Q@mail.gmail.com`, 2025-08-28, https://lore.kernel.org/all/CAHk-%3DwjcTwA5E7YT8KT6%3D87nQaJ78A0hqUAVGo9bYRWt9dTe3Q%40mail.gmail.com/)
- "That said, they are *more* useful when they are thought about, than when they are automated." (`CAHk-=wicuM=0iMeRCrbG=MMLZRdwihpZ64rWxDqidEjMa-YDsA@mail.gmail.com`, 2021-10-21, https://lore.kernel.org/all/CAHk-%3DwicuM%3D0iMeRCrbG%3DMMLZRdwihpZ64rWxDqidEjMa-YDsA%40mail.gmail.com/)

**How well supported.** Strong for checkpatch and automated tags (about 15 messages, 2007 to 2025); moderate for AI
disclosure (about 8 messages, 2025 to 2026; current but recent).

---

## 17. A pull request says what, why, what is odd, and why now; he refuses one he cannot understand or verify

**Principle.** The pull request (or PR description) is the explanation of a batch of work and becomes the merge
message, so it must be a human summary: what it does, why to take it, anything unusual (files outside your area,
recent rebases, known conflicts and their resolutions, late timing). It must match the tree. Let the integrator do
cross-tree merges; tell them about conflicts instead of resolving them by merging each other's trees.

**What triggers it in a review.**
- Descriptions that ramble about background but never say what the change does.
- A reformatted commit list instead of a summary.
- Diffstat touching other teams' files with no mention.
- Commits all dated today with no word about it.
- A branch that does not contain what the description claims.
- Unsigned or unverifiable sources (kernel-specific: signed tags).
- Sub-teams merging each other's branches to "pre-resolve" conflicts.

**His reasoning.** "I also want to use that message as the message for the merge, so it should not just make sense to
me, but make sense as a historical record too" (2017). If something odd is unexplained, "I'll just be extra
suspicious". If he does the merge himself he knows where the conflict was when a bug appears (2019).

**How serious.** Refuses or unpulls: 2026 "I'm not pulling this" over an "incomprehensible word salad" even though the
code looked fine; 2013 "I literally *cannot* pull this"; 2024 unsigned tag. Many more are pulled with a complaint.

**Limits and exceptions.** Trivial conflicts need no re-spin and he resolves them himself; he only wants a heads-up
(2023). An occasional oddity with an explanation is "perfectly fine" (2023). For a pull of a few commits a list of
details is a summary (2016).

**Outside the kernel.** Transfers fully: a PR description should be a summary a reader could use as the merge commit;
call out unusual scope, timing and history; don't merge other teams' unmerged branches to save the integrator work.

**Evidence.**
- "The code looks fine, but I had to *look* at the code to try to even guess at what the hell you asked me to pull, and that's not fine." (`CAHk-=wh0gCvsC7A9z_H7her218kSCmd16dqtd9uMfO5ZrSvxLw@mail.gmail.com`, 2026-10-26, https://lore.kernel.org/all/CAHk-%3Dwh0gCvsC7A9z_H7her218kSCmd16dqtd9uMfO5ZrSvxLw%40mail.gmail.com/)
- "Note that if there is something odd about the pull request, that should very much be in the explanation. If you're touching files that you don't maintain, explain _why_." (`CA+55aFyCu3_Qx2oBLO8229kSDqaM5SfNhB_L1ironkmiBF8-gA@mail.gmail.com`, 2017-11-14, https://lore.kernel.org/all/CA%2B55aFyCu3_Qx2oBLO8229kSDqaM5SfNhB_L1ironkmiBF8-gA%40mail.gmail.com/)
- Same message: "explain not just what they do and why they do it, but explain the _timing_."
- "I really prefer a _summary_. Something that is human-legible." (`CA+55aFzH+RrkebTvWYtvXOqMmQfrSy=coxt0ms9RGzN3kzxf4g@mail.gmail.com`, 2016-11-26, https://lore.kernel.org/all/CA%2B55aFzH%2BRrkebTvWYtvXOqMmQfrSy%3Dcoxt0ms9RGzN3kzxf4g%40mail.gmail.com/)
- Limit: "If you know there's something odd going on but you had a particular reason to do it that way, just mention it." (`CAHk-=wiNnK--B_K7DHvU28PKX00fUpb9oUmSq9OpkOLPDrMkUQ@mail.gmail.com`, 2023-04-25, https://lore.kernel.org/all/CAHk-%3DwiNnK--B_K7DHvU28PKX00fUpb9oUmSq9OpkOLPDrMkUQ%40mail.gmail.com/)
- "So I literally *cannot* pull this, because the git tree doesn't contain what you said it contains." (`CA+55aFzo-sA4P_rMC1wWfLp50QswfP0GdLxMQ+Wbw8ArK5capw@mail.gmail.com`, 2013-10-23, https://lore.kernel.org/all/CA%2B55aFzo-sA4P_rMC1wWfLp50QswfP0GdLxMQ%2BWbw8ArK5capw%40mail.gmail.com/)
- "I say this to somebody pretty much every single merge window: don't do merges for me." (`CAHk-=wj_L9d8P0Kmtb5f4wudm=KGZ5z0ijJ-NxTY-CcNcNDP5A@mail.gmail.com`, 2019-05-08, https://lore.kernel.org/all/CAHk-%3Dwj_L9d8P0Kmtb5f4wudm%3DKGZ5z0ijJ-NxTY-CcNcNDP5A%40mail.gmail.com/)
- "(a) it's unsigned, and I really don't pull from unsigned sources any more" (`CAHk-=whMS56xLhb7cAmTri2sXtGxK_zKWhZVX87YzjwAfVqTqQ@mail.gmail.com`, 2024-05-26, https://lore.kernel.org/all/CAHk-%3DwhMS56xLhb7cAmTri2sXtGxK_zKWhZVX87YzjwAfVqTqQ%40mail.gmail.com/)

**How well supported.** Very strong: 30+ messages, 2011 to 2026.

---

## 18. Attribution and sign-off: credit the right people, never certify for someone else, record reporters and testers

**Principle.** `Signed-off-by` records the path a patch took and certifies the right to pass it on; it is not
authorship and nobody may add it for anyone else, nor after the fact. Authorship must be preserved through every
tool. Reporters, testers and whoever root-caused the bug get credit in the commit itself, and finding the cause often
deserves more credit than writing the one-line fix.

**What triggers it in a review.**
- The committer listed as author of others' work.
- Sign-offs added for co-authors who did not sign.
- Late Acked-by/Tested-by added to already-published commits.
- Fixes for reported bugs with no Reported-by/Tested-by.
- Credit for root-causing a bug swallowed by the author of the trivial fix.

**His reasoning.** The sign-off chain documents "the path it has come through" and the "chain of trust" (2004).
Practically, whoever signs off "will be bothered by email if that patch turns out to be buggy" (2005). Forging a
sign-off is "like faking somebody else's signature" (2023). Bug reporting and testing are "a fundamental part of
commit logs" (2021).

**How serious.** Pulled but corrected for lost authorship (2006); a firm "no" to adding someone else's sign-off (2023).

**Limits and exceptions.** He waives authorship of his own throwaway "something like this" patches and asks that
credit go to whoever tested or found the bug (2019, 2021). Late acks are "worthless" rather than harmful; late
sign-offs are "actively _wrong_" (2009).

**Outside the kernel.** Transfers: preserve authorship when cherry-picking or squashing (`Co-authored-by`), credit
reporters and testers in the commit, never add a DCO sign-off or approval on another person's behalf. Projects without
a DCO keep the attribution half.

**Evidence.**
- "So what I'm suggesting is that we start "signing off" on patches, to show the path it has come through, and to document that chain of trust." (`Pine.LNX.4.58.0405222341380.18601@ppc970.osdl.org`, 2004-05-23, https://lore.kernel.org/all/Pine.LNX.4.58.0405222341380.18601%40ppc970.osdl.org/)
- "it means that the person is convinced he has the legal right to pass it on as a GPL'd piece of code." and "anybody who signs off or acknowledges a patch will be bothered by email if that patch turns out to be buggy" (`Pine.LNX.4.64.0512291340000.3298@g5.osdl.org`, 2005-12-29, https://lore.kernel.org/all/Pine.LNX.4.64.0512291340000.3298%40g5.osdl.org/)
- "Nobody can certify sign-off for anybody else." (`CAHk-=wg_E5qAOTtZ6BSJph1zDN7Unzw_ct8wK1pr+E8HTnooRw@mail.gmail.com`, 2023-02-09, https://lore.kernel.org/all/CAHk-%3Dwg_E5qAOTtZ6BSJph1zDN7Unzw_ct8wK1pr%2BE8HTnooRw%40mail.gmail.com/)
- "Yes, the sign-offs look fine, but still, attribution and credit is _important_." (`Pine.LNX.4.64.0606202001520.5498@g5.osdl.org`, 2006-06-21, https://lore.kernel.org/all/Pine.LNX.4.64.0606202001520.5498%40g5.osdl.org/)
- "Pulled, but I wanted to point out how bug reporting and testing is a fundamental part of commit logs, not some secondary thing." (`CAHk-=wgE+ngSaKxv1MW+un1f=N4QnC0jFC46b3nNZinQRnZj0g@mail.gmail.com`, 2021-09-17, https://lore.kernel.org/all/CAHk-%3DwgE%2BngSaKxv1MW%2Bun1f%3DN4QnC0jFC46b3nNZinQRnZj0g%40mail.gmail.com/)
- "*Fixing* this ends up being a one-liner or so. Finding the cause was the painful part." (`CA+55aFxyvr-PVWaOe_PGjej4gGMdfF_Moq0a3A9xZ6gGWAQjbQ@mail.gmail.com`, 2018-02-22, https://lore.kernel.org/all/CA%2B55aFxyvr-PVWaOe_PGjej4gGMdfF_Moq0a3A9xZ6gGWAQjbQ%40mail.gmail.com/)
- "And 'signed-off-by' are actively _wrong_ to add later. If it didn't come with a sign-off in the first place, it shouldn't have been committed." (`alpine.LFD.2.01.0910271200060.31845@localhost.localdomain`, 2009-10-27, https://lore.kernel.org/all/alpine.LFD.2.01.0910271200060.31845%40localhost.localdomain/)

**How well supported.** Strong: about 15 messages, 2004 to 2023.

---

## 19. His own commit messages: what a good one contains

Read about 30 of his commits from `source = 'git'`, `kind = 'commit'` (2007 git, 2010s to 2026 linux), plus his own
patch emails. A good commit from him has a consistent shape:

1. **Subject**: `area: imperative summary`, lower-case after the prefix, specific ("pipe: don't use 'pipe_wait() for
   basic pipe IO", "minmax: scsi: fix mis-use of 'clamp()' in sr.c").
2. **The problem, first, in plain words**: who reported it and what they saw ("Anatoly Trosinenko reports that a
   corrupted squashfs image can cause a kernel oops."), or what was wrong with the old code and why it matters.
3. **The mechanism**: why the old code misbehaves, often with a short quoted code fragment or the exact wrong call.
4. **The fix in one or two sentences**, and why this fix rather than another.
5. **Honest scope and risk**: whether anyone could have hit it ("Happily, I don't think anybody ever cared."),
   whether generated code changes ("the generated code does not change"), how the bug hid ("if you ask for patches
   when following ... the bug is hidden"), benchmark numbers labelled as artificial.
6. **Trailers that mean something**: `Reported-by`, `Fixes:` with SHA and subject, `Debugged-by`, `Requested-by`,
   tested-by when amended in, `Link:` only to an external report or CI run, the script when the change is mechanical.

It is conversational but dense: no "This patch", no filler, short paragraphs, and every claim checkable against the diff.

**Model 1: a revert that says what broke and why** (`7af08140979a6e7e12b78c93b8625c8d25b084e2`, 2021-04-19, https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=7af08140979a6e7e12b78c93b8625c8d25b084e2):

```
Revert "gcov: clang: fix clang-11+ build"

This reverts commit 04c53de57cb6435738961dace8b1b71d3ecd3c39.

Nathan Chancellor points out that it should not have been merged into
mainline by itself. It was a fix for "gcov: use kvmalloc()", which is
still in -mm/-next. Merging it alone has broken the build.

Link: https://github.com/ClangBuiltLinux/continuous-integration2/runs/2384465683?check_suite_focus=true
Reported-by: Nathan Chancellor <nathan@kernel.org>
Cc: Johannes Berg <johannes.berg@intel.com>
Cc: Nick Desaulniers <ndesaulniers@google.com>
Cc: Andrew Morton <akpm@linux-foundation.org>
Signed-off-by: Linus Torvalds <torvalds@linux-foundation.org>
```

**Model 2: a bug fix that shows the wrong code and its effect** (`9f499b8c791d2983c0a31a543c51d1b2f15e8755`, 2024-07-29, https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=9f499b8c791d2983c0a31a543c51d1b2f15e8755):

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

**Model 3: a design change explained as problem, approach, why it is safe** (`85190d15f4ea88e60047256fecb8216d5323ea47`, 2019-12-07, https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=85190d15f4ea88e60047256fecb8216d5323ea47):

```
pipe: don't use 'pipe_wait() for basic pipe IO

pipe_wait() may be simple, but since it relies on the pipe lock, it
means that we have to do the wakeup while holding the lock.  That's
unfortunate, because the very first thing the waked entity will want to
do is to get the pipe lock for itself.

So get rid of the pipe_wait() usage by simply releasing the pipe lock,
doing the wakeup (if required) and then using wait_event_interruptible()
to wait on the right condition instead.

wait_event_interruptible() handles races on its own by comparing the
wakeup condition before and after adding itself to the wait queue, so
you can use an optimistic unlocked condition for it.

Cc: David Howells <dhowells@redhat.com>
Signed-off-by: Linus Torvalds <torvalds@linux-foundation.org>
```

(The subject's unbalanced quote and "ddid" are his typos, kept verbatim.)

Other short passages from his commits used as evidence (all in the quotes file): "Anatoly Trosinenko reports that a
corrupted squashfs image can cause a kernel oops." (`01cfb7937a9a`, 2018-07-29); "No, I don't think we've ever hit
that issue in practice, but since we now have sane infrastructure for doing this right, let's just use it."
(`21b136cc63d2`, 2024-07-30); "alpha has no user_access_begin(), so the scope is the same access_ok() followed by the
same plain accesses, and the generated code does not change." (`ef9a9b616a6f`, 2026-10-20); a mechanical commit that
includes its script: "A simple git command line to show executable C/asm/header files is this:" (`90fda63fa115`,
2018-04-07); his 2007 git fix explaining how the bug hid: "Because of the nature of the bug, if you ask for patches
when following (which is one of the things I normally do), the bug is hidden" (`alpine.LFD.0.999.0710081337490.4964@woody.linux-foundation.org`);
a labelled benchmark: "On Hiroyuki-san's load, this trivial change improved his (admittedly _very_ artificial)
page-fault benchmark by about 2%." (`alpine.LFD.2.00.1001121708100.17145@localhost.localdomain`, 2010-01-13). On
`Fixes:` tags: "I really would like to see "Fixes" tags in general" (`CAHk-=whyYBFw+o9RRyGXvfS+ipQgGAM1oHFL9KXFoCCkRvrTfA@mail.gmail.com`, 2026-07-22).

---

## Changes of position over time

| Topic | Earlier | Later / current |
|---|---|---|
| `Link:` tags | Around 2011 he suggested a Link to the submission as the alternative to change-ID UUIDs (his own account, 2025-09-05) | From 2022 a sustained campaign against links to the submission; 2025 proposes `b4 dig` and hook-added comments instead. Current: links only when they add information |
| checkpatch | 2007 to 2009: considered removing it ("nazi dream", 80 columns "causing too many idiotic changes") | 2023: fine for new patches, wrong for existing code; 2025: cut it down to "obvious and real issues". The objection narrowed; it never reversed |
| Tool and AI patches | No AI-specific position before 2025 | 2025-11: treat AI like any tool (disclose, give the prompt like a script). 2026: firmly "Linux is not one of those anti-AI projects"; LLM-written text acceptable if it is concise and imperative; but "STOP THINKING THAT YOU - OR AI - NEVER ADD BUGS WHEN YOU FIX SOMETHING" (2026-11-24). Current: tool-neutral, disclosure required, same quality bar |
| Imperative mood | Not raised in the 2000s material read | Repeated from 2020 to 2026, for pull text as well as commits. Treated as taste |
| Late pulls / linux-next | 2001 policy already strict about post-release patches | From about 2011, whether it has been in linux-next became an explicit test; 2016 he says "I've been lax about this" and starts refusing rebased late pulls |
| Tone | Before 2018: profanity, "SH*T", "shit-for-brains" in rejections | After 2018 fewer insults aimed at people, but the same severity and still sharp language in 2025 to 2026 ("Get your shit together"). The standards did not soften; the target moved from people to behaviour |
| Rebasing | 2008: encouraged for individual developers, discouraged for maintainers | Unchanged through 2026; the 2014 three-exceptions list is the stable statement |

No reversal on the core demands (why, one change per commit, bisectability, merge messages, timing) was found in 25
years of material.

## Not in corpus

Searched for and not found as quotes in `corpus.db` (do not quote them):

- The kernel's `Documentation/process/submitting-patches.rst` text itself (the "describe your changes in imperative
  mood" sentence appears only as his quotation of it in 2020, inside his own mail).
- `Documentation/maintainer/rebasing-and-merging.rst` text; he points to it (2019, 2024, 2026) but the document is not
  in the corpus.
- The often-repeated line about "good commit messages ... 50/72 rule": not found.
- No Usenet-era (1991 to 1995) material on commit or patch etiquette beyond diffs posted inline; the theme effectively
  starts in 2000.

## Looked for and did not find (or found thin)

- **Fixes stacked on unmerged work** as a named rule: only 4 or 5 messages (2011, 2021 revert, 2022 fold requests).
  The principle is clear but not heavily repeated.
- **Wrong tense** as a ground for rejection: never; it is always a "matter of taste" edit.
- **Patch size limits as numbers**: none of his own; the only number is the stable tree's 100-line rule, which he
  cites (2024), not invents.
- **Commit message length rules** (line wrap widths): none found.
- **Explicit statements about squash-merging** (as on GitHub): none; transfer to squash workflows above is my
  inference.
- **AI-generated commit messages being rejected for being AI**: none; 2026 messages accept them if concise.
- **Positive praise of specific commit messages by others**: rare (2001 "useful real-life user information", 2021
  "great explanation" of a bug report, 2021 Rafael cross-tree heads-up). His praise is mostly for bug reports and
  pull requests that warned him of conflicts, not for commit prose.
