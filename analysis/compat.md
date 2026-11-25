# Compat: Linus Torvalds on never breaking users

Theme: the "we do not break userspace" rule and everything that follows from it, including what counts as a regression, reverts, interface design, defaults, deprecation, the internal-API contrast, and the same instinct in git. Every quote below is his own words, taken from `corpus.db` and checked with `scripts/verify_quotes.py` against the jsonl file `analysis/compat.quotes.jsonl`. URLs come from the `docs.url` column. Message ids are listed so the full context can be pulled with `bin/linus-search`.

Principles are ordered from the core rule outward. P1 to P7 say what a regression is and what to do about one. P8 to P11 cover how to design an interface so the rule stays cheap to keep. P12 and P13 cover removal and the limits of the rule. P14 and P15 cover the internal-API contrast and lock-step upgrades. P16 covers git.

---

## P1. No regressions is the first rule, because users must feel safe upgrading

**Principle.** Breaking user space is a kernel bug, whatever the reason for the change. The rule exists so that people upgrade without fear, not to get old bugs fixed. Keeping old interfaces working is cheaper overall than handling the downstream cost of a regression.

**What triggers it in a review.** Any patch description that admits a user-visible change in behaviour and justifies it ("cleanup", "more correct", "matches POSIX now", "nobody should rely on this"). It also triggers on a maintainer's NAK of a revert, or on any suggestion that users should upgrade something else to keep working.

```c
/* before: returns -EINVAL for an unknown cmd; after the "cleanup": */
-	return -EINVAL;
+	return -ENOTTY;	/* "the correct errno" */
/* If any shipped binary checks for EINVAL, this is a regression,
 * even though ENOTTY is what POSIX says. */
```

**His reasoning.** Upgrades only happen when they are painless ("if you make upgrades painful, it just means that people will stay back"). Regressions waste the time of everyone downstream, about ten times more than fixing an old bug. The kernel exists to serve user space. Libraries and anything else other programs build on are held to the same standard: a change there breaks every program that depends on it.

**How serious.** Absolute in tone and in action. He overrides maintainers' NAKs and calls ABI change "for its own sake" disqualifying, for kernel and library developers alike.

**Limits and exceptions.** See P13 (security, nobody noticing for years, test-only breakage, out-of-tree code).

**Outside the kernel.** For a library, CLI, service API or schema owner, a release must be something consumers can take without reading the changelog. If an upgrade needs coordinated changes downstream, users will pin the old version and stop upgrading, and from then on they get no fixes either. In his 2025 talk he names libraries and their dependants explicitly.

**Evidence.**
- "The reason we have that "no regression" rule is not so that we fix up bugs. It's because peopel should always feel safe upgrading their kernel, and basically _know_ that kernel developers consider it unacceptable to break user space."  
  `CA+55aFysKDXr2HEwNzm3z9QOw=E4ZeWcvYQ-xLhy5_k+rGbeRg@mail.gmail.com`, 2015-06-29, https://lore.kernel.org/all/CA%2B55aFysKDXr2HEwNzm3z9QOw%3DE4ZeWcvYQ-xLhy5_k%2BrGbeRg%40mail.gmail.com/
- "The fact is, regressions are about 10x more costly than fixing old bugs. They cause problems downstream that just waste everybodys time. It's a _hell_ of a lot more efficient to spend extra time to keep old interfaces stable than it is to cause regressions."  
  `Pine.LNX.4.64.0602220848280.30245@g5.osdl.org`, 2006-02-22, https://lore.kernel.org/all/Pine.LNX.4.64.0602220848280.30245%40g5.osdl.org/
- "Your job as a kernel developer is very much to support the users. Not try to make it easy for *you* at the cost of being nasty for *them*."  
  `CA+55aFy5yB2d-1iXEUtU+puua4TAmV0kZF_7TBhXO1Y4Khqb9Q@mail.gmail.com`, 2015-01-04, https://lore.kernel.org/all/CA%2B55aFy5yB2d-1iXEUtU%2Bpuua4TAmV0kZF_7TBhXO1Y4Khqb9Q%40mail.gmail.com/
- "Because if you make upgrades painful, it just means that people will stay back."  
  `https://techcrunch.com/2012/04/19/an-interview-with-millenium-technology-prize-finalist-linus-torvalds/`, 2012-04-19, https://techcrunch.com/2012/04/19/an-interview-with-millenium-technology-prize-finalist-linus-torvalds/
- "when you're doing a library that other people rely on, uh or when you're doing a kernel that libraries rely on that other people then rely on, you're not just fixing your own bug, you're breaking all the programs that rely on your project."  
  `https://www.youtube.com/watch?v=yEzdHYjY_RU`, 2025-12-19, https://www.youtube.com/watch?v=yEzdHYjY_RU
- "There are exactly *zero* reasons to change the ABI for its own sake, and this whole thread is a wonderful example of how F*CKING STUPID it was to even consider it."  
  `CA+55aFyjvESz3FZwAdnOuZX7R5B0ES0Vj3SngikA1A9PqTcoyQ@mail.gmail.com`, 2012-09-30, https://lore.kernel.org/all/CA%2B55aFyjvESz3FZwAdnOuZX7R5B0ES0Vj3SngikA1A9PqTcoyQ%40mail.gmail.com/
- "but anybody who does it on purpose "just because" should not be involved in kernel development (or library development for that matter)."  
  `CA+55aFyjvESz3FZwAdnOuZX7R5B0ES0Vj3SngikA1A9PqTcoyQ@mail.gmail.com`, 2012-09-30, https://lore.kernel.org/all/CA%2B55aFyjvESz3FZwAdnOuZX7R5B0ES0Vj3SngikA1A9PqTcoyQ%40mail.gmail.com/

**How well supported.** Strong. Dozens of messages in the corpus state the rule outright. The ones cited here run from 2006 to 2025, and the rule recurs in 2026 threads (see P2 to P4).

---

## P2. A regression is defined by what users actually see, not by docs, specs, intent or tests

**Principle.** Something is a regression when a user's existing workflow stops working. The definition does not depend on documented behaviour, where the code lives, what the developer intended, or whether a test suite changed its result. If nobody notices a change, it was not a regression. Conversely, an interface is whatever people can see and use, whether or not anyone meant it to be one.

**What triggers it in a review.** Arguments such as "this was never documented", "the docs say X", "userspace shouldn't use that file", "it was only under a debug option", "the intent was always ...". It also triggers on a test-suite diff presented as proof of breakage, or as proof that nothing broke.

**His reasoning.** Documentation that disagrees with behaviour is simply wrong documentation. An intent that the code does not check for is worth nothing. In practice it is usually harder to work out whether a change breaks someone than simply not to change the behaviour, so the working rule becomes "try to avoid intentionally changing behavior".

**How serious.** This is the definition everything else hangs on. He repeats it whenever a maintainer argues from the spec.

**Limits and exceptions.** The weasel words are deliberate: the behaviour must be one "that people use", and the breakage must be noticeable. A test-suite failure on its own is a red flag, not a regression. A debug-only interface that was never enabled in real builds is not ABI.

**Outside the kernel.** Hyrum's law, applied as policy. A CLI's exact output, an API's undocumented ordering, error-code choice, timing and the fields in a JSON response all become contract once a consumer depends on them. Saying "the docs never promised that" does not excuse the break. Either make a behaviour impossible to depend on (validate it, randomize it, hide it), or treat it as contract.

**Evidence.**
- "The rules about regressions have never been about any kind of documented behavior, or where the code lives. The rules about regressions are always about "breaks user workflow"."  
  `CAHk-=wiVi7mSrsMP=fLXQrXK_UimybW=ziLOwSzFTtoXUacWVQ@mail.gmail.com`, 2020-05-21, https://lore.kernel.org/all/CAHk-%3DwiVi7mSrsMP%3DfLXQrXK_UimybW%3DziLOwSzFTtoXUacWVQ%40mail.gmail.com/
- "No amount of "you shouldn't have used this" or "that behavior was undefined, it's your own fault your app broke" or "that used to work simply because of a kernel bug" is at all relevant."  
  `CAHk-=wiVi7mSrsMP=fLXQrXK_UimybW=ziLOwSzFTtoXUacWVQ@mail.gmail.com`, 2020-05-21, https://lore.kernel.org/all/CAHk-%3DwiVi7mSrsMP%3DfLXQrXK_UimybW%3DziLOwSzFTtoXUacWVQ%40mail.gmail.com/
- "For example, a test-suite giving a different result is *not* a regression, although it should obviously be considered a big red flag."  
  `CA+55aFz0cjsS4BTwtBt9P1pKHmPjXPYnOvFuP07UVoek7jSYLw@mail.gmail.com`, 2015-01-08, https://lore.kernel.org/all/CA%2B55aFz0cjsS4BTwtBt9P1pKHmPjXPYnOvFuP07UVoek7jSYLw%40mail.gmail.com/
- "So the very definition of "regression" is not really about the API changing, but about breaking peoples existing setups."  
  `CA+55aFz0cjsS4BTwtBt9P1pKHmPjXPYnOvFuP07UVoek7jSYLw@mail.gmail.com`, 2015-01-08, https://lore.kernel.org/all/CA%2B55aFz0cjsS4BTwtBt9P1pKHmPjXPYnOvFuP07UVoek7jSYLw%40mail.gmail.com/
- "But in practice, it's often _much_ more work to try to figure out whether something breaks somebody than it is to just say "don't change behavior", so 99% of the time, the rule ends up being just "try to avoid intentionally changing behavior, because you'll likely get it wrong"."  
  `CAHk-=wh0LsuM+kAZGbDaogDdSbdCk3GvXmjYVAMkpmLj2=VF=g@mail.gmail.com`, 2018-10-26, https://lore.kernel.org/all/CAHk-%3Dwh0LsuM%2BkAZGbDaogDdSbdCk3GvXmjYVAMkpmLj2%3DVF%3Dg%40mail.gmail.com/
- "If people rely on "Y", then pointing at the docs and saying "but you should never have relied on it, because teh docs say X" is totally and utterly bogus. The _documentation_ was wrong."  
  `alpine.LFD.2.00.0812011843340.3256@nehalem.linux-foundation.org`, 2008-12-02, https://lore.kernel.org/all/alpine.LFD.2.00.0812011843340.3256%40nehalem.linux-foundation.org/
- "Any "intent" that isn't actually enforced by _checking_ for it is only wishful thinking, and worth nothing at all."  
  `CAHk-=wiLdmz92CCfu2+-9_UrGSn6Pu6sUVvLs5gjyhGaEov-BA@mail.gmail.com`, 2026-04-27, https://lore.kernel.org/all/CAHk-%3DwiLdmz92CCfu2%2B-9_UrGSn6Pu6sUVvLs5gjyhGaEov-BA%40mail.gmail.com/
- "The only "ABI guarantee" is what people actually see and use, not some debug option that wasn't enabled."  
  `CAHk-=wjsEqWJxXArS-P5+ksSY2Apaox8u6FtUrtyWSBEOL4Q2Q@mail.gmail.com`, 2026-04-23, https://lore.kernel.org/all/CAHk-%3DwjsEqWJxXArS-P5%2BksSY2Apaox8u6FtUrtyWSBEOL4Q2Q%40mail.gmail.com/

**How well supported.** Strong. More than 15 messages across 2006 to 2026.

---

## P3. Bugs people depend on are part of the interface

**Principle.** If user space depends on a bug, fixing the bug is a regression, and the fix gets reverted. The rule does not freeze the interface. It means "you cannot make any changes that break applications". Where a fix is necessary (security), the kernel still tries to look as if it behaves the same way.

**What triggers it in a review.** A "fix" for long-standing odd behaviour, such as an errno, a rounding rule, a flag accepted silently or an ordering, with no survey of who relies on it. It also triggers on a regression report met with "the application was doing something wrong".

```c
/* Fix the bug, but keep the observable result users depend on. */
if (legacy_caller_pattern(args))
	return old_visible_result;	/* comment why: app X depends on it */
```

**His reasoning.** User space was tested against the old behaviour, so the old behaviour is what it relies on, and choosing that behaviour was "on us". He does revert based on user-reported *behaviour*. He does not revert just because some formal ABI changed with nobody affected.

**How serious.** High. Revert is the expected outcome, often with a comment in the source so nobody "fixes" it again.

**Limits and exceptions.** Security fixes go ahead, though they try to keep the visible behaviour the same. Some regressions cannot be fixed (pure timing races, see P13), which he still calls regressions.

**Outside the kernel.** When fixing a parser that accepted malformed input, a library that returned the wrong error type, or an API that sorted results by accident, first ask who relies on it. Then keep the old behaviour as the default and offer the corrected behaviour through an opt-in (P8), or keep the old visible result for the patterns that were really in use.

**Evidence.**
- "If it used to work, it should continue to work, even if it wasn't _meant_ to work."  
  `alpine.LFD.1.10.0806232004480.2926@woody.linux-foundation.org`, 2008-06-24, https://lore.kernel.org/all/alpine.LFD.1.10.0806232004480.2926%40woody.linux-foundation.org/
- "If we fix a bug, and it turns out that user space actually depends on that bug, then we need to revert the fix. But it never means "you can never make any changes at all to interfaces". It only means "you cannot make any changes that break applications"."  
  `BANLkTi=6W0quy1M71UapwKDe97E67b4EiA@mail.gmail.com`, 2011-06-28, https://lore.kernel.org/all/BANLkTi%3D6W0quy1M71UapwKDe97E67b4EiA%40mail.gmail.com/
- "But yes, let's try to fix it, and if it turns out that that breaks something, we must simply revert and probably add a comment to the source code"  
  `BANLkTi=6W0quy1M71UapwKDe97E67b4EiA@mail.gmail.com`, 2011-06-28, https://lore.kernel.org/all/BANLkTi%3D6W0quy1M71UapwKDe97E67b4EiA%40mail.gmail.com/
- "So if user space depends on specific historical kernel behavior, it's a regression when that behavior changes. It's on us: we were silly to have that non-optimal historical behavior, and our old kernel behavior was what user space was tested against."  
  `fe67f4dd8daa252eb9aa7acb61555f3cc3c1ce4c`, 2021-08-24, https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=fe67f4dd8daa252eb9aa7acb61555f3cc3c1ce4c
- "We remain bug-for-bug compatible with older kernel versions when people depend on the bugs. Unless the old bugs are security issues, and even then we try to make it _look_ like we work the same way."  
  `CA+55aFyAox9BTDpRsqLXiROhHOX60aa45LEZ7Azteaumdu11Fw@mail.gmail.com`, 2018-08-02, https://lore.kernel.org/all/CA%2B55aFyAox9BTDpRsqLXiROhHOX60aa45LEZ7Azteaumdu11Fw%40mail.gmail.com/
- "The point here being that we revert based on user-reported _behavior_, not based on some "it changes the ABI" or "it caused a bug" concept."  
  `CAHk-=wiP4K8DRJWsCo=20hn_6054xBamGKF2kPgUzpB5aMaofA@mail.gmail.com`, 2019-09-15, https://lore.kernel.org/all/CAHk-%3DwiP4K8DRJWsCo%3D20hn_6054xBamGKF2kPgUzpB5aMaofA%40mail.gmail.com/
- "Our regression rule for the kernel is that if applications break from new behavior, it's a regression, even if it was because the application did something patently wrong."  
  `3a34b13a88caeb2800ab44a4918f230041b37dd9`, 2021-07-30, https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=3a34b13a88caeb2800ab44a4918f230041b37dd9

**How well supported.** Strong. More than 10 messages and commits from 2008 to 2026.

---

## P4. Never blame the user, the application or the firmware

**Principle.** When a change breaks a user program, the bug is in the kernel. "Update your user space", "fix your app", "try a new firmware" and "work around it" are not acceptable answers, even when the application really is doing something stupid and even when a fixed version of it is on the way.

**What triggers it in a review.** A maintainer reply that tells the reporter to upgrade a library, tool, firmware or distro package. Also a NAK of a revert on the grounds that user space was buggy.

**His reasoning.** The old setup worked, so as far as the kernel is concerned user space was doing the right thing. Waiting for every distribution to update the app leaves real users broken in the meantime. Once other user space starts relying on the new behaviour, the problem compounds, so the breakage has to be fixed quickly.

**How serious.** This is where his tone is harshest (2012, 2018). He has explicitly overridden maintainers on it.

**Limits and exceptions.** It is not a rule that user space never changes. New features may require new tools (P13). The rule is that existing setups must keep working.

**Outside the kernel.** When a new release of a service, SDK or CLI breaks a client, "the client was misusing the API" is not a resolution. Fix it on the server or library side, or revert, and file the client issue separately. Never require clients to deploy at the same time (P15).

**Evidence.**
- "If a change results in user programs breaking, it's a bug in the kernel. We never EVER blame the user programs. How hard can this be to understand?"  
  `CA+55aFy98A+LJK4+GWMcbzaa1zsPBRo76q+ioEjbx-uaMKH6Uw@mail.gmail.com`, 2012-12-23, https://lore.kernel.org/all/CA%2B55aFy98A%2BLJK4%2BGWMcbzaa1zsPBRo76q%2BioEjbx-uaMKH6Uw%40mail.gmail.com/
- "As far as the kernel is concerned, a regressions is THE KERNEL NOT GIVING THE SAME END RESULT WITH THE SAME USER SPACE."  
  `CA+55aFwiiQYJ+YoLKCXjN_beDVfu38mg=Ggg5LFOcqHE8Qi7Zw@mail.gmail.com`, 2017-10-26, https://lore.kernel.org/all/CA%2B55aFwiiQYJ%2BYoLKCXjN_beDVfu38mg%3DGgg5LFOcqHE8Qi7Zw%40mail.gmail.com/
- "It's not ok to say "but we'll fix the user space setup"."  
  `CA+55aFwiiQYJ+YoLKCXjN_beDVfu38mg=Ggg5LFOcqHE8Qi7Zw@mail.gmail.com`, 2017-10-26, https://lore.kernel.org/all/CA%2B55aFwiiQYJ%2BYoLKCXjN_beDVfu38mg%3DGgg5LFOcqHE8Qi7Zw%40mail.gmail.com/
- "Eric, I want to make this 1000% clear: there are no user space bugs. If it used to work, then user space was clearly doing the right thing."  
  `CAHk-=wjd2VJDM+RXwg30MpW45F5EHZtLErzxQzYxi4+Dnm3sjw@mail.gmail.com`, 2018-12-22, https://lore.kernel.org/all/CAHk-%3Dwjd2VJDM%2BRXwg30MpW45F5EHZtLErzxQzYxi4%2BDnm3sjw%40mail.gmail.com/
- "And the same way we don't tell people "update your buggy user space" when we introduce kernel regressions, we don't tell people "try a new firmware"."  
  `CA+55aFw1LWO+zxePYtUBi9YOWHPX+98xbM2h3j4pcN+6V0G1zA@mail.gmail.com`, 2014-08-14, https://lore.kernel.org/all/CA%2B55aFw1LWO%2BzxePYtUBi9YOWHPX%2B98xbM2h3j4pcN%2B6V0G1zA%40mail.gmail.com/
- "So even if an app is getting updated eventually, the kernel breakage should be fixed."  
  `CA+55aFxk8-BsiKwr_S-c+4G6wihKPQVMLE34H9wOZpeua6W9+Q@mail.gmail.com`, 2015-08-14, https://lore.kernel.org/all/CA%2B55aFxk8-BsiKwr_S-c%2B4G6wihKPQVMLE34H9wOZpeua6W9%2BQ%40mail.gmail.com/
- "We don't then turn around and say "you were clever, and we did something stupid, so now we'll hurt you"."  
  `CAHk-=wh=B3fqU9AaBsyViZR=eVTG5qa2CGyN=qxPROVxu9Gctg@mail.gmail.com`, 2026-04-23, https://lore.kernel.org/all/CAHk-%3Dwh%3DB3fqU9AaBsyViZR%3DeVTG5qa2CGyN%3DqxPROVxu9Gctg%40mail.gmail.com/
- "I need to know so that I can override the bogus NAK, and so that we can fix the breakage ASAP. The absolute last thing we need is some other user space then starting to rely on the new behavior, which just compounds the problem and makes it a *much* bigger problem."  
  `CAHk-=wg-6jYZ=bJWdyBR=n8QOfwHTZZdzSUUPgFW+NGCV-pe2g@mail.gmail.com`, 2018-12-22, https://lore.kernel.org/all/CAHk-%3Dwg-6jYZ%3DbJWdyBR%3Dn8QOfwHTZZdzSUUPgFW%2BNGCV-pe2g%40mail.gmail.com/

**How well supported.** Strong. More than 10 messages from 2011 to 2026.

---

## P5. Revert is the default answer, and it should be fast

**Principle.** When a regression is traced to a known commit and there is no obvious, safe fix, revert it, preferably within a week and before the next rc. A revert is safe in a way a new fix is not. The only people who could notice a revert are those for whom the change never worked, while a new fix may break a "silent mass" of untested users. Revert, then rethink.

**What triggers it in a review.** A regression report on which the maintainer proposes a new, cleverer fix, or which sits waiting for a root-cause analysis while rc releases go by.

**His reasoning.** Developers become attached to their changes and see reverting as too drastic. Old, reliable behaviour is better than new problems. Reverting buys time to think about the issue.

**How serious.** High during the rc window. He does it himself if maintainers do not.

**Limits and exceptions.** The bias goes the other way late in a cycle or for old changes. A change that already shipped in an earlier release will not be reverted just before the next one ("would be more dangerous"), and a regression that took a decade to find "can't be that critical". A known, acceptable real fix is better than a revert.

**Outside the kernel.** For a service or library, roll back first and debug afterwards. Treat a regression found in a pre-release as cheap to revert and one found after release as needing care. Measure your time to revert.

**Evidence.**
- "In contrast, reverting something will be guaranteed to not have those kinds of issues, since the only people who could notice are people for who it never worked in the first place. There's no "silent mass of people" that can be affected."  
  `alpine.LFD.0.9999.0712091036380.12046@woody.linux-foundation.org`, 2007-12-09, https://lore.kernel.org/all/alpine.LFD.0.9999.0712091036380.12046%40woody.linux-foundation.org/
- "So we should revert unless there is some known acceptable real fix."  
  `alpine.LFD.0.9999.0712091036380.12046@woody.linux-foundation.org`, 2007-12-09, https://lore.kernel.org/all/alpine.LFD.0.9999.0712091036380.12046%40woody.linux-foundation.org/
- "But if it's a regression with a known commit that caused it, I think the rule of thumb should generally be "within a week", preferably before the next rc."  
  `CAHk-=wi86AosXs66-yi54+mpQjPu0upxB8ZAfG+LsMyJmcuMSA@mail.gmail.com`, 2026-01-28, https://lore.kernel.org/all/CAHk-%3Dwi86AosXs66-yi54%2BmpQjPu0upxB8ZAfG%2BLsMyJmcuMSA%40mail.gmail.com/
- "I think people are sometimes a bit too bought into whatever changes they made, and reverting is seen as "too drastic", but I think it's often the quick and easy solution for when there isn't some obvious response to a regression report."  
  `CAHk-=wi86AosXs66-yi54+mpQjPu0upxB8ZAfG+LsMyJmcuMSA@mail.gmail.com`, 2026-01-28, https://lore.kernel.org/all/CAHk-%3Dwi86AosXs66-yi54%2BmpQjPu0upxB8ZAfG%2BLsMyJmcuMSA%40mail.gmail.com/
- "Generally, I think that if there are regressions reports that come in while we're still in the -rc series and the problem hasn't hit an actual release yet, it's probably worth reverting simply to get time to think about the issue more."  
  `CAHk-=whFuDumk75VTTWeXzGfCQae4=XT-k8MdYWrca5JtcMrBw@mail.gmail.com`, 2026-03-21, https://lore.kernel.org/all/CAHk-%3DwhFuDumk75VTTWeXzGfCQae4%3DXT-k8MdYWrca5JtcMrBw%40mail.gmail.com/
- "Michal, our rules are very simple: we don't generate regressions. It's better to have old reliable behavior than to start creating *new* problems."  
  `CAHk-=whrfDw4yV4h2ijbX3vpXf5m4hzJ5pGX7_v6pU31RGib-g@mail.gmail.com`, 2018-12-03, https://lore.kernel.org/all/CAHk-%3DwhrfDw4yV4h2ijbX3vpXf5m4hzJ5pGX7_v6pU31RGib-g%40mail.gmail.com/
- "Does a plain revert just fix everything? Because if so, that's the right thing to do, and we can just re-visit this later."  
  `CA+55aFw5DzEn+jYmY0KwbkytBzowo45o3Czh1cQZ_aaR1+WZYA@mail.gmail.com`, 2015-08-13, https://lore.kernel.org/all/CA%2B55aFw5DzEn%2BjYmY0KwbkytBzowo45o3Czh1cQZ_aaR1%2BWZYA%40mail.gmail.com/
- "That said, this already went into 6.5, so I'm not going to revert it now just before the 6.6 release. That would be more dangerous than just letting things be."  
  `CAHk-=wgEHNFHpcvnp2X6-fjBngrhPYO=oHAR905Q_qk-njV31A@mail.gmail.com`, 2023-10-29, https://lore.kernel.org/all/CAHk-%3DwgEHNFHpcvnp2X6-fjBngrhPYO%3DoHAR905Q_qk-njV31A%40mail.gmail.com/

**How well supported.** Strong. About 10 messages from 2007 to 2026, with the one-week guidance in 2026.

---

## P6. A fix that breaks something else is not a fix

**Principle.** It is not acceptable to fix one thing and break another, even if the new case matters more to the author. Things that used to work are "a million times more important" than things that never worked. A consistent set of known bugs is better than bugs that move around.

**What triggers it in a review.** A patch that makes new hardware, a spec-compliant case or a test pass, at the cost of a configuration that worked before. Also any "weighing" argument that the new benefit outweighs the old breakage.

**His reasoning.** The rule came out of the suspend/resume and ACPI years, when "fix one machine, break another" went back and forth without progress. A stable base with known, documented problems lets users rely on their machine either working or not. Specs, including firmware specs, are less important than users.

**How serious.** High. A patch that causes a regression is "by definition" not a fix and gets reverted whatever it fixed.

**Limits and exceptions.** Cases that never worked are not regressions if they still do not work. A change may knowingly re-introduce an old bug in order to remove a new regression.

**Outside the kernel.** When a library change fixes one consumer's bug and breaks another's working code, revert it and find a fix that keeps both, usually behind an option. In a migration, a schema change that fixes a new feature but breaks an existing query path is a regression.

**Evidence.**
- "We revert stuff whether it "fixed" something else or not. The rule is "NO REGRESSIONS". It doesn't matter one whit if something "fixes" something else or not - if it breaks an old case, it gets reverted."  
  `CA+55aFxcqczXZf7zxJ0xjDsnLMbS8uu9Jp5BDOdnR5tqf==nrA@mail.gmail.com`, 2013-02-23, https://lore.kernel.org/all/CA%2B55aFxcqczXZf7zxJ0xjDsnLMbS8uu9Jp5BDOdnR5tqf%3D%3DnrA%40mail.gmail.com/
- "Things that used to work are simply a million times more important than things that historically didn't work."  
  `CA+55aFxcqczXZf7zxJ0xjDsnLMbS8uu9Jp5BDOdnR5tqf==nrA@mail.gmail.com`, 2013-02-23, https://lore.kernel.org/all/CA%2B55aFxcqczXZf7zxJ0xjDsnLMbS8uu9Jp5BDOdnR5tqf%3D%3DnrA%40mail.gmail.com/
- "Other cases - that never worked - are not regressions if they continue to not work."  
  `CAHk-=wi7DB2SJ-wngVvsJ7Ak2cM556Q8437sOXo4EJt2BWPdEg@mail.gmail.com`, 2021-09-20, https://lore.kernel.org/all/CAHk-%3Dwi7DB2SJ-wngVvsJ7Ak2cM556Q8437sOXo4EJt2BWPdEg%40mail.gmail.com/
- "The constant "one step forward, two steps back" dance was what made us have that hard rule about regressions, because it's better to have a stable base with known problems - that you can perhaps document - than have a base where the problems just shift around like quicksand"  
  `CAHk-=wh8dnp1qT_CHG-Zz9H2=G1Q=0rF5SYv+YsEaPnVhznxWA@mail.gmail.com`, 2026-03-20, https://lore.kernel.org/all/CAHk-%3Dwh8dnp1qT_CHG-Zz9H2%3DG1Q%3D0rF5SYv%2BYsEaPnVhznxWA%40mail.gmail.com/
- "There's no "weighing what is more important". None. Users are a million times more important than specs or tests."  
  `CAHk-=wh8dnp1qT_CHG-Zz9H2=G1Q=0rF5SYv+YsEaPnVhznxWA@mail.gmail.com`, 2026-03-20, https://lore.kernel.org/all/CAHk-%3Dwh8dnp1qT_CHG-Zz9H2%3DG1Q%3D0rF5SYv%2BYsEaPnVhznxWA%40mail.gmail.com/
- "Regressions need to be fixed even if it may even re-introduce another long-time bug - simply because we're much better off with a _consistent_ set of bugs where people can depend on their machine either working or not, than with some kind of unstable situation that never gets anywhere"  
  `alpine.LFD.2.01.0906231156220.3240@localhost.localdomain`, 2009-06-23, https://lore.kernel.org/all/alpine.LFD.2.01.0906231156220.3240%40localhost.localdomain/
- "The strict policy of no regressions actually originally started mainly wrt suspend/resume issues, where the "fix one machine, break another" kind of back-and-forth caused endless problems, and meant that we didn't actually necessarily make any forward progress, just moving a problem around."  
  `CA+55aFxk8-BsiKwr_S-c+4G6wihKPQVMLE34H9wOZpeua6W9+Q@mail.gmail.com`, 2015-08-14, https://lore.kernel.org/all/CA%2B55aFxk8-BsiKwr_S-c%2B4G6wihKPQVMLE34H9wOZpeua6W9%2BQ%40mail.gmail.com/

**How well supported.** Strong. About 10 messages from 2009 to 2026, plus the 2025 talk.

---

## P7. Performance regressions count when real workloads hit them

**Principle.** A slowdown is a regression when real users or real workloads see it. Microbenchmarks do not prove it either way. Showing that a change is faster on a synthetic test does not answer a real workload getting slower, and a benchmark-only slowdown can wait until someone complains.

**What triggers it in a review.** A report of a slower real workload answered with a different benchmark ("look, a helicopter!"). Also the reverse: a benchmark-only slowdown used to block a change without evidence from a workload.

**His reasoning.** The real programs users run decide, even if those programs are inefficient or "insane". Since insane programs never go away, it is better to fix the performance problem than to scold them.

**How serious.** Medium to high. A slowdown confirmed on a real workload leads to a revert (memcg 2021, 2018 THP case).

**Limits and exceptions.** Benchmark-only slowdowns, or bad benchmarks, are a reason to watch and wait, not to revert.

**Outside the kernel.** Latency and throughput are part of an API's contract when clients are built around them, for example timeouts, batch sizes and query plans. Gate releases on real traffic replays rather than microbenchmarks, and treat a confirmed production slowdown as a rollback trigger.

**Evidence.**
- "It doesn't matter one whit if SLUB is lots faster, if it's faster for cases that never matter."  
  `alpine.LFD.0.9999.0712211442000.21557@woody.linux-foundation.org`, 2007-12-21, https://lore.kernel.org/all/alpine.LFD.0.9999.0712211442000.21557%40woody.linux-foundation.org/
- "I don't mind performance regressions, but I *do* mind performance regressions when the main author then says "look, a helicopter!" and points to some totally different thing and claims that the performance regression doesn't even exist!"  
  `alpine.LFD.0.9999.0712211442000.21557@woody.linux-foundation.org`, 2007-12-21, https://lore.kernel.org/all/alpine.LFD.0.9999.0712211442000.21557%40woody.linux-foundation.org/
- "Let's ignore this issue for now, and see if it shows up in some real workload and people complain."  
  `CAHk-=wjgRO-=NPaU9EmrdC3it3o7kvf4u7sewv3crtNLkE13Hg@mail.gmail.com`, 2018-11-28, https://lore.kernel.org/all/CAHk-%3DwjgRO-%3DNPaU9EmrdC3it3o7kvf4u7sewv3crtNLkE13Hg%40mail.gmail.com/
- "Well, David Rientjes points out that it *does* cause real problems in real workloads, so it's not just this benchmark run that shows the issue. So I guess we should revert, or at least fix."  
  `CAHk-=wjgpWOA7zQ9H5=Zj6KQijm5CBXZc7J=it6C5gdEV0hb5Q@mail.gmail.com`, 2018-12-03, https://lore.kernel.org/all/CAHk-%3DwjgpWOA7zQ9H5%3DZj6KQijm5CBXZc7J%3Dit6C5gdEV0hb5Q%40mail.gmail.com/
- "And let's face it, user programs doing odd and not very efficient things should be considered par for the course. We're never going to get rid of insane user programs, so we might as well fix the performance problems even when we say "that's just stupid"."  
  `CA+55aFyed_pvUwCXSgyqvOa6VCkuE-qgFPi0CRqcnOWuXiAECQ@mail.gmail.com`, 2016-08-12, https://lore.kernel.org/all/CA%2B55aFyed_pvUwCXSgyqvOa6VCkuE-qgFPi0CRqcnOWuXiAECQ%40mail.gmail.com/

**How well supported.** Moderate. About 6 messages from 2007 to 2023. The corpus has many performance threads but few explicit statements of this as a rule.

---

## P8. New behaviour gets a new opt-in, not a new version and not a change to the old path

**Principle.** New behaviour does not go into an old interface where it would break old callers. Add a flag (or a new call) that says "I want the new behaviour", and leave the old interface working. User space should never test kernel versions. It should try the new call and fall back to the old one. Version numbers do not help existing users, because existing binaries do not know about version 6.

**What triggers it in a review.** A patch that changes the semantics of an existing syscall, ioctl or file format, with the justification that new code wants it. Also an interface that advertises a version for callers to check, or user space that sniffs `uname`.

```c
/* wrong: change what flags==0 means */
/* right: */
#define FOO_NEW_SEMANTICS 0x1
if (flags & ~FOO_VALID_FLAGS) return -EINVAL;
if (flags & FOO_NEW_SEMANTICS) return foo_new(...);
return foo_old(...);	/* unchanged forever */
```

**His reasoning.** The old interface has to be kept "basically forever" anyway, so a new call or flag adds convenience and replaces nothing. Explicit opt-in keeps the decision with the caller. Checking capability by trying the call degrades gracefully, and version checks do not.

**How serious.** High. It is the main thing that makes the no-regression rule cheap to keep.

**Limits and exceptions.** Valid reasons to change an ABI do exist: security, an implementation that cannot be kept, and real applications breaking. None of them is "for its own sake".

**Outside the kernel.** For a REST or gRPC API, add a field or parameter that opts into the new semantics instead of changing what the default does. For a CLI, add a new flag rather than changing the old one's output. For a library, add a new function or option and keep the old one. For a client, use feature detection (try it, handle "unknown"), not version comparison. In the 2025 talk he names Python 3.14 breaking user programs as the anti-pattern.

**Evidence.**
- "When we add NEW BEHAVIOUR, we don't add it to old interfaces when that breaks old user mode! We add a new flag saying "I want the new behaviour"."  
  `alpine.LFD.0.999.0708310055010.25853@woody.linux-foundation.org`, 2007-08-31, https://lore.kernel.org/all/alpine.LFD.0.999.0708310055010.25853%40woody.linux-foundation.org/
- "So, that's why the kernel has always had this rule that, "Hey, we don't make those kinds of improvements. If we're doing new things, we use new interfaces, and we leave the old interfaces alone in a working state.""  
  `https://www.youtube.com/watch?v=yEzdHYjY_RU`, 2025-12-19, https://www.youtube.com/watch?v=yEzdHYjY_RU
- "(because we *would* have to maintain the old interface basically forever, so it would be more of a "the new system call doesn't really deprecate the old one, it just has more convenient semantics")."  
  `CA+55aFxE+M54mSM7=nRP_frA7LDAQYyMW6UhcGq62hOP4bX5Kw@mail.gmail.com`, 2014-01-31, https://lore.kernel.org/all/CA%2B55aFxE%2BM54mSM7%3DnRP_frA7LDAQYyMW6UhcGq62hOP4bX5Kw%40mail.gmail.com/
- "Absolutely *no* user space shjould ever care about kernel versions. If you want to use a new system call or something, just *use* if, and then if it fails, fall back to the old one. Never ever check "what's the kernel version" or anything like that."  
  `CA+55aFyFXxN3Qkt+=Ke5Mqctbc3+iX5_HzeH0gHFZK8tDpa=Uw@mail.gmail.com`, 2018-08-03, https://lore.kernel.org/all/CA%2B55aFyFXxN3Qkt%2B%3DKe5Mqctbc3%2BiX5_HzeH0gHFZK8tDpa%3DUw%40mail.gmail.com/
- "So even in case 2, we do try to avoid versioning. More often we add a new flag, and say "hey, if you want the new behavior, use the new flag to say so". Not versioning, but explicit "I want the new behavior""  
  `CA+55aFyFXxN3Qkt+=Ke5Mqctbc3+iX5_HzeH0gHFZK8tDpa=Uw@mail.gmail.com`, 2018-08-03, https://lore.kernel.org/all/CA%2B55aFyFXxN3Qkt%2B%3DKe5Mqctbc3%2BiX5_HzeH0gHFZK8tDpa%3DUw%40mail.gmail.com/
- "A simple revert won't fix it, and saying "and here is version 6" won't matter one whit to existing packages."  
  `CA+55aFxEP7-+N7vTPZ-4hD-UirZ=+YMJh2x3EjZvUmjjyOchtg@mail.gmail.com`, 2012-04-27, https://lore.kernel.org/all/CA%2B55aFxEP7-%2BN7vTPZ-4hD-UirZ%3D%2BYMJh2x3EjZvUmjjyOchtg%40mail.gmail.com/

**How well supported.** Strong. About 8 messages from 2007 to 2025.

---

## P9. Design new interfaces so they can be extended, and enforce the rules from day one

**Principle.** Give a new syscall a flags argument, or an extensible struct, and reject unknown bits and non-zero padding from the start, so the space is free for later use. Never take a bare `bool`. The semantics must make sense conceptually, not reflect "random implementation issue of the day". Validation added after the fact is itself a regression, and a sign that you should not do it at all.

**What triggers it in a review.** A new syscall or ioctl with no flags argument, a flags argument that is not checked, a `bool` parameter, a user-visible struct with implicit padding or kernel types in it, or a patch that starts rejecting flags that used to be silently accepted.

```c
struct foo_args {		/* uapi: fixed-size, aligned, no holes */
	__aligned_u64 addr;
	__aligned_u64 flags;	/* must be 0 for now */
};
if (args.flags & ~FOO_KNOWN_FLAGS)
	return -EINVAL;		/* day one, not later */
```

**His reasoning.** An ABI without hard checks is stuck with whatever semantics people assume. Unchecked bits get set at random by callers and can never be given a meaning. Keep the user-visible layout separate from the in-kernel struct so the kernel side can change. preadv2 and pwritev2 are his example of an interface that was extended lazily.

**How serious.** High for new uapi. His 2026 messages describe this as a lesson that "most new system calls have learnt".

**Limits and exceptions.** He also dislikes "random flags" with no coherent meaning (2023). Flags are for future extension, not a substitute for design.

**Outside the kernel.** Reject unknown fields in a request schema, or at least unknown values in enum and flag fields, from version 1 on. Reserve fields. Use an options object or bitmask rather than a positional boolean. Starting to reject input after release is a breaking change. In storage formats, give every record a flags or type field that readers check.

**Evidence.**
- "Maybe add a flag field (require it to be zero initially) just to allow any future expansion."  
  `CAHk-=wjS=xg12RVQdTNxEurjo21eXQBQO0D5My6Aox4LCfsO1A@mail.gmail.com`, 2023-10-17, https://lore.kernel.org/all/CAHk-%3DwjS%3Dxg12RVQdTNxEurjo21eXQBQO0D5My6Aox4LCfsO1A%40mail.gmail.com/
- "This is why system calls and ABI's need to have hard rules that they actually check, because if they don't, they are stuck with the semantics that people assume."  
  `CAHk-=wh=B3fqU9AaBsyViZR=eVTG5qa2CGyN=qxPROVxu9Gctg@mail.gmail.com`, 2026-04-23, https://lore.kernel.org/all/CAHk-%3Dwh%3DB3fqU9AaBsyViZR%3DeVTG5qa2CGyN%3DqxPROVxu9Gctg%40mail.gmail.com/
- "Most new system calls have learnt their lesson, and they check for unused bits in flags etc, and error out on bits that the lernel doesn't really care about being randomly set - so that one day we *can* extend on things and start caring about them."  
  `CAHk-=wh=B3fqU9AaBsyViZR=eVTG5qa2CGyN=qxPROVxu9Gctg@mail.gmail.com`, 2026-04-23, https://lore.kernel.org/all/CAHk-%3Dwh%3DB3fqU9AaBsyViZR%3DeVTG5qa2CGyN%3DqxPROVxu9Gctg%40mail.gmail.com/
- "Now *IF* the interfaces had had these kinds of flag validation checks from day one, that would be one thing. But adding these kinds of things after the fact, when somebody then reports that they break things, then that's just a big big flag that you shouldn't try to do this at all."  
  `CA+55aFx+NrXEtd4bveFbZqw0r9UHxkrQ7rzdZBbfBiGdvEX3zw@mail.gmail.com`, 2015-04-17, https://lore.kernel.org/all/CA%2B55aFx%2BNrXEtd4bveFbZqw0r9UHxkrQ7rzdZBbfBiGdvEX3zw%40mail.gmail.com/
- "Particularly for new system calls with fairly specialized use, I think it's very important that the semantics are sensible on a conceptual level, and that we do not add system calls that are based on "random implementation issue of the day"."  
  `CAHk-=wiVhHmnXviy1xqStLRozC4ziSugTk=1JOc8ORWd2_0h7g@mail.gmail.com`, 2023-12-14, https://lore.kernel.org/all/CAHk-%3DwiVhHmnXviy1xqStLRozC4ziSugTk%3D1JOc8ORWd2_0h7g%40mail.gmail.com/
- "So the *user* visible structure should be full of those __aligned_u64 to make sure everything is aligned and doesn't care about compat models. But the *kernel* structure that we use should be nice and tailored for kernel use, and use proper kernel types."  
  `CAHk-=wieuV4hGwznPsX-8E0G2FKhx3NjZ9X3dTKh5zKd+iqOBw@mail.gmail.com`, 2019-05-26, https://lore.kernel.org/all/CAHk-%3DwieuV4hGwznPsX-8E0G2FKhx3NjZ9X3dTKh5zKd%2BiqOBw%40mail.gmail.com/
- "Nobody should ever use 'bool' as a system call argument. Anything that takes a boolean should take a 'flags' field with bits."  
  `CAHk-=wip3mwLOHOYJ9TtjDxOaq9YUXmuCg2AycyASGgeY6qqUw@mail.gmail.com`, 2026-06-04, https://lore.kernel.org/all/CAHk-%3Dwip3mwLOHOYJ9TtjDxOaq9YUXmuCg2AycyASGgeY6qqUw%40mail.gmail.com/
- "Of course, the real take-away is that "preadv2/pwritev2()" is a horrible interface. It should have been more extensible, rather than the lazy "just add another flag argument"."  
  `CAHk-=wi37_ccWmq1EKTduS8ms_=KpyY2LwJV7roD+s=ZkBkjCw@mail.gmail.com`, 2021-06-24, https://lore.kernel.org/all/CAHk-%3Dwi37_ccWmq1EKTduS8ms_%3DKpyY2LwJV7roD%2Bs%3DZkBkjCw%40mail.gmail.com/

**How well supported.** Strong. About 8 messages from 2015 to 2026, with more of them after 2019.

---

## P10. Keep the user-visible surface small: ioctls, text files and tracepoints all become ABI

**Principle.** Every user-visible thing is interface: syscalls, ioctls, /proc, /sys, netlink byte streams, tracepoints that tools pick up, and the field layout of text files. Each ioctl is effectively a new syscall. The thinnest interface is best, and doing the job automatically with no interface at all is better still, because it hides the implementation and leaves room to change it. If something can be used without parsing its self-description, you are stuck with its current form.

**What triggers it in a review.** A new ioctl added casually. A tracepoint exposing scheduler internals. A procfs or sysfs field removed or reordered. A "self-describing" format offered as the excuse for changing a layout. A tunable added where automatic behaviour would do.

```text
/proc/meminfo: field no longer meaningful?
  -> keep the line, report 0. Tools grep for it.
```

**His reasoning.** Tools "root around for values" and break when a field disappears. Theory about self-description does not matter, because binary compatibility is what users depend on. Generic attributes are better than private ioctls because they can be listed and scripted. Internal tracepoints lock the implementation in place.

**How serious.** High. It is the main design lever for keeping P1 affordable.

**Limits and exceptions.** Tracepoints and sysfs are usually less of a problem than ioctls. They become ABI only once real tools depend on them.

**Outside the kernel.** Each public endpoint, CLI flag, metric name, log line that people parse, and column in a CSV export is a promise. Expose less. Prefer automatic behaviour to a knob. When a field loses its meaning, keep it with a neutral value instead of deleting it. Do not expose internal state through debug endpoints that tooling can latch onto.

**Evidence.**
- "It's _not_ just system calls. It's any user-visible stuff. That very much includes /proc, /sys, and any "kernel pipes" aka netlink etc bytestreams."  
  `Pine.LNX.4.64.0602220848280.30245@g5.osdl.org`, 2006-02-22, https://lore.kernel.org/all/Pine.LNX.4.64.0602220848280.30245%40g5.osdl.org/
- "(Which is something you can pretty much take for granted with ioctl's, of course. DO NOT CHANGE IOCTL'S. EVER!)"  
  `alpine.LFD.1.10.0807311235350.3277@nehalem.linux-foundation.org`, 2008-07-31, https://lore.kernel.org/all/alpine.LFD.1.10.0807311235350.3277%40nehalem.linux-foundation.org/
- "What do you think ioctl's are? Every single ioctl number is an extra system call."  
  `https://yarchive.net/comp/linux/event_queues.html#6`, 2000-10-24, https://yarchive.net/comp/linux/event_queues.html#6
- "If you made an interface that can be used without parsing the interface description, then we're stuck with the interface. Theory simply doesn't matter."  
  `BANLkTim9YvResB+PwRp7QTK-a5VNg2PvmQ@mail.gmail.com`, 2011-05-06, https://lore.kernel.org/all/BANLkTim9YvResB%2BPwRp7QTK-a5VNg2PvmQ%40mail.gmail.com/
- "And an important thing to keep in mind is that "user interfaces are bad". The thinner the interface, the better."  
  `AANLkTinp45D+1XM4vc961RRHWK3WV_N7REY2=34X3ir8@mail.gmail.com`, 2010-11-16, https://lore.kernel.org/all/AANLkTinp45D%2B1XM4vc961RRHWK3WV_N7REY2%3D34X3ir8%40mail.gmail.com/
- "So doing things automatically and without any user interface is about _more_ than just convenience. If it can be done that way, it is fundamentally better way to do things. Because it hides the implementation details, and leaves us open to do totally different things in the end."  
  `AANLkTinp45D+1XM4vc961RRHWK3WV_N7REY2=34X3ir8@mail.gmail.com`, 2010-11-16, https://lore.kernel.org/all/AANLkTinp45D%2B1XM4vc961RRHWK3WV_N7REY2%3D34X3ir8%40mail.gmail.com/
- "But when then somebody writes a trace script that is so useful that distros pick it up, and people start using it and depending on it, then _that_ trace point may well have become effectively locked in stone."  
  `CA+55aFy5=74ad4tByQJYnkyX079z59yn02koJ_G8kfxamjvPDw@mail.gmail.com`, 2016-11-25, https://lore.kernel.org/all/CA%2B55aFy5%3D74ad4tByQJYnkyX079z59yn02koJ_G8kfxamjvPDw%40mail.gmail.com/
- "You can have a static tracepoint, but only for GENERIC stuff. Not random internal stuff that only makes sense to one scheduler implementation. We've made that mistake too many times before, we're not making it again."  
  `CA+55aFxzkwj8R+oqyw4ZpJf6Sm1Ubzy_LjSNi2_-LfcDE6bRuw@mail.gmail.com`, 2017-06-30, https://lore.kernel.org/all/CA%2B55aFxzkwj8R%2Boqyw4ZpJf6Sm1Ubzy_LjSNi2_-LfcDE6bRuw%40mail.gmail.com/
- "I can imagine system tools that just root around for values, and break and complain when they don't exist, even if all they do is report them"  
  `CA+55aFyWSAQE6pw2z0+QCuN=ckWv4QdzXuGyf+4VnUdUirOdWQ@mail.gmail.com`, 2015-11-02, https://lore.kernel.org/all/CA%2B55aFyWSAQE6pw2z0%2BQCuN%3DckWv4QdzXuGyf%2B4VnUdUirOdWQ%40mail.gmail.com/
- "Yeah, I think attributes are likely much better than some random crazy ioctl interface. They can be listed with generic tools, and have various scripting interfaces in ways that ioctl's do not sanely have."  
  `CA+55aFyFEW8LTEoyckW2YNeMrk5q_FweRsGbZKxXHWQjGLRw8w@mail.gmail.com`, 2017-07-08, https://lore.kernel.org/all/CA%2B55aFyFEW8LTEoyckW2YNeMrk5q_FweRsGbZKxXHWQjGLRw8w%40mail.gmail.com/

**How well supported.** Strong. More than 10 messages from 2000 to 2017. The sysfs-specific evidence is thinner than the ioctl and procfs evidence.

---

## P11. Defaults and config: new options default off, and never ask questions users cannot answer

**Principle.** New features start as `default n`. The exception is an old feature newly hidden behind an option, which defaults to on so existing configurations keep the old result. Do not ask users configuration questions they cannot answer: ask about hardware they have, and derive the rest. If the developer does not know the right answer, the user certainly does not. A change to an option's meaning or default needs a rename, so that `make oldconfig` asks the question again.

**What triggers it in a review.** `default y` on a new Kconfig option. A new question whose help text does not say who should enable it. An option rename or split that silently changes an existing user's resulting config.

```kconfig
config NEW_THING
	bool "Support new thing"
	default n		# new feature

config OLD_THING		# existing code, newly optional
	bool "Keep old thing"
	default y		# preserves old configs
```

**His reasoning.** Developers always want their own features on. A minimal working config is the goal. A user running `oldconfig` on an upgrade should get the same kernel they had before, without having to understand new questions.

**How serious.** Medium to high. He calls `default y` on new options "broken", and he fixed the XZ case himself in a commit.

**Limits and exceptions.** `default y` is right for old code made optional, for things almost everyone needs, and for options that are really dependencies.

**Outside the kernel.** New features in a CLI, library or service default off. Upgrading must not change what an existing config file produces. Do not ask users to choose settings that need knowledge of the internals: ask about their environment and derive the rest. When a setting's meaning changes, rename the key instead of reinterpreting it.

**Evidence.**
- "I'd really like the basic rule to be that all new features start out as 'default n'."  
  `CA+55aFwsTfGRkKASqa_LFQwGZnYyTdVTzb4MG=2Ywv+bG1E1Qw@mail.gmail.com`, 2012-01-07, https://lore.kernel.org/all/CA%2B55aFwsTfGRkKASqa_LFQwGZnYyTdVTzb4MG%3D2Ywv%2BbG1E1Qw%40mail.gmail.com/
- "The one exception is that when an *old* feature is hidden behind a *new* config option - if it used to be compiled in by default (even if that was for a bad reason), we should still default to compiling it in."  
  `CA+55aFwsTfGRkKASqa_LFQwGZnYyTdVTzb4MG=2Ywv+bG1E1Qw@mail.gmail.com`, 2012-01-07, https://lore.kernel.org/all/CA%2B55aFwsTfGRkKASqa_LFQwGZnYyTdVTzb4MG%3D2Ywv%2BbG1E1Qw%40mail.gmail.com/
- "For example, we have *way* too many questions that come about because some developer went "I don't know what the answer is, I'll just make it a Kconfig option". And I absolutely *HATE* those questions. Dammit, if the developer doesn't know, then a user sure as hell doesn't either."  
  `CAHk-=wj+4yA5jtzbTjctrk7Xu+88H=it2m5a-bpnnFeCQP7r=A@mail.gmail.com`, 2024-07-16, https://lore.kernel.org/all/CAHk-%3Dwj%2B4yA5jtzbTjctrk7Xu%2B88H%3Dit2m5a-bpnnFeCQP7r%3DA%40mail.gmail.com/
- "It's much better to ask people "do you have hardware XYZ" that they can hopefully answer, and then we enable all the things that hardware needs."  
  `CAHk-=wj+4yA5jtzbTjctrk7Xu+88H=it2m5a-bpnnFeCQP7r=A@mail.gmail.com`, 2024-07-16, https://lore.kernel.org/all/CAHk-%3Dwj%2B4yA5jtzbTjctrk7Xu%2B88H%3Dit2m5a-bpnnFeCQP7r%3DA%40mail.gmail.com/
- "Developers want their features to be enabled. Regardless of whether they are features that make sense to normal people."  
  `alpine.LFD.1.10.0805051337530.32269@woody.linux-foundation.org`, 2008-05-05, https://lore.kernel.org/all/alpine.LFD.1.10.0805051337530.32269%40woody.linux-foundation.org/
- "That means that anybody who upgrades their kernel and does a make oldconfig to update their configuration, will end up without the XZ compression that the configuration used to have."  
  `07953c54a10567e484cefd8f8c782025dc68b3b1`, 2022-06-03, https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=07953c54a10567e484cefd8f8c782025dc68b3b1
- "The one thing we might want to do is to rename the config option, simply to make sure that people who do "make oldconfig" will actually see the new question and hopefully pick the new default rather than just getting their old "y" without even seeing it."  
  `CA+55aFzdBf4GPyR-+FRy3PkBdvp0f7PJ1xCx6SSUU=WN=PvUzw@mail.gmail.com`, 2015-07-09, https://lore.kernel.org/all/CA%2B55aFzdBf4GPyR-%2BFRy3PkBdvp0f7PJ1xCx6SSUU%3DWN%3DPvUzw%40mail.gmail.com/

**How well supported.** Strong. About 10 messages and commits from 2007 to 2024.

---

## P12. Remove something only on evidence that nobody uses it: try the removal, be ready to restore it, and do not trust schedules

**Principle.** There is no time limit on compatibility. A deprecation schedule or a "feature-removal" entry is not evidence that a feature is unused. Either it is unused and can go now, or there is no excuse for removing it. The evidence he accepts is a removal that nobody notices: remove it aggressively, early in a cycle, and restore or stub it if someone complains. Warnings ("add some noise") can come first. A stub that does nothing can often satisfy the users who remain.

**What triggers it in a review.** "Deprecated for N releases, removing now." A removal with no investigation of users. A "legacy" interface turned off when current software still uses it.

**His reasoning.** Time does not stop users depending on something; only actual non-use does. Finding out early is better ("the sooner we find out, the better"). The Bluetooth legacy-ioctl revert shows that "legacy" users may be current ones.

**How serious.** High. He deleted `feature-removal-schedule.txt` itself.

**Limits and exceptions.** Hardware and architecture support can be dropped once no real users are left (386, and arch removals that can come back "not as a revert"). In his 2024 talk he admits that dropping 386 "in a sense" broke user space.

**Outside the kernel.** Do not delete an API version, CLI flag or config key because a sunset date has passed. Measure use (telemetry, logs, 404s), log a warning first, remove it in a release where rollback is easy, and keep a no-op stub if the remaining callers only need it to exist. For a database schema, keep the old column or view until queries against it have stopped.

**Evidence.**
- "There is no time limit. It's not about time. It's about not breaking user space."  
  `CA+55aFwSxwjqK8CScNBWvzk=ExDqREAGAyRoZLW4zjOu4dyxqw@mail.gmail.com`, 2012-11-13, https://lore.kernel.org/all/CA%2B55aFwSxwjqK8CScNBWvzk%3DExDqREAGAyRoZLW4zjOu4dyxqw%40mail.gmail.com/
- "If people reports it breaks user-space, we fix it. And we keep fixing things until nobody uses the old versions any more."  
  `CA+55aFwSxwjqK8CScNBWvzk=ExDqREAGAyRoZLW4zjOu4dyxqw@mail.gmail.com`, 2012-11-13, https://lore.kernel.org/all/CA%2B55aFwSxwjqK8CScNBWvzk%3DExDqREAGAyRoZLW4zjOu4dyxqw%40mail.gmail.com/
- "There is never any reason to add stuff to this idiotic file. Either something isn't getting used, and you should just remove it, or there is no excuse for removing it in the first place."  
  `9c0ece069b32e8e122aea71aa47181c10eb85ba7`, 2012-10-01, https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=9c0ece069b32e8e122aea71aa47181c10eb85ba7
- "It has also been the excuse for just plain bad behavior ("Hey, I don't like xyz, so let's mark it for removal" followed by "Hey, look, it been in feature-removal.txt for six months now, so we should remove it")."  
  `9c0ece069b32e8e122aea71aa47181c10eb85ba7`, 2012-10-01, https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=9c0ece069b32e8e122aea71aa47181c10eb85ba7
- "The usual reason for deprecating a feature is to give people time to move away from it, but since clearly nobody uses it..."  
  `alpine.LFD.2.00.1001221755320.13231@localhost.localdomain`, 2010-01-23, https://lore.kernel.org/all/alpine.LFD.2.00.1001221755320.13231%40localhost.localdomain/
- "so let's try removing them and seeing what happens. And then we know what we can do if somebody does actually notice."  
  `CA+55aFwG_ifxOQ7YLqbrRF3kqx8XAMesB3MHG2LQ_SF9RQH7Xw@mail.gmail.com`, 2015-08-25, https://lore.kernel.org/all/CA%2B55aFwG_ifxOQ7YLqbrRF3kqx8XAMesB3MHG2LQ_SF9RQH7Xw%40mail.gmail.com/
- "So rather than try to maintain a likely unused set of code, I'll just aggressively remove it, and see if anybody even notices."  
  `973c096f6a85e5b5f2a295126ba6928d9a6afd45`, 2020-09-09, https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=973c096f6a85e5b5f2a295126ba6928d9a6afd45
- "It turns out that the "legacy" users aren't so legacy at all, and that turning off the legacy ioctl will break the current Qt bluetooth stack for bluetooth LE devices that were released just a couple of months ago."  
  `e49aa15ef6c179f69e5578a271801f31a09e9a3f`, 2017-09-28, https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=e49aa15ef6c179f69e5578a271801f31a09e9a3f
- "The work-around might be as simple as creating an oom_adj file that simply doesn't do anything."  
  `CA+55aFz2Kgn0mVV4ozH0g1QGKw1VE6NpgCz9taxxfbCUz2a8VA@mail.gmail.com`, 2012-11-13, https://lore.kernel.org/all/CA%2B55aFz2Kgn0mVV4ozH0g1QGKw1VE6NpgCz9taxxfbCUz2a8VA%40mail.gmail.com/

**How well supported.** Strong. More than 10 messages and commits from 2010 to 2026.

---

## P13. The limits of the rule: security, nobody noticing, test-only failures, out-of-tree code, config files

**Principle.** The rule is about real users. That gives it real limits.
- Security fixes may break things, though they still try hard not to.
- A regression nobody notices for years is past fixing ("tough luck").
- If only one or two technically savvy users are affected and they can work around it, the bar is lower.
- A test failure is not a user failure.
- Out-of-tree code is not covered.
- Theoretical breakage does not count.
- Depending on the kernel's config file is broken by definition.
- Pure timing races are regressions that cannot be fixed.

**What triggers it in a review.** A regression claim based only on a test, an out-of-tree module, a hypothetical, or a change that is years old.

**His reasoning.** The point of the rule is users' workflows ("Schrödinger's cat": a regression nobody sees does not exist). Stretching it to tests and hypotheticals would freeze everything.

**How serious.** These are exceptions to a strict rule and he states them sparingly. Security is the only one he calls "the one exception".

**Outside the kernel.** Separate contract tests from incidental ones. A broken internal test is a signal to investigate, not proof of a break. Supported, published interfaces are covered. Private forks and internal-only consumers that bypass the published API are not, though see P2 on what counts as "published".

**Evidence.**
- "So the one exception to the regression rule is "security fixes", but even for security fixes we do try to be as reasonable as humanly possible to make them not break things."  
  `CA+55aFymwdHBs02GQkqQYwYF9Ru5dMKd4=2whLUfPwZSPU7ZGA@mail.gmail.com`, 2015-04-24, https://lore.kernel.org/all/CA%2B55aFymwdHBs02GQkqQYwYF9Ru5dMKd4%3D2whLUfPwZSPU7ZGA%40mail.gmail.com/
- "I'm definitely not reverting a patch from almost a decade ago as a regression. If it took that long to find, it can't be that critical of a regression."  
  `CAHk-=wgFuoHpMk_Z_R3qMXVDgq0N1592+bABkyGjwwSL4zBtHA@mail.gmail.com`, 2024-03-28, https://lore.kernel.org/all/CAHk-%3DwgFuoHpMk_Z_R3qMXVDgq0N1592%2BbABkyGjwwSL4zBtHA%40mail.gmail.com/
- "It's happened several times, and if it really is "it's been years", even I will go "tough luck, I guess you're stuck on your old kernel". Because we can't fix it."  
  `CA+55aFyFXxN3Qkt+=Ke5Mqctbc3+iX5_HzeH0gHFZK8tDpa=Uw@mail.gmail.com`, 2018-08-03, https://lore.kernel.org/all/CA%2B55aFyFXxN3Qkt%2B%3DKe5Mqctbc3%2BiX5_HzeH0gHFZK8tDpa%3DUw%40mail.gmail.com/
- "But even with regressions, it's also an issue of "if there's only one or two technically savvy users" and they can fix the regression outside of kernel work."  
  `CA+55aFy_so3PKnuHF6Ou5BS5KAyZs3w_zxXkZy2BwFWL5qx3_g@mail.gmail.com`, 2017-05-18, https://lore.kernel.org/all/CA%2B55aFy_so3PKnuHF6Ou5BS5KAyZs3w_zxXkZy2BwFWL5qx3_g%40mail.gmail.com/
- "And "test failure" is simply not the same thing as "user failure"."  
  `CAHk-=wgxcupvBROWUsrsyTKTWr8L93T+1xJaRvG6cOfREjpXMw@mail.gmail.com`, 2023-01-18, https://lore.kernel.org/all/CAHk-%3DwgxcupvBROWUsrsyTKTWr8L93T%2B1xJaRvG6cOfREjpXMw%40mail.gmail.com/
- "Sure, it's a "regression" in that you don't get the microcode update included, but from a user perspective things should still continue to work."  
  `CAHk-=wiV+NM+jLKbSj_Ej9RaXpu4akWV03G_wXyTSHZhArq1tg@mail.gmail.com`, 2023-11-22, https://lore.kernel.org/all/CAHk-%3DwiV%2BNM%2BjLKbSj_Ej9RaXpu4akWV03G_wXyTSHZhArq1tg%40mail.gmail.com/
- "Absolutely not. If you depend on any config file, you're broken by definition."  
  `CA+55aFxShsoiTfXUJM2463ZHPNzBsV_VcKBkM4NyGMpk6Cm=iQ@mail.gmail.com`, 2013-07-15, https://lore.kernel.org/all/CA%2B55aFxShsoiTfXUJM2463ZHPNzBsV_VcKBkM4NyGMpk6Cm%3DiQ%40mail.gmail.com/
- "It technically *is* still a regression, it's just not one we can fix."  
  `CA+55aFxZ4YESQ0vr3qO_o_H8AvQPOv500qnbBXdq+4YNsnOPgA@mail.gmail.com`, 2015-01-08, https://lore.kernel.org/all/CA%2B55aFxZ4YESQ0vr3qO_o_H8AvQPOv500qnbBXdq%2B4YNsnOPgA%40mail.gmail.com/
- "Buggy applications that do insane things still count as regressions."  
  `CA+55aFxZ4YESQ0vr3qO_o_H8AvQPOv500qnbBXdq+4YNsnOPgA@mail.gmail.com`, 2015-01-08, https://lore.kernel.org/all/CA%2B55aFxZ4YESQ0vr3qO_o_H8AvQPOv500qnbBXdq%2B4YNsnOPgA%40mail.gmail.com/
- "a regression is a bit like Schrödinger's cat - if nobody is around to notice it and it doesn't actually affect any real workload, then you can treat the regression as if it doesn't exist"  
  `CAHk-=wi7DB2SJ-wngVvsJ7Ak2cM556Q8437sOXo4EJt2BWPdEg@mail.gmail.com`, 2021-09-20, https://lore.kernel.org/all/CAHk-%3Dwi7DB2SJ-wngVvsJ7Ak2cM556Q8437sOXo4EJt2BWPdEg%40mail.gmail.com/
- "Because no, some out-of-tree garbage is not relevant, and if they don't fix it out of tree, that's *their* problem, not ours."  
  `CAHk-=wiJgRfOnt4TVFOaXfjkjTAh1AdY64zw1ohZxv7yzqzBxQ@mail.gmail.com`, 2024-04-12, https://lore.kernel.org/all/CAHk-%3DwiJgRfOnt4TVFOaXfjkjTAh1AdY64zw1ohZxv7yzqzBxQ%40mail.gmail.com/
- "we still have a very hard rule that we never break user space but then at the same time never is one of those black and white words that sometimes reality inter comes in and and bites you in the ass"  
  `https://www.youtube.com/watch?v=s4wlrxFf2lM`, 2024-10-17, https://www.youtube.com/watch?v=s4wlrxFf2lM

**How well supported.** Moderate to strong. About 12 messages from 2013 to 2024, plus a 2024 talk.

---

## P14. Internal APIs are not stable: whoever changes one fixes every caller and makes the break loud

**Principle.** The stability promise covers the user-visible ABI only. Internal kernel interfaces and data structures change all the time, and binary modules are deliberately unsupported. To keep that from turning into chaos, whoever changes an internal API converts every in-tree user in the same change. When semantics change, change the name or prototype as well, so stale callers fail to compile instead of failing quietly. Introducing a parallel API instead means maintaining both forever.

**What triggers it in a review.** A semantic change to a function that keeps its name. A "new_foo()" added next to "foo()" with no conversion of callers. Complaints from out-of-tree modules. Internal clutter kept only to avoid touching callers.

```c
-int foo_lock(struct foo *f);              /* used to sleep */
+int foo_lock_nosleep(struct foo *f);      /* new name: every caller must look */
```

**His reasoning.** Internal freedom is what allows cleanups and fixes ("with abandon, if that is what it takes"). ABI only forms where binaries can depend on something across versions, so the kernel makes sure they cannot do that for internals. Type safety and compiler errors are what keep the internal churn safe. Internals still do not change "just to be difficult".

**How serious.** High, as policy. It is the necessary counterpart of P1.

**Limits and exceptions.** uapi headers are user-visible. Even moving a header can break builds, and he reverted such a move in 2021 even though the policy is about binary interfaces.

**Outside the kernel.** In a monorepo, refactor internal APIs freely, but in one atomic change that updates every caller. Rename on semantic change. Do not keep a deprecated internal wrapper "for compat". Publish only what you intend to keep stable, and make the rest impossible to link against.

**Evidence.**
- "Rather, we deliberately don't _care_ about binary modules, exactly because we have documented several times that it IS NOT AN API."  
  `Pine.LNX.4.58.0312101535170.1273@home.osdl.org`, 2003-12-10, https://lore.kernel.org/all/Pine.LNX.4.58.0312101535170.1273%40home.osdl.org/
- "But we don't change the interfaces just to be difficult."  
  `Pine.LNX.4.58.0312101535170.1273@home.osdl.org`, 2003-12-10, https://lore.kernel.org/all/Pine.LNX.4.58.0312101535170.1273%40home.osdl.org/
- "What is not stable is the _internal_ data structures. We break external modules, and we sometimes break even in-kernel drivers etc with abandon, if that is what it takes to fix something or make it prettier."  
  `Pine.LNX.4.64.0602220848280.30245@g5.osdl.org`, 2006-02-22, https://lore.kernel.org/all/Pine.LNX.4.64.0602220848280.30245%40g5.osdl.org/
- "What makes something an ABI is that it's useful and available. The only way something isn't an ABI is by _explicitly_ making sure that it's not available even by mistake in a stable form for binary use."  
  `alpine.LFD.2.00.0812011210030.3256@nehalem.linux-foundation.org`, 2008-12-01, https://lore.kernel.org/all/alpine.LFD.2.00.0812011210030.3256%40nehalem.linux-foundation.org/
- "Example: kernel internal data structures and function calls. We make sure that you simply _cannot_ make a binary that works across kernel versions. That is the only way for an ABI to not form."  
  `alpine.LFD.2.00.0812011210030.3256@nehalem.linux-foundation.org`, 2008-12-01, https://lore.kernel.org/all/alpine.LFD.2.00.0812011210030.3256%40nehalem.linux-foundation.org/
- "Here's the only thing that works: if you change the API, you have to fix up all existing users."  
  `CAHk-=wgOXd-meRuz5Gv2oz0W0wBUOpMO5CK9eifjfdR5Xz_-Fw@mail.gmail.com`, 2025-08-26, https://lore.kernel.org/all/CAHk-%3DwgOXd-meRuz5Gv2oz0W0wBUOpMO5CK9eifjfdR5Xz_-Fw%40mail.gmail.com/
- "If you are not willing to fix up all existing users, and you introduce a parallel API, then you are the one that maintains both the old and the new API forever."  
  `CAHk-=wgOXd-meRuz5Gv2oz0W0wBUOpMO5CK9eifjfdR5Xz_-Fw@mail.gmail.com`, 2025-08-26, https://lore.kernel.org/all/CAHk-%3DwgOXd-meRuz5Gv2oz0W0wBUOpMO5CK9eifjfdR5Xz_-Fw%40mail.gmail.com/
- "So please: when you change the semantics of a function, just change the function prototype (or function name) at the same time. Especially when it comes to a driver interface, so that the drivers don't get taken by surprise."  
  `AANLkTinj2BM2eGo2yyfzs=t+nu79WLW_bGYota9sDZwH@mail.gmail.com`, 2010-11-13, https://lore.kernel.org/all/AANLkTinj2BM2eGo2yyfzs%3Dt%2Bnu79WLW_bGYota9sDZwH%40mail.gmail.com/
- "If you want to get rid of a function, just get rid of it. Convert every user to the new world order."  
  `771c035372a036f83353eef46dbb829780330234`, 2018-08-18, https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=771c035372a036f83353eef46dbb829780330234
- "Ok. I'd really rather have a cleaner internal API and break the raw driver for a while, than have a silly API just because the raw driver uses it."  
  `Pine.LNX.4.44.0210041621170.2526-100000@home.transmeta.com`, 2002-10-04, https://lore.kernel.org/all/Pine.LNX.4.44.0210041621170.2526-100000%40home.transmeta.com/

**How well supported.** Strong. About 10 messages and commits from 2002 to 2025.

---

## P15. No lock-step upgrades or two-way dependencies

**Principle.** A newer kernel must work with older user space. A newer user space may need a newer kernel for new features, but there must be no two-way dependency that forces both to be upgraded together. "Flag days aren't acceptable." Applications should copy uapi headers, not include them.

**What triggers it in a review.** A change that only works once user space (X, udev, a tool) is updated as well. A "staging" driver used as an excuse for breaking its ABI.

**His reasoning.** Lock-step upgrades stop users upgrading and stop developers bisecting. When a combination fails, it becomes much harder to tell which side is at fault.

**How serious.** High. He calls it "a real bug and a regression".

**Limits and exceptions.** One direction is allowed: new user space may require a new kernel for new features.

**Outside the kernel.** Server and client, producer and consumer, migration and application: each must be deployable independently in either order. Use expand-and-contract schema migrations. Make wire protocols tolerate older peers. Never ship a release that needs a simultaneous client release.

**Evidence.**
- "But if you have a TWO-WAY dependency, you're screwed. That means that you have to upgrade in lock-step, and that just IS NOT ACCEPTABLE."  
  `Pine.LNX.4.64.0602220848280.30245@g5.osdl.org`, 2006-02-22, https://lore.kernel.org/all/Pine.LNX.4.64.0602220848280.30245%40g5.osdl.org/
- "it's horrible for developers, because it means that you can't say "a bug happened" and do things like try to narrow it down with bisection or similar."  
  `Pine.LNX.4.64.0602220848280.30245@g5.osdl.org`, 2006-02-22, https://lore.kernel.org/all/Pine.LNX.4.64.0602220848280.30245%40g5.osdl.org/
- "The major users are USERS. Not developers. It doesn't help to "coordinate" things, when what gets screwed is the end-user who no longer can upgrade his kernel without worrying that something might break."  
  `Pine.LNX.4.64.0602220848280.30245@g5.osdl.org`, 2006-02-22, https://lore.kernel.org/all/Pine.LNX.4.64.0602220848280.30245%40g5.osdl.org/
- "If you cannot upgrade a kernel without ugrading some user package, that should be considered a real bug and a regression."  
  `Pine.LNX.4.64.0512291451440.3298@g5.osdl.org`, 2005-12-29, https://lore.kernel.org/all/Pine.LNX.4.64.0512291451440.3298%40g5.osdl.org/
- "Upgrading X and the kernel in lock-step is not a valid model"  
  `alpine.LFD.2.00.1003041015080.3588@localhost.localdomain`, 2010-03-04, https://lore.kernel.org/all/alpine.LFD.2.00.1003041015080.3588%40localhost.localdomain/
- "And if we want to encourage people to upgrade their kernel very aggressively (and we absolutely do!), then that means that we have to also make sure it doesn't require them upgrading anything else."  
  `alpine.LFD.1.10.0807311235350.3277@nehalem.linux-foundation.org`, 2008-07-31, https://lore.kernel.org/all/alpine.LFD.1.10.0807311235350.3277%40nehalem.linux-foundation.org/
- "We very much try to discourage user space applications from using the kernel header files directly - even projects like glibc etc are supposed to _copy_ them, not include the kernel headers."  
  `CAHk-=wjSadWPfzQ_hOqbjq6c_xwJs8GLHTyznhXRvDF5Yrs4FA@mail.gmail.com`, 2021-08-23, https://lore.kernel.org/all/CAHk-%3DwjSadWPfzQ_hOqbjq6c_xwJs8GLHTyznhXRvDF5Yrs4FA%40mail.gmail.com/

**How well supported.** Strong. About 6 messages from 2005 to 2021.

---

## P16. The same instinct in git: on-disk format, protocol, config and output

**Principle.** In git he applied the same rules to the object database, the wire protocol, config syntax and command output.
- Keep old and new repositories readable through format changes.
- Extend the protocol instead of forcing clients to upgrade.
- Write config in a syntax older versions can read.
- Make output that scripts parse "brittle by design", meaning fixed, with no variation.
- Prefer compatibility to a clean slate (the 2017 hash transition).

He also accepts that breaking a script is sometimes justified (32-bit GPG key ids are "really broken"). Once a release has shipped without something, "compatibility" stops being an argument for bringing it back.

**What triggers it in a review.** A format change that strands older git versions sharing a repository. A protocol change that forces client upgrades. Free-form header fields whose meaning will drift. Porcelain output changed with no thought for scripts.

**His reasoning.** Many git versions access the same repository, and servers and clients upgrade at different times. Fields whose meaning drifts produce an unresolvable compatibility mess "five years from now". Breaking existing users is "very objectionable".

**How serious.** High for the on-disk format and the protocol. Milder for porcelain output.

**Limits and exceptions.** New features may need a newer git. Deprecations that had more than a year's notice and then shipped (the `git-foo` dash commands in 2008) are final. Decorations and similar human-oriented output are not expected to be parsed.

**Outside the kernel.** This is the clearest example of the rule applied to file formats and wire protocols. Readers must tolerate formats newer than themselves where they can, and writers should produce the oldest format that expresses the data. Negotiate protocol capabilities. Separate machine (plumbing) output from human (porcelain) output, and freeze the former.

**Evidence.**
- "but on the whole, I still think that the compatibility would be worth much more than the possible technical advantages of a clean slate restart."  
  `CA+55aFwXaSAMF41Dz3u3nS+2S24umdUFv0+k+s18UyPoj+v31g@mail.gmail.com`, 2017-03-02, https://lore.kernel.org/all/CA%2B55aFwXaSAMF41Dz3u3nS%2B2S24umdUFv0%2Bk%2Bs18UyPoj%2Bv31g%40mail.gmail.com/
- "Even if you can upgrade all servers (there aren't that many of them), why force a client upgrade when the protocol is designed to be extensible?"  
  `Pine.LNX.4.64.0510200924110.3369@g5.osdl.org`, 2005-10-20, https://lore.kernel.org/all/Pine.LNX.4.64.0510200924110.3369%40g5.osdl.org/
- "the nice thing is that I tried very hard to make it so that the "git" programs will work with both a pre-conversion and a post-conversion database."  
  `Pine.LNX.4.58.0504200144260.6467@ppc970.osdl.org`, 2005-04-20, https://lore.kernel.org/all/Pine.LNX.4.58.0504200144260.6467%40ppc970.osdl.org/
- "That's just crazy, and it's how you end up with a backwards compatibility mess five years from now that is totally unresolvable, because different projects end up having different meanings or uses for the fields"  
  `Pine.LNX.4.64.0604250833540.3701@g5.osdl.org`, 2006-04-25, https://lore.kernel.org/all/Pine.LNX.4.64.0604250833540.3701%40g5.osdl.org/
- "the upside of using "branch" is exactly that you _can_ generate it with the old-style syntax that is acceptable to older git versions too."  
  `Pine.LNX.4.64.0605071740550.3718@g5.osdl.org`, 2006-05-08, https://lore.kernel.org/all/Pine.LNX.4.64.0605071740550.3718%40g5.osdl.org/
- "That would actually be a major change to data structures, and would require some serious surgery and be hard to support in a backwards-compatible way (think different git versions accessing the same repository)."  
  `CA+55aFzuQnfo1iywnp-WAajMHe2+6_HOM85aw0bS+p0xv5RyhA@mail.gmail.com`, 2011-07-14, https://lore.kernel.org/all/CA%2B55aFzuQnfo1iywnp-WAajMHe2%2B6_HOM85aw0bS%2Bp0xv5RyhA%40mail.gmail.com/
- "But breaking existing users - that I find to be very objectionable."  
  `CAHk-=wg7r=y_tYpWuRwNFP0JU5D4g=UN1puCzkvQP4bey0-Hmw@mail.gmail.com`, 2020-07-29, https://lore.kernel.org/all/CAHk-%3Dwg7r%3Dy_tYpWuRwNFP0JU5D4g%3DUN1puCzkvQP4bey0-Hmw%40mail.gmail.com/
- "If you script the --oneline format and parse the output, you won't have any decorations at all unless you are crazy"  
  `CA+55aFy-vvOBu5Y4KDeteUyK-7U7yTa1HoqHo+hME1=8bq7Xhw@mail.gmail.com`, 2017-02-13, https://lore.kernel.org/all/CA%2B55aFy-vvOBu5Y4KDeteUyK-7U7yTa1HoqHo%2BhME1%3D8bq7Xhw%40mail.gmail.com/
- "so there is certainly a chance this could break some automated scripting. But the 32-bit key ID's really are broken."  
  `b624a3e67f498cb41f704c9bd28e7d53076611c8`, 2016-08-16, https://git.kernel.org/pub/scm/git/git.git/commit/?id=b624a3e67f498cb41f704c9bd28e7d53076611c8
- "Also, like it or not, it's done. So the argument about "compatibility" is TOTAL AND UTTER BULLSHIT. There is no compatibility, because we already released a major version without them."  
  `alpine.LFD.1.10.0808260959000.3363@nehalem.linux-foundation.org`, 2008-08-26, https://lore.kernel.org/all/alpine.LFD.1.10.0808260959000.3363%40nehalem.linux-foundation.org/
- "Itw as deprecated over a _year_ ago."  
  `alpine.LFD.1.10.0808280936300.3300@nehalem.linux-foundation.org`, 2008-08-28, https://lore.kernel.org/all/alpine.LFD.1.10.0808280936300.3300%40nehalem.linux-foundation.org/
- "I agree, it's brittle by design, exactly because I think it's very important not to allow any variations."  
  `Pine.LNX.4.58.0504271352110.18901@ppc970.osdl.org`, 2005-04-27, https://lore.kernel.org/all/Pine.LNX.4.58.0504271352110.18901%40ppc970.osdl.org/

**How well supported.** Moderate. About 15 messages from 2005 to 2020, mostly 2005 to 2008. Explicit statements on plumbing-output stability are few.

---

## Changes of position over time

- **2002 (the 2.5 development series): looser.** He accepted "just upgrade to a newer quota tool". His reaction to removing /proc/ide was "good riddance", with a skeleton to be added back if needed.
- **2005 to 2007: the rule hardens.** By his own account (2015) the strict policy started with suspend/resume, and "Back in 2005 we may well not have been as strict". By 2006 (HAL) and 2007 (the revert default) it is the rule in its full form.
- **2008 to 2018: absolute and loud.** He writes "We never EVER blame the user programs" (2012) and "there are no user space bugs" (2018).
- **After 2018: the tone changes, the substance does not.** In 2026 he still writes "we don't then turn around and say ... we'll hurt you" and calls intent without checks "worth nothing at all". In 2020 and 2023 he states the test-only and Schrödinger limits more explicitly. His 2024 talk concedes that "never" meets reality (386).
- **Interface design matured.** Up to about 2015 the emphasis is on keeping behaviour. From 2019 to 2026 more of it is about designing for extension: checked flags, aligned uapi structs, no bools.
- **Process.** He deleted the feature-removal schedule in 2012. "Within a week" for reverts is written down in 2026.

Evidence for the timeline above:

- "Are there _any_ reasons to use the old stuff, if the fix is just to upgrade to a newer quota tool?"  
  `Pine.LNX.4.44.0205231002460.1006-100000@home.transmeta.com`, 2002-05-23, https://lore.kernel.org/all/Pine.LNX.4.44.0205231002460.1006-100000%40home.transmeta.com/
- "Back in 2005 we may well not have been as strict about regressions as we are now, no."  
  `CA+55aFxk8-BsiKwr_S-c+4G6wihKPQVMLE34H9wOZpeua6W9+Q@mail.gmail.com`, 2015-08-14, https://lore.kernel.org/all/CA%2B55aFxk8-BsiKwr_S-c%2B4G6wihKPQVMLE34H9wOZpeua6W9%2BQ%40mail.gmail.com/
- "So my personal reaction to removal of /proc/ide is: "good riddance, but if it turns out that we seriously need it for backwards compatibility, we can add back a skeleton without the bloat"."  
  `Pine.LNX.4.44.0205070944020.2509-100000@home.transmeta.com`, 2002-05-07, https://lore.kernel.org/all/Pine.LNX.4.44.0205070944020.2509-100000%40home.transmeta.com/

## Not in corpus

- `Documentation/process/stable-api-nonsense.rst` (Greg Kroah-Hartman's document, often attributed to Linus) appears only in rc shortlogs, not as his text. The P14 evidence uses his own messages instead.
- Talks and interviews: only the 2012 TechCrunch interview, the 2024 and 2025 YouTube talks, and a few others matched this theme. Many famous conference Q&As where he discusses the rule are not in the corpus.

## Searched for and not found

- No general statement in his words on database schemas or config-file formats outside Kconfig and git config. The transfer sections on these are inference.
- "Theory loses" or "reality wins" as a phrase: one 2009 hit that is unrelated to compat.
- "not a bug, it's a feature": the FTS query failed on quoting, and the near variants turned up nothing relevant.
- Versioned interfaces as a positive pattern: none. Every hit argues against versioning (P8). The one exception is a 2005 git thread (`Pine.LNX.4.64.0511171131260.13959@g5.osdl.org`) that proposes a version key in the repository config, with no key meaning version 1. It is a format guard for repositories, not a versioned API, and it is not quoted here.
- A formal performance-regression policy: only case-by-case statements (P7).
- sysfs "one value per file" as his own rule: not found in his words.
- ELF and a.out deprecation as compat statements: one 2019 a.out thread, which is consistent with P12 and not quoted.
