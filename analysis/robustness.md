# Robustness: error handling, failure behaviour, debugging and security

Theme miner report for the `linus-review` skill. Sources are only `corpus.db`. Every quote below passed
`scripts/verify_quotes.py` (also listed in `robustness.quotes.jsonl`). Where a statement exists as both a yarchive
copy (`news:fa.*`) and a lore message, it is counted once.

**The thread that ties the theme together.** Linus judges failure handling by one question: *after this goes
wrong, can someone still find out what happened and keep working?* That question explains his whole set of
positions. He hates BUG_ON because a dead machine reports nothing. He likes WARN_ON_ONCE because it reports once
and carries on. He dislikes asserts and "cannot happen" checks because they are either dead code or untested
crash paths. He calls hardening "debugging" because its job is to find bugs, not to kill users. He defends
printk-free understanding and root-cause fixes because patching a symptom loses the bug. Read the principles below
as aspects of that one stance.

---

## 1. Do not crash the whole system for a local problem (BUG_ON / panic)

**Principle.** Code must not take down the process, service or machine because one of its own assumptions
failed. Crash only when continuing would cause worse damage (corrupted persistent state), and even then the
decision mostly belongs to the operator, not to the code. Code that can return an error must return it.

**What triggers it in a review.**
- A new `BUG_ON()`, `panic()`, `abort()`, `assert()` on a path that could instead fail the operation.
- A driver, plugin or non-core module that kills the host on a bad state.
- "Out of resources" handled by crashing (`panic` on allocation failure, table full, counter overflow).

```c
/* rejected */                              /* wanted */
BUG_ON(!dev->ring);                         if (WARN_ON_ONCE(!dev->ring))
                                                    return -EINVAL;
```

**His reasoning.** A machine killed by BUG_ON often dies holding locks or in interrupt context, leaving no log.
So the bug report is lost, and the crash is also a denial-of-service hole. Non-core code cannot know what the
rest of the system holds, so it is never entitled to stop it. "Cannot happen" happens because code changes under
it.

**How serious.** One of his strongest, most repeated positions. He NAKs patches that add BUG_ON (2015), rewrites BUG_ON into WARN_ON in his own commits (2016
`21f54dd`), and in 2022 told maintainers WARN_ON_ONCE is the thing to aim for. A BUG_ON that only *moves* is
pulled with a grumble that people should look at the code they move (2017).

**Limits and exceptions.** BUG_ON is allowed when "continuing is deadly", for example massive corruption that
would spread to disk. panic() is acceptable during early boot, when the machine cannot come up anyway
(2022-08-29, second mail). Admins may opt into panic-on-warn (see principle 3).

**Outside the kernel.** Map BUG_ON to `panic!`, `.unwrap()`, `.expect()`, `assert!` in release paths,
`process.exit`, `os.Exit`, uncaught exceptions that kill a worker, and `abort()` in a library. A library or
request handler must return an error, not end the process. A reviewer should flag `unwrap()` on anything
fallible from outside (I/O, parse, allocation in no-std, network), and `panic!` inside library code. The 2021
Rust mail states this directly: running out of memory must give an error return, never an abort.

**Evidence.**
- `news:fa.oaq5dnv.h4i4bb@ifi.uio.no`, 2002-09-10, <https://yarchive.net/comp/linux/BUG.html#1>
  > Rule of thumb: BUG() is only good for something that never happens and that we really have no other option for (ie state is so corrupt that continuing is deadly).
- `CA+55aFymSQYnutQgv0B2yXHL00hHs-3UZZGEXVik18QUdPTgyg@mail.gmail.com`, 2012-10-12, <https://lore.kernel.org/all/CA%2B55aFymSQYnutQgv0B2yXHL00hHs-3UZZGEXVik18QUdPTgyg%40mail.gmail.com/>
  > We have way too many people who seem to think that "I don't know what I should do, so I'll just kill the machine" is a sane option. It's not.
- `21f54ddae449f4bdd9f1498124901d67202243d9`, 2016-10-04, <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=21f54ddae449f4bdd9f1498124901d67202243d9>
  > The only valid situation for BUG_ON() is when continuing is not an option, because there is massive corruption. But if you are just verifying that something is true, you warn about your broken assumptions (preferably just once), and limp on.
- `CAHk-=wit-DmhMfQErY29JSPjFgebx_Ld+pnerc4J2Ag990WwAA@mail.gmail.com`, 2022-08-29, <https://lore.kernel.org/all/CAHk-%3Dwit-DmhMfQErY29JSPjFgebx_Ld%2Bpnerc4J2Ag990WwAA%40mail.gmail.com/>
  > So WARN_ON_ONCE() is the thing to aim for. BUG_ON() is the thing for "oops, I really don't know what to do, and I physically *cannot* continue" (and that is *not* "I'm too lazy to do error handling").
- `CA+55aFzdZJw7Ot7=PYyyskNhkv=H+NPzoF6rKtb6oMyzkuQ-=Q@mail.gmail.com`, 2015-06-15, <https://lore.kernel.org/all/CA%2B55aFzdZJw7Ot7%3DPYyyskNhkv%3DH%2BNPzoF6rKtb6oMyzkuQ-%3DQ%40mail.gmail.com/>
  > If your non-critical code has s bug in it, you do WARN_ONCE() and you return. You don't kill the machine just because of some "this can't happen" situation.
- `https://yarchive.net/comp/linux/semaphores.html#9`, 2001-04-16, <https://yarchive.net/comp/linux/semaphores.html#9>
  > There is _never_ any excuse for panic'ing because of some inherent limitation of the data structures. You can return -ENOMEM, -EAGAIN or something like that, but you must _not_ allow a panic (or a roll-over, which would just result in corrupted kernel data structures).

**How well supported.** About 30 distinct messages and commits read, 1992 to 2023 (1992 inode-panic removal,
2001, 2002 thread, 2007, 2012 x3, 2013, 2015 x2, 2016 x2, 2017, 2018, 2020, 2022 x3, 2023). Very strong.

---

## 2. A dead system cannot be debugged: keep running so the failure is reported

**Principle.** Prefer "fail this operation and keep the system up" to "stop everything", because a living
system can report the bug and a dead one cannot. Even a wrong answer that is logged is better than a stop that
hides the cause.

**What triggers it in a review.**
- A failure path that stops at a point where no log line, core dump or error reply reaches anyone.
- Hardware or I/O failure turned into a crash instead of a failed request.
- Fatal handling in code that runs with locks held or in a context that cannot report.

**His reasoning.** "a working machine is about a million times easier to debug on than a dead one" (2002), and
users act on a warning they can see but not on a hang. In the kernel there are no core files or debugger in the
general case (2022), so a stop loses all evidence.

**How serious.** The reason behind principle 1; he repeats it whenever he rejects BUG_ON. He rejected the Rust
"panic on violation" model on these grounds (2021, 2022).

**Limits and exceptions.** His 2022 justification is that the kernel often has no separate environment outside it to deal with a
failure. That implies the rule is weaker for a user process supervised by something else. Continuing with the wrong answer is only for
state that will not corrupt persistent data.

**Outside the kernel.** Transfers strongly but needs care. A web service under a supervisor may crash a worker,
since the supervisor logs and restarts it, but the request must fail cleanly and the error must be logged
first. A daemon with no supervisor, firmware, an embedded loop, or a desktop app must stay up and report.
Reviewers should ask: when this fails, who learns about it, and where?

**Evidence.**
- `news:fa.mau2div.140088o@ifi.uio.no`, 2002-09-10, <https://yarchive.net/comp/linux/BUG.html#9>
  > It has nothing to do with zen mind power or printk's. It has everything to do with the fact that a working machine is about a million times easier to debug on than a dead one, _and_ is a lot more likely to get acted upon by most users.
- `CA+55aFyqAKacNmbuu1oY3P_eaMxHNBzcbQiNcDvb10f-9MK53Q@mail.gmail.com`, 2012-08-21, <https://lore.kernel.org/all/CA%2B55aFyqAKacNmbuu1oY3P_eaMxHNBzcbQiNcDvb10f-9MK53Q%40mail.gmail.com/>
  > We've literally had DoS security issues due to code having BUG_ON()'s and killing the machine, and BUG_ON() often makes things *worse* if it ends up happening in irq context or with some critical lock held, and then the machine is just dead with no logging and no messages left anywhere.
- `CAHk-=whm5Ujw-yroDPZWRsHK76XxZWF1E9806jNOicVTcQC6jw@mail.gmail.com`, 2022-09-19, <https://lore.kernel.org/all/CAHk-%3Dwhm5Ujw-yroDPZWRsHK76XxZWF1E9806jNOicVTcQC6jw%40mail.gmail.com/>
  > In the kernel, "panic and stop" is not an option (it's actively worse than even the wrong answer, since it's really not debugable), so the kernel version of "panic" is "WARN_ON_ONCE()" and continue with the wrong answer.
- `CAHk-=wh_sNLoz84AUUzuqXEsYH35u=8HV3vK-jbRbJ_B-JjGrg@mail.gmail.com`, 2021-04-14, <https://lore.kernel.org/all/CAHk-%3Dwh_sNLoz84AUUzuqXEsYH35u%3D8HV3vK-jbRbJ_B-JjGrg%40mail.gmail.com/>
  > Because kernel code is different from random user-space system tools. Running out of memory simply MUST NOT cause an abort. It needs to just result in an error return.
- `news:fa.m7vadiv.170888h@ifi.uio.no`, 2002-09-10, <https://yarchive.net/comp/linux/BUG.html#5>
  > But even broken hardware is not a reason for a BUG(). For example, if the driver notices that some part of the controller is hung hard (ie provable hardware problem), the last thing it should do is to bring the system down. It should fail the IO, and maybe turn itself off, but let the system continue otherwise.

**How well supported.** About 12 distinct messages, 2002 to 2022 (2002 x3, 2012, 2017, 2021, 2022 x3).

---

## 3. Crash policy belongs to the operator, not to the code

**Principle.** Code reports the problem; whether a warning becomes a reboot is a deployment setting. Do not
build "kill on anomaly" into the code; offer a switch (panic-on-warn, `-Werror`-like) for operators who want it.

**What triggers it in a review.**
- A new "kill the process / reboot on suspicious state" feature without being opt-in.
- Hard-coded fatal handling where a configurable severity would do.
- Security features that kill a process when a heuristic fires (see principle 12).

**His reasoning.** A fleet operator with a million machines and staff reading logs can usefully fail fast; a
laptop user loses work and the report. The code cannot know which it is running on. He proposed the
configurable-severity model himself in 2002 (DEBUG/WARN/FATAL, with warnings made fatal "a kernel version of
-Werror").

**How serious.** Firm. In 2022 he told kernel developers that the choice to panic is never theirs to make. For `pkill_on_warn` (2021) he asked for a real use case and pointed out it creates a new attack.

**Limits and exceptions.** Panic-on-warn exists and is fine as the operator's choice. Kill-on-warn is not, if
users can trigger the warning, since that hands them a way to kill other processes.

**Outside the kernel.** Map to strict modes, fail-fast flags, `RUST_BACKTRACE`/panic=abort settings, assertion
levels configured per environment. Library code logs or returns errors; the application's configuration
decides whether that ends the process.

**Evidence.**
- `CAHk-=wit-DmhMfQErY29JSPjFgebx_Ld+pnerc4J2Ag990WwAA@mail.gmail.com`, 2022-08-29, <https://lore.kernel.org/all/CAHk-%3Dwit-DmhMfQErY29JSPjFgebx_Ld%2Bpnerc4J2Ag990WwAA%40mail.gmail.com/>
  > Understand? The "should I panic and reboot" is fundamentally not about the code, and it's not a choice that the kernel code gets to make. It's purely about the choice of the person maintaining the machine.
- `CAHk-=wit-DmhMfQErY29JSPjFgebx_Ld+pnerc4J2Ag990WwAA@mail.gmail.com`, 2022-08-29, <https://lore.kernel.org/all/CAHk-%3Dwit-DmhMfQErY29JSPjFgebx_Ld%2Bpnerc4J2Ag990WwAA%40mail.gmail.com/>
  > People who want to panic on warnings can do so. WARN_ON() _becomes_ PANIC for those people. But those people are the "we have a million machines, we want to just fail things on any sign of trouble, and we have MIS people who can look at the logs".
- `news:fa.m7eqdav.17gs80n@ifi.uio.no`, 2002-09-10, <https://yarchive.net/comp/linux/BUG.html#3>
  > That would also make it easy to dynamically change the behaviour (ie some people might want to explicitly make even the "warnings" fatal - a kernel version of -Werror), and the implementation should be trivial:
- `CAHk-=whrLuVEC0x+XzYUNV2de5kM-k39GkJWwviQNuCdZ0nfKg@mail.gmail.com`, 2021-10-02, <https://lore.kernel.org/all/CAHk-%3DwhrLuVEC0x%2BXzYUNV2de5kM-k39GkJWwviQNuCdZ0nfKg%40mail.gmail.com/>
  > If you can reliably trigger the WARN_ON some way, you can probably cause more problems by fooling some other process to trigger it.

**How well supported.** About 6 distinct messages, 2002, 2021, 2022 (x2).

---

## 4. "Cannot happen" checks: either remove them or handle the case

**Principle.** A check for something that truly cannot happen is noise: delete it. If you are not sure it cannot
happen, then it can, so handle it properly (or warn once and recover). Never keep a "cannot happen" check whose
only behaviour is a crash, and never let a "cannot happen" error code spread complexity through callers.

**What triggers it in a review.**
- `BUG_ON`/`assert` on a condition the surrounding code already guarantees.
- New error returns added for impossible cases, forcing every caller to propagate them.
- "should never happen" comments followed by a crash or a silent `return`.

```c
/* "can't fail" alloc path, now every caller handles -ENOMEM it will never see */
int ret = setup_thing();      /* only fails if the caller passed NULL, which none do */
if (ret) goto unwind;
```

**His reasoning.** You cannot have it both ways: if it is impossible the code is dead, if it is possible it
deserves real handling. Spreading impossible error paths makes code illegible, and illegible code ends up as buggy code a
decade later (2020).

**How serious.** He asks for rework or removes the check himself; strong wording ("You might as well sprinkle
them randomly in every damn place", 2018).

**Limits and exceptions.** A WARN_ON_ONCE is the accepted middle ground for "I believe this cannot happen but I
want to know if it does" (2018, 2022). See principle 6.

**Outside the kernel.** Transfers directly. Flag `unreachable!()` or `assert` with nothing behind it, `catch
(Exception) {}` for "impossible" errors, `Result` types added to infallible functions, and defensive null checks
for values the type system already guarantees. Ask the author: can this happen? If yes, handle it; if no,
delete it.

**Evidence.**
- `news:fa.m6v4cqv.14069gm@ifi.uio.no`, 2002-09-10, <https://yarchive.net/comp/linux/BUG.html#4>
  > Either it really never happens. Or it _does_ happen, in which case you want sane debuggable output.
- `CAHk-=wh3_NkjfHmhTSMsHVxVji1+Fp_f_SByFRspR+KW4uqWWQ@mail.gmail.com`, 2020-11-08, <https://lore.kernel.org/all/CAHk-%3Dwh3_NkjfHmhTSMsHVxVji1%2BFp_f_SByFRspR%2BKW4uqWWQ%40mail.gmail.com/>
  > BUG_ON() is not a debug aid. If it's a "cannot happen" condition, you don't write any code for it at all. And if it's a "I'm not sure this cannot happen", you either handle it (like this patch does), or you do a "WARN_ON()" with proper cleanup.
- `CA+55aFzdZJw7Ot7=PYyyskNhkv=H+NPzoF6rKtb6oMyzkuQ-=Q@mail.gmail.com`, 2015-06-15, <https://lore.kernel.org/all/CA%2B55aFzdZJw7Ot7%3DPYyyskNhkv%3DH%2BNPzoF6rKtb6oMyzkuQ-%3DQ%40mail.gmail.com/>
  > It turns out "this can't happen" happens way too often, just because code changes, or programmers didn't think all the cases through.
- `CAHk-=wjL-4=YfvQb_pLhK5oH1QL2j-JCt-Z+S-r86-H__Vow0w@mail.gmail.com`, 2020-02-21, <https://lore.kernel.org/all/CAHk-%3DwjL-4%3DYfvQb_pLhK5oH1QL2j-JCt-Z%2BS-r86-H__Vow0w%40mail.gmail.com/>
  > But having the error condition of a "cannot happen" situation then percolate down and make other code more complex seems to be only a downside.
- `CAHk-=wjL-4=YfvQb_pLhK5oH1QL2j-JCt-Z+S-r86-H__Vow0w@mail.gmail.com`, 2020-02-21, <https://lore.kernel.org/all/CAHk-%3DwjL-4%3DYfvQb_pLhK5oH1QL2j-JCt-Z%2BS-r86-H__Vow0w%40mail.gmail.com/>
  > Maybe not immediately. But "illegible code" ends up being "buggy code" a decade later.
- `CA+55aFwJtj5ucfx3T-g9VnNgWG7EqHS9+oFMSv8oyv11Yaa2UQ@mail.gmail.com`, 2018-05-23, <https://lore.kernel.org/all/CA%2B55aFwJtj5ucfx3T-g9VnNgWG7EqHS9%2BoFMSv8oyv11Yaa2UQ%40mail.gmail.com/>
  > Why would you add a BUG_ON() for something that cannot happen? You might as well sprinkle them randomly in every damn place.

**How well supported.** About 14 distinct messages, 2002 to 2022 (2002, 2012, 2015 x2, 2018 x2, 2020 x2, 2022).

---

## 5. Asserts are temporary debugging aids, and the assert itself may be the bug

**Principle.** An assert is a development tool, not error handling. It belongs in debug or test builds and must
be removed or turned into handling once it has served. When an assert fires, first ask whether the assert is
wrong, before adding code to dodge it.

**What triggers it in a review.**
- Production code depending on assert for error handling.
- A fix that rewrites working code to "satisfy" an assert, with no argument that the asserted condition is
  actually required.
- Debug-only checks (lockdep asserts, `debug_assert!`) that nobody ever runs with the debug option on.

**His reasoning.** An assert carries an "I am sure" mindset that makes people afraid to remove it, so they add
convoluted code to avoid it, and that code is "non-obvious and broken" (2003). In the kernel, asserts mean
crashes, which principle 1 forbids.

**How serious.** Firm ("we don't use asserts in the kernel. Not acceptable", 2018). "Debugging by assert() is a
disease" (2016 commit).

**Limits and exceptions.** Debug-build asserts are fine and useful: "it's often very nice to enable asserts for
development and testing" (2024). The problem is only when they ship as fatal checks or are left untested (2023:
a lockdep assert he found had never been tested with lockdep enabled).

**Outside the kernel.** Very transferable. `debug_assert!` and test-only checks are fine. Release-build `assert`
used as validation is a finding. When a PR changes logic "because an assert fired", ask for the reason the
assertion is right.

**Evidence.**
- `https://yarchive.net/comp/linux/assert.html#1`, 2000-03-19, <https://yarchive.net/comp/linux/assert.html#1>
  > I donot like asserts. I like temporary debugging aides, and I like them just as long as they are _seen_ as temporary debugging aides.
- `21f54ddae449f4bdd9f1498124901d67202243d9`, 2016-10-04, <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=21f54ddae449f4bdd9f1498124901d67202243d9>
  > Debugging by assert() is a disease. Don't do it.
- `Pine.LNX.4.58.0312031203430.7406@home.osdl.org`, 2003-12-03, <https://lore.kernel.org/all/Pine.LNX.4.58.0312031203430.7406%40home.osdl.org/>
  > I've seen this way too often: somebody added an assert for something he thought was a bug, and then people are too damn afraid to just admit that it wasn't a bug at all, and just get rid of the f-ing assert. So instead, you add code to avoid the assert. And that code itself is non-obvious and broken.
- `alpine.LFD.1.00.0801151600140.2806@woody.linux-foundation.org`, 2008-01-16, <https://lore.kernel.org/all/alpine.LFD.1.00.0801151600140.2806%40woody.linux-foundation.org/>
  > (Pet peeve on mine: people fixing assert()'s by changing the source-code, without ever asking themselves whether maybe the assert itself was the bug).
- `CA+55aFy=T6TmG_VcLvSTb02RyKTacxVCxwUALRn8_7cdoic0pA@mail.gmail.com`, 2018-09-03, <https://lore.kernel.org/all/CA%2B55aFy%3DT6TmG_VcLvSTb02RyKTacxVCxwUALRn8_7cdoic0pA%40mail.gmail.com/>
  > First off, we don't use asserts in the kernel. Not acceptable. You handle errors, you don't crash.
- `CAHk-=wgtRUwd+9aAJ1GGq3sri+drsfArbtsrTuk9YxJU+ZGO5w@mail.gmail.com`, 2024-03-13, <https://lore.kernel.org/all/CAHk-%3DwgtRUwd%2B9aAJ1GGq3sri%2BdrsfArbtsrTuk9YxJU%2BZGO5w%40mail.gmail.com/>
  > IOW, it's often very nice to enable asserts for development and testing (but lockdep may be overkill and psosibly even entirely unacceptable if you also want to check lock contention etc).

**How well supported.** About 8 distinct messages, 2000 to 2024 (2000, 2002, 2003, 2008, 2016, 2018, 2023,
2024).

---

## 6. Warn once and recover; if input can trigger it, turn the warning into real handling

**Principle.** The right tool for "this shouldn't happen" is a one-time warning with a backtrace plus code that
leaves the system consistent. A warning must never be followed by the bad action it warned about. If the
condition turns out to be reachable from user input or odd hardware, the warning is replaced by a proper error
return.

**What triggers it in a review.**
- `WARN_ON(x)` followed by code that then corrupts state anyway.
- A warning that can fire repeatedly (spam) instead of once.
- A known, reachable condition still handled by a warning rather than an error code.

```c
/* rejected: warn, then push anyway */      /* wanted */
WARN_ON(sp >= max);                         if (WARN_ON_ONCE(sp >= max))
stack[sp++] = x;                                    return;   /* drop, don't corrupt */
```

**His reasoning.** WARN_ON_ONCE gives a backtrace showing how it happened after all without spamming logs if it turns out
to be user-triggerable (2018). Defensive layers are worth keeping: they turned an oops into a printk (2001),
and "a bug in one layer hopefully gets caught be the other layer" (2005).

**How serious.** Asks for rework; in his own commits he converts warnings to error returns (2023 hfs `cb7a95a`).

**Limits and exceptions.** A WARN_ON that fires repeatedly is a log-spam problem in its own right (principle 19).
Kill-on-warn turns a warning into an attack vector (principle 3).

**Outside the kernel.** Map to "log once with stack trace, then degrade" (a metric plus a once-per-process log,
or a rate-limited error log) and to returning `Err` once a condition is known reachable. Flag code that logs an
error and then proceeds with the invalid value.

**Evidence.**
- `Pine.LNX.4.21.0105071921110.8237-100000@penguin.transmeta.com`, 2001-05-08, <https://lore.kernel.org/all/Pine.LNX.4.21.0105071921110.8237-100000%40penguin.transmeta.com/>
  > It so happens that right now you'll only get a printk from swap_count(), because of defensive programming, but the fact remains that you _cannot_ decide on whether a page is a dead swap-cache entry until you've gotten the page lock.
- `Pine.LNX.4.58.0501261151010.2362@ppc970.osdl.org`, 2005-01-26, <https://lore.kernel.org/all/Pine.LNX.4.58.0501261151010.2362%40ppc970.osdl.org/>
  > So having good interfaces that are harder to have bugs in does _not_ mean that we still shouldn't have defensive programming practices anyway. The combination of the two means that a bug in one layer hopefully gets caught be the other layer.
- `CAHk-=wiOm8x5KnBQH+FYN76sSjCeP2_9cxgzu4WArR3jP0MD8g@mail.gmail.com`, 2018-11-01, <https://lore.kernel.org/all/CAHk-%3DwiOm8x5KnBQH%2BFYN76sSjCeP2_9cxgzu4WArR3jP0MD8g%40mail.gmail.com/>
  > If it's a "this shouldn't happen" situation, the advantage of WARN_ON_ONCE() is that it will still show the backtrace of the "how the heck did it happen after all" situation, but if it turns ouit to be user-triggerable (or simply triggerable by some odd hw situation), it won't spam your logs forever.
- `cb7a95af78d29442b8294683eca4897544b8ef46`, 2023-01-04, <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=cb7a95af78d29442b8294683eca4897544b8ef46>
  > The warning actually does warn about a bad situation, but we are much better off just handling it as the error it is. So rather than warn about us doing bad things, stop doing the bad things and return -EIO.
- `CAHk-=wjJZGA6w_DxA+k7Ejbqsq+uGK==koPai3sqdsfJqemvag@mail.gmail.com`, 2022-07-28, <https://lore.kernel.org/all/CAHk-%3DwjJZGA6w_DxA%2Bk7Ejbqsq%2BuGK%3D%3DkoPai3sqdsfJqemvag%40mail.gmail.com/>
  > (c) push_rcu() should damn well not "warn and corrupt the stack". It should warn-and-not-corrupt the stack, even if that then means that the thing isn't pushed at all.
- `news:fa.gaD/+HhjslaxEsxVKvydm+VFVAo@ifi.uio.no`, 2007-05-24, <https://yarchive.net/comp/linux/BUG.html#12>
  > It's totally idiotic to call both "BUG". One is a clear BUG, the other is a "uhhuh, something unexpected happened, but I know how to continue".

**How well supported.** About 10 distinct messages and commits, 2001 to 2023 (2001, 2005, 2007, 2017 commit,
2018, 2022 x2, 2023).

---

## 7. Error paths: goto-based unwinding in reverse order, but split functions before it gets unreadable

**Principle.** Use a single exit path with labels that undo setup in reverse order instead of deep nesting.
When a function has so many unwind steps that you can no longer see them, split it into helpers. Get the
cleanup order right and make cleanup functions accept what the setup returned.

**What triggers it in a review.**
- Deeply nested `if (ok) { if (ok2) { ... } }` instead of early exits.
- Ten or more unwind labels in one function.
- Cleanup done in the wrong order, or a partial setup that error handling cannot undo.
- `goto` used for trivial control flow rather than error exits.

```c
p = alloc_a(); if (!p) return -ENOMEM;
q = alloc_b(); if (!q) goto free_a;
if (register(q)) goto free_b;
return 0;
free_b: release_b(q);
free_a: release_a(p);
return -ENOMEM;
```

**His reasoning.** Gotos are often more readable than indentation (2003); they match the proper single-error-exit
structure. But at some point "you can't see the unwinding any more" (2010), and the answer then is
smaller functions, not more labels. Error handling in the wrong order is an easy and common mistake (2024
commit).

**How serious.** Style-level for nesting; correctness-level for wrong order or leaks. He reorganises code
himself (2023 commit `f196220`) rather than add one more `goto out`.

**Limits and exceptions.** Do not use `goto` for trivial control flow (2010). Prefer restructuring with helper
functions to growing the unwind chain.

**Outside the kernel.** In languages with RAII, `defer`, `using` or `with`, the direct goal (reverse-order,
complete cleanup) is achieved by the language; the review point becomes "is the cleanup order right and is the
function small enough to see it". In C, Go without defer, or shell scripts, the goto pattern transfers as is.

**Evidence.**
- `Pine.LNX.4.44.0301121134340.14031-100000@home.transmeta.com`, 2003-01-12, <https://lore.kernel.org/all/Pine.LNX.4.44.0301121134340.14031-100000%40home.transmeta.com/>
  > I think goto's are fine, and they are often more readable than large amounts of indentation.
- `alpine.LFD.2.00.1006012137390.8175@i5.linux-foundation.org`, 2010-06-02, <https://lore.kernel.org/all/alpine.LFD.2.00.1006012137390.8175%40i5.linux-foundation.org/>
  > (That function _really_ should be peeled like an onion, and split into many smaller functions, so that we don't have ten error cases needing unwinding. I like "goto error", but at some point you can't see the unwinding any more, and that function has passed that point a long time ago, I think)
- `alpine.LFD.2.00.1003211029480.18017@i5.linux-foundation.org`, 2010-03-21, <https://lore.kernel.org/all/alpine.LFD.2.00.1003211029480.18017%40i5.linux-foundation.org/>
  > Let's keep 'goto' for cases where we have error returns that we don't want to nest, not trivial stuff like this.
- `79a61cc3fc0466ad2b7b89618a6157785f0293b3`, 2024-09-12, <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=79a61cc3fc0466ad2b7b89618a6157785f0293b3>
  > That's all very much intentional, but it does mean that it's easy to mess up the cleanup in case of errors.
- `79a61cc3fc0466ad2b7b89618a6157785f0293b3`, 2024-09-12, <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=79a61cc3fc0466ad2b7b89618a6157785f0293b3>
  > To make this situation less error-prone, just make sure that any partial pfn mapping is torn down early, before any other error handling.
- `f1962207150c8b602e980616f04b37ea4e64bb9f`, 2023-07-04, <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=f1962207150c8b602e980616f04b37ea4e64bb9f>
  > Vegard also provided a patch for the idempotent loading issue, but I'd rather re-organize the code and make it more legible using another level of helper functions than add the usual "goto out" error handling.

**How well supported.** About 10 distinct messages and commits, 2003 to 2024 (2003, 2004, 2010 x2, 2019 commit,
2020, 2021, 2023 commit, 2024 commit).

---

## 8. Scope-based cleanup (`__cleanup`, guards) only where cleanup is unconditional; no mindless conversions

**Principle.** Automatic scope cleanup is good for the plain case: a lock or resource that is always released at
the end of scope. It is not for conditional ownership, complicated locking, or rewriting working code just to
use the new pattern.

**What triggers it in a review.**
- Guards on code where some path must return still holding the lock.
- Bulk conversion of existing error handling to `guard()`/`__free()` without a bug being fixed.
- New, cleverer guard variants (`if_not_guard`, conditional guards) invented to fit awkward code.
- Scope-based cleanup in a stable-backport fix.

**His reasoning.** Conditional cleanup is dangerous (2023). If a sane guard model does not fit some
code, "the answer is not to make an insane guard model" (2024). Mindless conversions of ugly code "actually just
got worse" (2025).

**How serious.** Asks for rework or rejects new guard variants; urges slow adoption, not a rush where everybody
converts at once (2023).

**Limits and exceptions.** He supports the facility itself and wanted it mainly to replace "goto exit" patterns
in new or clearly simpler code (2023).

**Outside the kernel.** Direct analogue: RAII guards, `defer`, `with`, `using`, `try-with-resources`. Flag
guards whose ownership is conditional or that are moved out of scope, large mechanical rewrites to a new
cleanup idiom with no bug fixed, and custom "maybe-release" guard types.

**Evidence.**
- `CAHk-=wgQ5m+SnWTYGHu0JgYXTk2dkGF+msX=ARfYoo3t1_fX9g@mail.gmail.com`, 2023-06-06, <https://lore.kernel.org/all/CAHk-%3DwgQ5m%2BSnWTYGHu0JgYXTk2dkGF%2BmsX%3DARfYoo3t1_fX9g%40mail.gmail.com/>
  > The locking cases can probably be handled with just a couple of macros (mutex, rcu, maybe spinlock?) and I would violently argue that the locking cases will have to have unconditional cleanup (ie if you *ever* have the situation where some path is supposed to be able to return with the lock held and no cleanup, then you should simply not use the "mutex_scope()" kind of helper AT ALL).
- `CAHk-=wjsb5gZTvhXofPCQthk48S9_bSGohXKU8x8XDnf7=bROw@mail.gmail.com`, 2023-07-04, <https://lore.kernel.org/all/CAHk-%3Dwjsb5gZTvhXofPCQthk48S9_bSGohXKU8x8XDnf7%3DbROw%40mail.gmail.com/>
  > Let's *not* treat this as a "W00t! Black Friday at Walmart! Everybody rush in at once!"
- `CAHk-=win7bwWhPJ=iuW4h-sDTqbX6v9_LJnMaO3KxVfPSs81bQ@mail.gmail.com`, 2024-02-27, <https://lore.kernel.org/all/CAHk-%3Dwin7bwWhPJ%3DiuW4h-sDTqbX6v9_LJnMaO3KxVfPSs81bQ%40mail.gmail.com/>
  > If a sane 'guard' model doesn't work for some code, the answer is not to make an insane guard model. The answer is to not use 'guard' in code like that.
- `CAHk-=whn07tnDosPfn+UcAtWHBcLg=KqA16SHVv0GV4t8P1fHw@mail.gmail.com`, 2024-11-20, <https://lore.kernel.org/all/CAHk-%3Dwhn07tnDosPfn%2BUcAtWHBcLg%3DKqA16SHVv0GV4t8P1fHw%40mail.gmail.com/>
  > The "if_not_guard()" model may be great for mindless conversions of existing code. But I'm not convinced it's a great interface in itself, or that "mindless conversions" of conditional locking is actually a good thing.
- `CAHk-=whef03dn8OWJ01L08hShVHCieVz7Rrzr1HJQOriVBvaDg@mail.gmail.com`, 2024-09-02, <https://lore.kernel.org/all/CAHk-%3Dwhef03dn8OWJ01L08hShVHCieVz7Rrzr1HJQOriVBvaDg%40mail.gmail.com/>
  > Honestly, I still think the guard macros are new enough that we should strive to avoid them in complicated cases like this.
- `CAHk-=wgRPDGvofj1PU=NemF6iFu308pFZ=w5P+sQyOMGd978fA@mail.gmail.com`, 2025-05-03, <https://lore.kernel.org/all/CAHk-%3DwgRPDGvofj1PU%3DNemF6iFu308pFZ%3Dw5P%2BsQyOMGd978fA%40mail.gmail.com/>
  > And the real issues have been that people who wanted this actually had truly ugly code that they wanted to mindlessly try to rewrite to use cleanup. And in the process it actually just got worse.

**How well supported.** About 8 distinct messages, 2023 to 2025 (2023 x3, 2024 x3, 2025).

---

## 9. Check the errors that matter; do not force checks that do not

**Principle.** Errors that happen in practice and need action must be checked. But not every return value needs a
check, and forcing callers to check everything (`must_check` everywhere) creates bugs. If the callee knows an
error is that serious, it should handle it itself. Some "fixes" for unchecked returns are actively wrong (retrying
`close()`).

**What triggers it in a review.**
- A fallible call whose failure matters (I/O, allocation, copy from user) left unchecked.
- `must_check`/`#[must_use]`/lint-driven checks added to functions whose errors callers cannot act on.
- Error-handling code added only to silence such an annotation.
- Retrying an operation that is not idempotent (`close` on `EINTR`).

**His reasoning.** Forced checks make callees dictate callers' behaviour and produce bogus handling: "we have
created way more bugs by having that stupid "you must check the return value even if you don't care", than by
just letting it go" (2007). Sometimes the code checks success with a stronger test than the return value (2019).

**How serious.** Rejects blanket `must_check` additions; calls tool reports about unchecked returns false
positives when the code is right (2021 Coverity).

**Limits and exceptions.** `must_check` is right "unless not checking causes a real and obvious SECURITY ISSUE"
(2007), and for functions whose errors are common and require action (2005). For user copies, you must check the
return even after `access_ok()` (2020).

**Outside the kernel.** Rust's `#[must_use]` on `Result` is roughly what he wanted for important errors; the
review question is the opposite case: wrapper errors, logging calls, `printf`-style returns that a lint forces
to be "handled" with junk. Flag `let _ =` on important results, and also flag pointless error handling for
infallible ones.

**Evidence.**
- `news:fa.g1pv3j7.nga62v@ifi.uio.no`, 2005-09-09, <https://yarchive.net/comp/linux/must_check.html#2>
  > There are functions where it is really _important_ to check the error return, because they return errors often enough - and the error case is something you have to do something about - that it's good to force people to be aware.
- `news:fa.lazKVQYX9tVjZPb69scMJ09zsrA@ifi.uio.no`, 2007-07-19, <https://yarchive.net/comp/linux/must_check.html#10>
  > I think "must_check" is an abomination. It makes the callee dictate what the caller has to do, but dammit, if the callee really "knows" its errors are that serious, it should damn well handle them itself.
- `news:fa.wNkqzlpYTsX+fMwfcq6UV/leloo@ifi.uio.no`, 2007-07-19, <https://yarchive.net/comp/linux/must_check.html#8>
  > Well, the thing is, I suspect we have created way more bugs by having that stupid "you must check the return value even if you don't care", than by just letting it go.
- `news:fa.hd418cr.i7c1o3@ifi.uio.no`, 2005-09-10, <https://yarchive.net/comp/linux/must_check.html#5>
  > Re-doing the close() is the wrong thing to do, since in a threaded environment, something else might have opened another file, gotten the same file descriptor, and you now close _another_ file.
- `news:fa.mJ8tFyAJNjnhq5E15vYZi5A61n0@ifi.uio.no`, 2007-07-19, <https://yarchive.net/comp/linux/must_check.html#7>
  > We absolutely NEVER add things like "must_check" unless not checking causes a real and obvious SECURITY ISSUE.
- `CAHk-=wgD6U97778Zz_-iMtyu47Nn3L9Mr2K5wq1afiMyE=eosg@mail.gmail.com`, 2019-09-03, <https://lore.kernel.org/all/CAHk-%3DwgD6U97778Zz_-iMtyu47Nn3L9Mr2K5wq1afiMyE%3Deosg%40mail.gmail.com/>
  > So the code *does* check for success, but it does so using a *stronger* check than the return value of probe_kernel_address().

**How well supported.** About 12 distinct messages, 2005 to 2021 (2005 x2, 2007 x4, 2019, 2020, 2021).

---

## 10. Do not change code just to silence a tool; fix the cause or fix the tool

**Principle.** A warning, sanitizer report or static-analysis hit is worth acting on only if it is interesting,
correct and valid. Otherwise the fix belongs in the tool or in what causes the warning, not in a workaround in
the code. Never "fix" a warning without understanding the code.

**What triggers it in a review.**
- Casts, dummy initialisers, `uninitialized_var()`, `READ_ONCE` sprinkled to quiet a tool.
- Commit messages like "fix warning from X" with no explanation of the actual bug.
- Rewriting a correct idiom (`a + b < a` overflow check) because a checker does not understand it.

**His reasoning.** Adding code adds bugs; sign-warning "fixes" have introduced real bugs (2007). Hiding a warning
with a dummy initialiser hid a real uninitialised variable (2012). "I don't think "change the kernel source for a
tool that isn't good enough" is the solution" (2019).

**How serious.** Rejects such patches and has threatened to stop taking a whole class of them ("If KCSAN patches
end up being "just shut up the tool", I will stop taking them", 2020).

**Limits and exceptions.** Tools that report real bugs are welcome: he calls KASAN reports easy to deal with because they
report actual bugs (2019), and praises syzbot for flushing out bugs (2021). Fixes for real issues found by tools are fine; the objection is to
fixes made only to quiet the tool.

**Outside the kernel.** Directly applicable: `// eslint-disable`, `#[allow(...)]`, `# type: ignore`,
`!` non-null assertions, `as any`, `@SuppressWarnings`, dummy default values to quiet "maybe uninitialised",
sanitizer suppressions. Ask whether the report is right; if not, fix the config or tool; if it is, fix the bug.

**Evidence.**
- `news:fa.VQX6eUxuNQf8Oq/rUVzh1vD9+90@ifi.uio.no`, 2007-07-19, <https://yarchive.net/comp/linux/must_check.html#9>
  > People shut up warnings by adding code. Adding code tends to add bugs.
- `news:fa.VQX6eUxuNQf8Oq/rUVzh1vD9+90@ifi.uio.no`, 2007-07-19, <https://yarchive.net/comp/linux/must_check.html#9>
  > Every time you see a warning, you should ask yourself: is the warning interesting, correct and valid? And if it isn't all three, then the problem is whatever *causes* the warning, not the code itself.
- `alpine.LFD.0.98.0705231850520.3890@woody.linux-foundation.org`, 2007-05-24, <https://lore.kernel.org/all/alpine.LFD.0.98.0705231850520.3890%40woody.linux-foundation.org/>
  > Please, we do NOT fix compiler warnings without understanding the code! That's a sure way to just introduce _new_ bugs, rather than fix old ones.
- `CAHk-=wgWf7Ma+iWuJTTr9HW1-yP26vEswC1Gids-A=eOP7LaOQ@mail.gmail.com`, 2019-11-11, <https://lore.kernel.org/all/CAHk-%3DwgWf7Ma%2BiWuJTTr9HW1-yP26vEswC1Gids-A%3DeOP7LaOQ%40mail.gmail.com/>
  > I don't think "change the kernel source for a tool that isn't good enough" is the solution.
- `CAHk-=wheF6DDWZa0nvopnVLbBjoL_rTmfoTmw1mJRhkR_bKH5w@mail.gmail.com`, 2020-07-03, <https://lore.kernel.org/all/CAHk-%3DwheF6DDWZa0nvopnVLbBjoL_rTmfoTmw1mJRhkR_bKH5w%40mail.gmail.com/>
  > If KCSAN patches end up being "just shut up the tool", I will stop taking them.
- `CA+55aFw+Vbj0i=1TGqCR5vQkCzWJ0QxK6CernOU6eedsudAixw@mail.gmail.com`, 2012-10-26, <https://lore.kernel.org/all/CA%2B55aFw%2BVbj0i%3D1TGqCR5vQkCzWJ0QxK6CernOU6eedsudAixw%40mail.gmail.com/>
  > Better than the crap that is uninitialized_var(), which just causes silent random behavior if it is wrong.

**How well supported.** About 14 distinct messages, 2007 to 2024 (2007 x4, 2012, 2019 x3, 2020, 2021, 2024).

---

## 11. Validate untrusted input at the boundary with real limits; trust internal callers

**Principle.** Everything that crosses a trust boundary (user space, network, files, admin-supplied data in
some cases) must be checked for sanity with practical limits, not only "doesn't overflow". Read each value once
and use the value you tested. Inside the trusted code, do not re-validate what trusted callers pass; keep track
of where data came from instead.

**What triggers it in a review.**
- A length or count from outside the trust boundary used for an allocation without a real upper bound.
- "Overflow-safe" arithmetic presented as the only limit.
- A value read twice from shared or user memory (check, then fetch again to use): TOCTOU.
- Permission checks (`access_ok`) far from the unsafe access they protect.
- Paranoid re-checking of internal arguments that hides where validation really happens.

```c
if (copy_from_user(&hdr, uptr, sizeof hdr)) return -EFAULT;
if (hdr.len > MAX_REASONABLE_LEN) return -EINVAL;   /* real limit, not just overflow */
buf = kmalloc(hdr.len, GFP_KERNEL);
/* use hdr.len from here on; never re-read uptr->len */
```

**His reasoning.** Limits must reflect "practical real issues" (2025). Random testers must still be able to find
code that takes untrusted lengths from user space, so internal warnings on absurd sizes stay (2024). Checks
should be local to the use so a reader can see the code is safe (2014). For trusted sources, "just trust it",
because defensive code there becomes random bogus code (2025).

**How serious.** Treated as an absolute requirement for user input, not just a good idea (2025). Missing checks get fixed in his own patches.

**Limits and exceptions.** Do not validate trusted internal callers just in case (2025). He rejects the claim that integer
wraparound is always wrong as a blanket rule (2024); wrap-around is often intentional.

**Outside the kernel.** Classic API validation: reject at the handler, with schema limits on size, count and
depth, not just type checks. Parse once into a validated type and pass that type inward (no re-reading the raw
request). Flag both missing validation at the edge and layers of repeated validation deep inside.

**Evidence.**
- `CAHk-=whLixL8-iYt1qH0-YvEnVsYtryZaN5Da0qoBBhKsBnumw@mail.gmail.com`, 2025-04-09, <https://lore.kernel.org/all/CAHk-%3DwhLixL8-iYt1qH0-YvEnVsYtryZaN5Da0qoBBhKsBnumw%40mail.gmail.com/>
  > User space input absolutely has to be validated for sanity.
- `CAHk-=whLixL8-iYt1qH0-YvEnVsYtryZaN5Da0qoBBhKsBnumw@mail.gmail.com`, 2025-04-09, <https://lore.kernel.org/all/CAHk-%3DwhLixL8-iYt1qH0-YvEnVsYtryZaN5Da0qoBBhKsBnumw%40mail.gmail.com/>
  > Because no, "doesn't overflow" isn't even remotely a valid limit. A real limit on memory allocations - and most other things, for that matter - needs to be about practical real issues, not about something like "this doesn't overflow".
- `CAHk-=wi8Zer6tnqO-bz+WxFpMv9sPc-LxGRm_3poOtZegjhfrg@mail.gmail.com`, 2024-01-03, <https://lore.kernel.org/all/CAHk-%3Dwi8Zer6tnqO-bz%2BWxFpMv9sPc-LxGRm_3poOtZegjhfrg%40mail.gmail.com/>
  > Exactly *because* we want all those crazy random tester robots to actually find cases where people just randomly take untrusted lengths from user space.
- `CAHk-=wh8=QAC0jjcjDRnmsmd2xDf97j8h25=aSFGeh9x+1X8UA@mail.gmail.com`, 2025-04-02, <https://lore.kernel.org/all/CAHk-%3Dwh8%3DQAC0jjcjDRnmsmd2xDf97j8h25%3DaSFGeh9x%2B1X8UA%40mail.gmail.com/>
  > If the address came from something you consider trustworthy, then just trust it. If some admin person gave you garbage, it's better to just get a random oops than to have random bogus code.
- `CA+55aFxK0wj2LLp0WmhRsBZch8XfoYbzmbEeJaMpt=SDh5GBvw@mail.gmail.com`, 2014-11-18, <https://lore.kernel.org/all/CA%2B55aFxK0wj2LLp0WmhRsBZch8XfoYbzmbEeJaMpt%3DSDh5GBvw%40mail.gmail.com/>
  > (b) when that performance issue is clear and unmistakable, you should generally have the "access_ok()" check *locally* to the use of unsafe ops, so that you can *locally* see that it's safe.
- `CA+55aFyLTc72-xTkjugVSMb3EQq=+__UcFe28agu086xf9d6ZA@mail.gmail.com`, 2015-03-26, <https://lore.kernel.org/all/CA%2B55aFyLTc72-xTkjugVSMb3EQq%3D%2B__UcFe28agu086xf9d6ZA%40mail.gmail.com/>
  > Why is that important? It's important because we have to absolutely guartantee that the value we *test* is the same value we use later.

**How well supported.** About 16 distinct messages, 1999 to 2026 (1999, 2010, 2012, 2014, 2015, 2018, 2020 x2,
2023, 2024 x2, 2025 x3, 2026).

---

## 12. Security bugs are just bugs; hardening starts by warning, not killing

**Principle.** Treat a security bug like any other bug: find the root cause and fix it. Hardening exists to catch
bugs, so a new hardening rule should first warn and collect reports, and only after a long time of warnings
become enforcing. Never break working users in the name of a new rule.

**What triggers it in a review.**
- A new security check that kills a process or panics on first violation.
- Hardening enabled as enforcing by default with no warning period.
- A security fix that only blocks the symptom and does not fix the bug that let the bad access happen.
- Security bugs handled through a special, separate process that bypasses normal review.

**His reasoning.** "the bad access was just a symptom, and it needs to be reported, and debugged, and fixed"
(2017). A new rule will hit legitimate cases nobody knew about; warning finds them; killing breaks users. All the
boring normal bugs matter more than security ones because there are more of them (2008).

**How serious.** One of his most heated positions (2017 hardening rant). He refuses enforcing-by-default hardening
that breaks users.

**Limits and exceptions.** Acute security holes get fixed even if that breaks ABI (2016); hardening that is
only hardening must not break applications. Defence in depth is good (2005). After warnings have run for a long
time, drastic measures are allowed (2017).

**Outside the kernel.** Map to WAF rules, CSP, rate limits, new auth checks, sandboxing: deploy in
report-only / log mode first, measure false positives, then enforce. Flag "block and 500" security features
rolled out without monitoring, and security patches that only filter one exploit string.

**Evidence.**
- `CA+55aFykjza0H5ytZH_aJKYs9tC84OLyVT30--cvo0mpAzpWaA@mail.gmail.com`, 2017-11-17, <https://lore.kernel.org/all/CA%2B55aFykjza0H5ytZH_aJKYs9tC84OLyVT30--cvo0mpAzpWaA%40mail.gmail.com/>
  > The important part about "just bugs" is that you need to understand that the patches you then introduce for things like hardening are primarly for DEBUGGING.
- `CA+55aFykjza0H5ytZH_aJKYs9tC84OLyVT30--cvo0mpAzpWaA@mail.gmail.com`, 2017-11-17, <https://lore.kernel.org/all/CA%2B55aFykjza0H5ytZH_aJKYs9tC84OLyVT30--cvo0mpAzpWaA%40mail.gmail.com/>
  > So the hardening efforts should instead _start_ from the standpoint of "let's warn about what looks dangerous, and maybe in a _year_ when we've warned for a long time, and we are confident that we've actually caught all the normal cases, _then_ we can start taking more drastic measures".
- `CA+55aFyybavkF8ccQKJsoVAF+MG=J5=e9PxXKU=J_hqCQRZnug@mail.gmail.com`, 2017-11-29, <https://lore.kernel.org/all/CA%2B55aFyybavkF8ccQKJsoVAF%2BMG%3DJ5%3De9PxXKU%3DJ_hqCQRZnug%40mail.gmail.com/>
  > We don't kill processes or forbid them from doing things that might be bad. We start by warning about them, to see what "might be bad" cases are actually normal, and not actually bad at all.
- `CA+55aFyBOWcz5jhni5PKEmwWMEiu8xm0-smorPA_wEJYNhbLaw@mail.gmail.com`, 2017-11-21, <https://lore.kernel.org/all/CA%2B55aFyBOWcz5jhni5PKEmwWMEiu8xm0-smorPA_wEJYNhbLaw%40mail.gmail.com/>
  > But from a developer standpoint, things _really_ are not done. Not even close. From a developer standpoint, the bad access was just a symptom, and it needs to be reported, and debugged, and fixed, so that the bug actually gets corrected.
- `news:fa.FocnvcnLqG7kPaYdjYdPJfSdhjc@ifi.uio.no`, 2008-07-15, <https://yarchive.net/comp/linux/security_bugs.html#1>
  > So I personally consider security bugs to be just "normal bugs". I don't cover them up, but I also don't have any reason what-so-ever to think it's a good idea to track them and announce them as something special.
- `CAHk-=wi6z5BGUUT2p+=qrJg+obom8VnCo3MqB=7xp3Gw+UMMkg@mail.gmail.com`, 2026-05-06, <https://lore.kernel.org/all/CAHk-%3Dwi6z5BGUUT2p%2B%3DqrJg%2Bobom8VnCo3MqB%3D7xp3Gw%2BUMMkg%40mail.gmail.com/>
  > Bugs are bugs. And not having them in public only makes them harder to deal with.

**How well supported.** About 14 distinct messages, 2005 to 2026 (2005, 2008 x3, 2016, 2017 x4, 2021, 2026 x2).

---

## 13. Real security is a balance; reject security theatre

**Principle.** Security is one engineering goal among several. Judge a measure by the real attack it stops versus
what it costs in usability, debuggability and performance. Measures that only look secure, opt-in rituals, or
hardening that makes the system unusable are theatre.

**What triggers it in a review.**
- Measures with no stated threat model ("this looks safer").
- Clearing memory, hiding info or adding checks that do not stop any real attack.
- Hiding diagnostic information (kernel pointers, `dmesg`) in ways that mainly hurt bug reports.
- A hardening change that leaves machines unbootable or unusable.

**His reasoning.** A security person who ignores other aspects "is actually HURTING security by insisting on
things that may not be practical" (2005). Protections should target large generic classes of bugs (2017),
not one-off detail. Pointer hiding and restricted logs often only break debugging (2017).

**How serious.** Rejects or reverts; strong wording ("security theater", 2008, 2017).

**Limits and exceptions.** He supports generic mitigations against large classes of bugs (2017) and individual
small measures as "one small tool in your toolchest" (2009), as long as they are not treated as fundamental.

**Outside the kernel.** Flag password-complexity-style rules with no threat model, redaction that blinds on-call,
"security" flags nobody enables, and checks that break users without stopping an attack. Ask for the attack it
prevents and the cost it carries.

**Evidence.**
- `news:fa.gstdv66.aikr1i@ifi.uio.no`, 2005-01-27, <https://yarchive.net/comp/linux/security.html#1>
  > Real engineering is about doing a good job balancing different issues.
- `news:fa.gut9v6e.8igr1q@ifi.uio.no`, 2005-01-27, <https://yarchive.net/comp/linux/security.html#2>
  > Thus a security person who doesn't take other aspects into account is actually HURTING security by insisting on things that may not be practical for a general vendor.
- `CA+55aFxZo5kZEiZFYj5mns3Tsgb0JLC_rae2ThObeM5xrC8Mug@mail.gmail.com`, 2017-10-13, <https://lore.kernel.org/all/CA%2B55aFxZo5kZEiZFYj5mns3Tsgb0JLC_rae2ThObeM5xrC8Mug%40mail.gmail.com/>
  > It's security theater. Particularly with the opt-in, it was never anything more.
- `CA+55aFymLSQyWECCBWLGtChXcJwtWNxOqdJQRbOwGyYzjY=MSg@mail.gmail.com`, 2011-08-08, <https://lore.kernel.org/all/CA%2B55aFymLSQyWECCBWLGtChXcJwtWNxOqdJQRbOwGyYzjY%3DMSg%40mail.gmail.com/>
  > but it's a prime example of code that "looks" secure, but has absolutely zero actual real security.
- `news:fa.I/LkbOXNEIoxWt7MMrcJKSx3nKo@ifi.uio.no`, 2009-06-03, <https://yarchive.net/comp/linux/address_zero.html#3>
  > Disallowing NULL pointer mmap's is one small tool in your toolchest, and not at all all-consumingly important or fundamental. It's just one more detail.
- `CAHk-=whEd020BYzGTzYrENjD9Z5_82xx6h8HsQvH5xDSnv0=Hw@mail.gmail.com`, 2026-02-21, <https://lore.kernel.org/all/CAHk-%3DwhEd020BYzGTzYrENjD9Z5_82xx6h8HsQvH5xDSnv0%3DHw%40mail.gmail.com/>
  > It's "hardening" only in the strict sense that a completely non-bootable machine sure as hell is secure.

**How well supported.** About 12 distinct messages, 2005 to 2026 (2005 x2, 2008, 2009 x2, 2011, 2017 x4, 2026).

---

## 14. Disclosure: timely open fixes, short embargoes, no exploit recipes

**Principle.** Fix security bugs in the open and quickly. Publish the patch and its explanation; do not publish
exploit details. Embargoes are acceptable only when short (days, not weeks) and free of politics, because hidden
fixes miss review and testing.

**What triggers it in a review / process.**
- A fix held back for weeks or months for coordination.
- A security patch pushed without passing normal review and CI because it was secret.
- Commit messages written as exploit recipes, or, the opposite, fixes hidden behind vague text that also hides
  the bug from reviewers.

**His reasoning.** Embargoed fixes miss bugs because nobody can review them (2005), and they skip test
automation (2018, 2022). To him, disclosing is the fixing of the bug (2008). He will not make bugs trivially
exploitable, so no "here's how to exploit it" logs (2008).

**How serious.** Policy-level; he refused to join long-embargo lists (2005) and keeps a "timely open fixes" model
(2018). In 2026 he argued AI-found bugs should go to public lists.

**Limits and exceptions.** Short self-imposed embargoes are fine. Hardware bugs (Spectre, Meltdown) ran under
long embargoes he disliked but worked with.

**Outside the kernel.** Mostly a process point: for a project's security policy, prefer short embargoes and
normal CI for security fixes; commit messages explain the bug, not the exploit. Lower weight for code review.

**Evidence.**
- `CA+55aFzGgtnkKpJEDCvzDmEn7JE6DnOKuHwtkTkeN3AeHjt6dw@mail.gmail.com`, 2018-03-07, <https://lore.kernel.org/all/CA%2B55aFzGgtnkKpJEDCvzDmEn7JE6DnOKuHwtkTkeN3AeHjt6dw%40mail.gmail.com/>
  > We disclose the *patches*, and the explanation of the patch, but not necessarily anything else (ie no exploit code or even any exploit discussion).
- `CA+55aFzGgtnkKpJEDCvzDmEn7JE6DnOKuHwtkTkeN3AeHjt6dw@mail.gmail.com`, 2018-03-07, <https://lore.kernel.org/all/CA%2B55aFzGgtnkKpJEDCvzDmEn7JE6DnOKuHwtkTkeN3AeHjt6dw%40mail.gmail.com/>
  > It's more like just "timely open fixes".
- `news:fa.gtdhue7.b2or9t@ifi.uio.no`, 2005-01-12, <https://yarchive.net/comp/linux/security_lists.html#4>
  > But in the absense of politics, I'd _happily_ have a self-imposed embargo that is limited to some reasonable timeframe (and "reasonable" is definitely counted in days, not weeks. And absolutely _not_ in months, like apparently sometimes happens on vendor-sec).
- `news:fa.gutttu1.8i4qpn@ifi.uio.no`, 2005-01-12, <https://yarchive.net/comp/linux/security_lists.html#5>
  > One of the problems with the embargo thing has been exactly the fact that people couldn't even find bugs (or just uglinesses) in the fixes, because they were kept under wraps until the "proper date".
- `news:fa.rdcOoBM7quHjitCB7xgr8LCp5vw@ifi.uio.no`, 2008-07-15, <https://yarchive.net/comp/linux/security_bugs.html#4>
  > But that also doesn't mean that I see any reason to make it obvious what to do to trigger them, and cause problems at universities and such. So I don't do "here's how to exploit it" commit logs, for example.
- `CAHk-=wiHa0vsZseZES=1T0rJ4Z_bC5cwHMUJfqFL9hVpvB283g@mail.gmail.com`, 2022-03-13, <https://lore.kernel.org/all/CAHk-%3DwiHa0vsZseZES%3D1T0rJ4Z_bC5cwHMUJfqFL9hVpvB283g%40mail.gmail.com/>
  > And while the patches were mostly fine, we had the usual "because it was hidden, all our normal testing automation didn't see it either".

**How well supported.** About 12 distinct messages, 2005 to 2026 (2005 x3, 2008 x4, 2018 x2, 2022, 2026).

---

## 15. Mitigations must earn their cost; ask for numbers

**Principle.** A mitigation that costs performance on every call needs evidence that it addresses a real, present
attack. Ask for measurements. Prefer structural fixes (remove the vulnerable indirection) to expensive blanket
measures, and do not accept costs "on theory".

**What triggers it in a review.**
- A mitigation added to a hot path with no benchmark.
- Mitigations enabled by default for theoretical attacks.
- Vendor-driven mitigations whose design suggests the vendor does not expect them to be enabled.

**His reasoning.** "we're not taking another 30% performance hit on kernel entry on theory" (2018), because
performance matters to real users. Often the real fix is structural, such as inlining away the indirect call (2018).

**How serious.** Rejects or asks for rework and numbers; harsh about vendor (Intel IBRS) designs.

**Limits and exceptions.** Mitigations for real, demonstrated attacks were merged under pressure in 2018. Later
(2023) he supported per-mitigation config options, so the user chooses.

**Outside the kernel.** Map to expensive security middleware, constant-time everything, per-request crypto,
blanket input sanitisation in hot paths: ask for the threat and for a benchmark, and prefer designs that remove
the attack surface.

**Evidence.**
- `alpine.LFD.2.21.999.1804231415001.18164@i7.lan`, 2018-04-23, <https://lore.kernel.org/all/alpine.LFD.2.21.999.1804231415001.18164%40i7.lan/>
  > Because we're not taking another 30% performance hit on kernel entry on theory. You may not care, and there are a lot of crazy security people who may not care, but real people do. Performance matters.
- `CA+55aFwOkH8RH12Dzs=hT3e7eS3Ckz9Ed6x_-9a0zs1cw9zbKA@mail.gmail.com`, 2018-01-21, <https://lore.kernel.org/all/CA%2B55aFwOkH8RH12Dzs%3DhT3e7eS3Ckz9Ed6x_-9a0zs1cw9zbKA%40mail.gmail.com/>
  > The whole IBRS_ALL feature to me very clearly says "Intel is not serious about this, we'll have a ugly hack that will be so expensive that we don't want to enable it by default, because that would look bad in benchmarks".
- `CA+55aFzNQ8CZ8iNcPXrCfyk=1edMiRGDA0fY0rd87BsFKBxgAw@mail.gmail.com`, 2018-01-12, <https://lore.kernel.org/all/CA%2B55aFzNQ8CZ8iNcPXrCfyk%3D1edMiRGDA0fY0rd87BsFKBxgAw%40mail.gmail.com/>
  > Do you have any performance numbers and perhaps example code generation? Is this noticeable? Are there any microbenchmarks showing the difference between lfence use and the masking model?
- `CA+55aFwg88mxuOiJSh+xLnAfqEwAC-ReB9rdNx+r8fy=FTSHJw@mail.gmail.com`, 2018-02-02, <https://lore.kernel.org/all/CA%2B55aFwg88mxuOiJSh%2BxLnAfqEwAC-ReB9rdNx%2Br8fy%3DFTSHJw%40mail.gmail.com/>
  > Honestly, if this is so performance-critical, the *real* fix is to actually just mark all those "slot_handle_*()" functions as "always_inline".

**How well supported.** About 8 distinct messages, 2013 to 2023 (2013 x2, 2018 x5, 2023). Concentrated in 2018.

---

## 16. Fix the root cause, do not paper over symptoms (but a pragmatic stopgap can be the right fix)

**Principle.** A fix must explain and remove the cause. Workarounds that hide a symptom (delays, retries,
suppressing a detector, special cases) are not accepted when nobody has tried to find the real problem. A
stopgap is fine when it is labelled as one and the real fix is not practical.

**What triggers it in a review.**
- A sleep, delay, retry or timeout added "because it fixes the issue" with no explanation.
- Silencing a watchdog or detector instead of fixing what it detected.
- A commit message that cannot say why the change works.

**His reasoning.** Papering over "makes people less likely to bother with the real issue" (2008). Detectors exist
to find such places, so silencing them "end up killing the whole idea" (2003).

**How serious.** NAKs the patch when nobody is willing to try alternatives (2017).

**Limits and exceptions.** The perfect is the enemy of the good: sometimes there is no proper solution and the
"paper over" is the best one there is (2007). Band-aids are acceptable for theoretical
worst-case behaviour (2017). Temporary "two aspirins" fixes are fine if they are seen as such (2003).

**Outside the kernel.** Flag `sleep` in tests, retry loops around flaky calls, catch-and-ignore around
intermittent errors, and disabled health checks. Ask: what is the root cause, and has anyone looked? Accept a
labelled stopgap with a tracking issue when the real fix is impractical.

**Evidence.**
- `CA+55aFyHVV=eTtAocUrNLymQOCj55qkF58+N+Tjr2YS9TrqFow@mail.gmail.com`, 2017-08-15, <https://lore.kernel.org/all/CA%2B55aFyHVV%3DeTtAocUrNLymQOCj55qkF58%2BN%2BTjr2YS9TrqFow%40mail.gmail.com/>
  > We don't "fix" things by papering over some symptom. We try to fix the _actual_ underlying problem.
- `CA+55aFyHVV=eTtAocUrNLymQOCj55qkF58+N+Tjr2YS9TrqFow@mail.gmail.com`, 2017-08-15, <https://lore.kernel.org/all/CA%2B55aFyHVV%3DeTtAocUrNLymQOCj55qkF58%2BN%2BTjr2YS9TrqFow%40mail.gmail.com/>
  > Because a band-aid is ok for "some theoretical worst-case behavior". But a band-aid is *not* ok for "we can't even be bothered to try to figure out the right thing, so we're just adding this hack and leaving it".
- `alpine.LFD.1.10.0807301310130.3334@nehalem.linux-foundation.org`, 2008-07-30, <https://lore.kernel.org/all/alpine.LFD.1.10.0807301310130.3334%40nehalem.linux-foundation.org/>
  > And by papering it over, it then just makes people less likely to bother with the real issue.
- `CAHk-=wi53cJEKim7UvUXtdhQG1BR7oU5TABPXaOq5SmBKLSKYg@mail.gmail.com`, 2024-03-04, <https://lore.kernel.org/all/CAHk-%3Dwi53cJEKim7UvUXtdhQG1BR7oU5TABPXaOq5SmBKLSKYg%40mail.gmail.com/>
  > Hiding a problem isn't fixing it.
- `Pine.LNX.4.44.0308051402300.2835-100000@home.osdl.org`, 2003-08-05, <https://lore.kernel.org/all/Pine.LNX.4.44.0308051402300.2835-100000%40home.osdl.org/>
  > So this is a case of trying to paper over the symptoms. Which is perfectly ok in the sense that "we don't have the resources to fix it right now, so let's just give it two aspirins and ask it to call in the morning". That's fine. But since the whole _point_ of watchdogging is to find places like this, when you paper over _these_ symptoms, you end up killing the whole idea.
- `Pine.LNX.4.64.0701112044070.3594@woody.osdl.org`, 2007-01-12, <https://lore.kernel.org/all/Pine.LNX.4.64.0701112044070.3594%40woody.osdl.org/>
  > Very basic issue: the perfect is the enemy of the good. Claiming that there is a "proper solution" is usually a total red herring. Quite often there isn't, and the "paper over" is actually not papering over, it's quite possibly the best solution there is.

**How well supported.** About 12 distinct messages and commits, 2003 to 2024 (2003, 2007, 2008 x2 incl. blog,
2010 commit, 2017, 2024 x2).

---

## 17. Hardware and firmware are buggy: work around them, and trust what you can probe

**Principle.** Bugs in hardware and firmware cannot be fixed, so a driver must work around them; a driver that
does not is buggy. Do not trust firmware tables when the hardware can be probed directly. Prefer to recover from
the actual error instead of tables of exceptions.

**What triggers it in a review.**
- "That's a firmware bug, not ours" as a reason not to handle it.
- New dependence on firmware or vendor-provided data where probing is possible.
- Per-model quirk tables that need a newer release for each new device.
- Workarounds that penalise every user instead of recovering from the actual error.

**His reasoning.** Firmware "is always buggy, and we can't fix the bugs in it" (2004). Knowing the hardware better
than the BIOS is a stable strategy, matching Windows or trusting ACPI is not (2010). Quirk tables require a kernel
newer than the hardware (2004).

**How serious.** Strong; he refuses arguments that the kernel should not work around BIOS bugs.

**Limits and exceptions.** Quirks are acceptable for things that seldom change, or where there is good vendor
support (2004). Workarounds should be narrow and recover from the error rather than hide it (2007).

**Outside the kernel.** Transfers to any third-party dependency: browsers, external APIs, SDKs, OS quirks.
Users experience your product, so working around a known-bad dependency is your job. Prefer feature detection to
user-agent or version tables; prefer handling the error the dependency actually returns.

**Evidence.**
- `Pine.LNX.4.64.0703070746150.5963@woody.linux-foundation.org`, 2007-03-07, <https://lore.kernel.org/all/Pine.LNX.4.64.0703070746150.5963%40woody.linux-foundation.org/>
  > BIOS bugs are not bugs we can fix, they are things we have to work around. They are like hardware bugs in a network chip: a "driver" that doesn't work around a BIOS bug is simply a *buggy* driver, exactly the same way a network driver has to work around errata in the hardware.
- `Pine.LNX.4.58.0411221116480.20993@ppc970.osdl.org`, 2004-11-22, <https://lore.kernel.org/all/Pine.LNX.4.58.0411221116480.20993%40ppc970.osdl.org/>
  > To me, firmware is not something cool to be used. It's a necessary evil, and it should be avoided and mistrusted as far as humanly possible, because it is always buggy, and we can't fix the bugs in it.
- `AANLkTi=U+CTn=RDvYG0w6JK0Owv_TEc9YNtAtm9DeLKi@mail.gmail.com`, 2010-12-15, <https://lore.kernel.org/all/AANLkTi%3DU%2BCTn%3DRDvYG0w6JK0Owv_TEc9YNtAtm9DeLKi%40mail.gmail.com/>
  > The whole "ok, we know the hardware better than the BIOS does" is a _stable_ strategy. In contrast, the things you propose are NOT stable strategies, they all depend on basically "we match windows exactly and/or trust ACPI". Both of which are *known* to be failing models.
- `Pine.LNX.4.58.0411071434240.24286@ppc970.osdl.org`, 2004-11-07, <https://lore.kernel.org/all/Pine.LNX.4.58.0411071434240.24286%40ppc970.osdl.org/>
  > It fundamentally takes the approach of "you have to have a kernel that is two years newer than the hardware you have", which is an approach that I just find incredibly broken.
- `alpine.LFD.0.999.0708201853020.30176@woody.linux-foundation.org`, 2007-08-21, <https://lore.kernel.org/all/alpine.LFD.0.999.0708201853020.30176%40woody.linux-foundation.org/>
  > Would it not be a lot more natural to handle the *result* of the problem (ie the MMF errors by broken EHCI controllers?) rather than add totally insane workarounds for this case to try to hide them in the first place?

**How well supported.** About 10 distinct messages, 2002 to 2012 (2002, 2004 x2, 2007 x2, 2008, 2010, 2012).

---

## 18. Understand the code before changing it; debug by reasoning, not by random changes

**Principle.** Fix bugs by understanding the code. Random changes that "work on my machine", copied code whose
purpose you do not know, and debugger-driven symptom fixes are not acceptable. Debugging aids should not make the
code worse for everyone.

**What triggers it in a review.**
- A fix whose commit message cannot explain why it works.
- Code copied from elsewhere with unexplained steps.
- Debugging infrastructure (verbose printing, hooks) added permanently to production paths.

**His reasoning.** Debuggers "tend to cause the _symptoms_ to be fixed rather than the actual underlying bugs"
(2000). Random changes that work on one machine are not fixes (2023). Fixes need "actual reasons" (2017).

**How serious.** Rejects patches; strong wording, especially to repeat offenders.

**Limits and exceptions.** His view of tools softened: printk was the standard debugging trick in 1992; kgdb was
merged in 2008 on the condition that it stay minimal. gdb as a disassembler is fine. In 2026 he still calls
printk debugging "a failure mode", but his point there is not to make everyone's kernel worse for it.

**Outside the kernel.** Transfers fully: a PR must explain the mechanism of the bug and why the change fixes it.
Flag "added retry, seems to fix it", Stack Overflow paste with unexplained flags, and permanent debug logging
left in hot paths. Debuggers themselves are fine in application code; the rule is about understanding.

**Evidence.**
- `https://yarchive.net/comp/linux/debuggers.html#1`, 2000-09-06, <https://yarchive.net/comp/linux/debuggers.html#1>
  > I don't think kernel development should be "easy". I do not condone single-stepping through code to find the bug. I do not think that extra visibility into the system is necessarily a good thing.
- `https://yarchive.net/comp/linux/assert.html#1`, 2000-03-19, <https://yarchive.net/comp/linux/assert.html#1>
  > my strongly held personal belief is that debuggers tend to cause the _symptoms_ to be fixed rather than the actual underlying bugs that you fix when you think about the problem on a source level
- `CAHk-=wjNQaT+uYYE2G_YuRyHTdZZNYwCKU0fb5H7fS1Z1G5uZw@mail.gmail.com`, 2026-06-21, <https://lore.kernel.org/all/CAHk-%3DwjNQaT%2BuYYE2G_YuRyHTdZZNYwCKU0fb5H7fS1Z1G5uZw%40mail.gmail.com/>
  > But I personally think that debugging should be done by looking at and understanding the code. To me, "debugging using printk's" - fancy printk's or not - is a failure mode, and soemthing you should be quietly ashamed of, instead of using it as some kind of argument for making everybody elses kernel worse.
- `CAHk-=wiKooX5vOu6TgGPEwdX--k0DyE4ntJDU4QzbVFMWGVXFw@mail.gmail.com`, 2023-12-14, <https://lore.kernel.org/all/CAHk-%3DwiKooX5vOu6TgGPEwdX--k0DyE4ntJDU4QzbVFMWGVXFw%40mail.gmail.com/>
  > Stop making random changes that just happen to work on the one machine you tested it on.
- `CA+55aFw9S7f6eawrH6B5M-sTca9TT2sjzBU14xijBCeSpmCkHA@mail.gmail.com`, 2017-09-13, <https://lore.kernel.org/all/CA%2B55aFw9S7f6eawrH6B5M-sTca9TT2sjzBU14xijBCeSpmCkHA%40mail.gmail.com/>
  > Honestly, what we need here is less "let's do random changes", and more "have actual reasons for those changes".
- `oldlinux:mail-archive/linux-activists/Volume1/Linux-V1.tar.z#25`, 1992-02-14, <https://github.com/oldlinux-web/oldlinux-files/blob/master/mail-archive/linux-activists/Volume1/Linux-V1.tar.z>
  > Printk's in the kernel is the standard "debugging" trick. If somebody comes up with something better, feel free to post: I'm not too happy about it either, but it's simple.

**How well supported.** About 12 distinct messages, 1992 to 2026 (1992, 2000 x3, 2008, 2017 x2, 2023, 2024,
2026).

---

## 19. Log messages must be actionable information, not noise

**Principle.** Print only messages that help someone run or debug the system. Informational chatter, repeated
messages and scary messages for expected situations hide the real problems. A message that can repeat needs a
sensible rate limit, often far stricter than default.

**What triggers it in a review.**
- New info-level messages on normal paths (probe success, hotplug chatter).
- Errors logged at high severity for expected conditions.
- Messages that can be triggered in a loop, including by users.
- Hex dumps and "data" without interpretation.

**His reasoning.** Informational messages "aren't informational, they're just annoying, and they hide the _real_
stuff" (2001). Data is only useful as information (2016). Excess warnings might hide any real cases (2023 commit).

**How serious.** He treats new log spam as a regression and lowers or removes messages himself (2011, 2023
commits).

**Limits and exceptions.** Messages useful for debugging are wanted. Rate limiting is not a fix for floods: "if
you can flood things without the rate limiting, you can still flood things with the rate limiting" (2023).

**Outside the kernel.** Flag INFO logs per request, ERROR for expected 404s or validation failures, logging of
whole payloads, and any log that a client can trigger in a loop. Ask: what action would someone take on seeing this?

**Evidence.**
- `Pine.LNX.4.33.0106280956030.15199-100000@penguin.transmeta.com`, 2001-06-28, <https://lore.kernel.org/all/Pine.LNX.4.33.0106280956030.15199-100000%40penguin.transmeta.com/>
  > Let's make it policy that we _never_ print out annoying messages that have no useful purpose for debugging or running the system, ok?
- `Pine.LNX.4.33.0106280956030.15199-100000@penguin.transmeta.com`, 2001-06-28, <https://lore.kernel.org/all/Pine.LNX.4.33.0106280956030.15199-100000%40penguin.transmeta.com/>
  > "Informational" messages aren't informational, they're just annoying, and they hide the _real_ stuff.
- `CA+55aFwH4UL-76-=ygDww4=vC9U=6_Yhs0D0H-nwtAkKXC6Vag@mail.gmail.com`, 2014-08-21, <https://lore.kernel.org/all/CA%2B55aFwH4UL-76-%3DygDww4%3DvC9U%3D6_Yhs0D0H-nwtAkKXC6Vag%40mail.gmail.com/>
  > Printing pointless hotplug information for them is just crazy, and takes up kernel message space and hides _real_ messages for no good reason.
- `CA+55aFw4hfHMNn_vPGwKjUafV42C+H5ba4S29iJvk225etZ1pg@mail.gmail.com`, 2016-08-26, <https://lore.kernel.org/all/CA%2B55aFw4hfHMNn_vPGwKjUafV42C%2BH5ba4S29iJvk225etZ1pg%40mail.gmail.com/>
  > So in order for data to be useful, it has to be more than "data". It has to be "information". More random useless hex noise is not good.
- `CAHk-=wjVTfej6+D62rzedjY_wzBVFqH0+U5vbq+ava8VhYPH3g@mail.gmail.com`, 2023-03-21, <https://lore.kernel.org/all/CAHk-%3DwjVTfej6%2BD62rzedjY_wzBVFqH0%2BU5vbq%2Bava8VhYPH3g%40mail.gmail.com/>
  > It's fine for things that never happen, but if you can flood things without the rate limiting, you can still flood things with the rate limiting.
- `6cd06ab12d1afdab3847e7981f301bd0404aaa5c`, 2023-07-05, <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=6cd06ab12d1afdab3847e7981f301bd0404aaa5c>
  > Which not only causes extra noise in itself, but might also end up hiding any real cases if they do exist.

**How well supported.** About 10 distinct messages and commits, 2001 to 2023 (2001, 2007, 2009, 2011 commit,
2014 x2, 2016, 2023 x2).

---

## 20. Retries and timeouts must have a reason; a retry often hides a bug

**Principle.** Every retry or timeout needs a stated reason. Arbitrary retry counts, retries on errors that will not
go away (out of memory, I/O error), and timeouts tuned to make a failure disappear are suspicious; ask whether the
retry is hiding a race or a bug.

**What triggers it in a review.**
- Magic retry counts (1000 tries), nested retry loops that multiply.
- Retrying on permanent errors.
- Quirk tables and timeouts tuned to hide one failing case.

**His reasoning.** An old retry "was hiding some locking problem" and lingered after the races were fixed (2011).
Either retry forever or fall back immediately; a thousand tries is neither (2013). Retrying on OOM or I/O errors
changes error semantics (2023).

**How serious.** Asks questions and requests rework; not a top-tier issue.

**Limits and exceptions.** Time-bounded retries exist and he has suggested them (2015). Retrying a transaction to
recover from hardware errors can be the right fix (2007, see principle 17).

**Outside the kernel.** Transfers well: flag retries without backoff or without classifying errors as transient
vs permanent, retry counts with no rationale, and timeouts increased to make a flaky test pass.

**Evidence.**
- `AANLkTikvXSZ2NSA7Ar+bTA1H+S3HBs9e5NNb71RPTs32@mail.gmail.com`, 2011-03-31, <https://lore.kernel.org/all/AANLkTikvXSZ2NSA7Ar%2BbTA1H%2BS3HBs9e5NNb71RPTs32%40mail.gmail.com/>
  > At a guess, it was hiding some locking problem - and it's been carried around even though hopefully we've fixed all the crazy races we used to have (and it was a mindless "hey, we can retry in one jiffy - it doesn't really cost us anything")
- `CA+55aFze8ZC0YP+TdwDFRPpa=BqUhY25RhEJb6c9pkCk2CZfVA@mail.gmail.com`, 2013-08-22, <https://lore.kernel.org/all/CA%2B55aFze8ZC0YP%2BTdwDFRPpa%3DBqUhY25RhEJb6c9pkCk2CZfVA%40mail.gmail.com/>
  > First off, the thousand-time retry seems completely excessive. Does it actually need any retry AT ALL? If the hash entry changes, either you should retry forever, or if you feel that can result in livelocks (fair enough) and you need a fallback case to a bigger lock, then why not just do the fallback immediately?
- `CAHk-=wiZ0GaAdqyke-egjBRaqP-QdLcX=8gNk7m6Hx7rXjcXVQ@mail.gmail.com`, 2023-05-06, <https://lore.kernel.org/all/CAHk-%3DwiZ0GaAdqyke-egjBRaqP-QdLcX%3D8gNk7m6Hx7rXjcXVQ%40mail.gmail.com/>
  > I do not believe that retrying the fault is the right thing to do when we ran out of memory, or when we had an IO error, and I do not think it was intentional that the error handling was changed.
- `alpine.LFD.2.00.1005130724280.3711@i5.linux-foundation.org`, 2010-05-13, <https://lore.kernel.org/all/alpine.LFD.2.00.1005130724280.3711%40i5.linux-foundation.org/>
  > It is _not_ maintainable to create random tables of exceptions ("DMI tables"), and it's actively _wrong_ to do for something like this where we not only have historically worked perfectly well, and this apparently tries to hide some other bug

**How well supported.** Thin: about 7 distinct messages, 2003 to 2023 (2003, 2010, 2011, 2012, 2013, 2015,
2023). Principle is clear but the corpus has no general statement on retries.

---

## Changes of position over time

| Topic | Earlier | Later / current |
|---|---|---|
| BUG() vs assert | 2000: likes BUG() *because* it lacks the psychological mindset of assert() | 2002: BUG() almost always wrong; 2012-2020 harsher; 2022: aim for WARN_ON_ONCE; current: WARN_ON_ONCE plus handling |
| panic() | 1992: earlier kernels panicked on inode exhaustion, 0.99 waits instead; 2001: no panic for data-structure limits | 2022: panic only for boot failures or by operator choice |
| WARN_ON | Did not exist before Oct 2002; he added it as a polite BUG_ON that does not kill the machine (commit `0fffce8`) | 2018-2022: WARN_ON_ONCE preferred; repeated warnings seen as spam |
| Debuggers | 2000: dislikes debuggers; no kernel debugger | 2008: kgdb merged if minimal; 2026: still says understand the code, printk debugging is "a failure mode" |
| Security bugs | 2008: just normal bugs, no special marking | Unchanged through 2017 and 2026 ("Bugs are bugs") |
| Hardening | 2005: balance; 2017: warn first, then enforce | 2026: still mocks hardening that makes machines unbootable |
| Disclosure | 2005: short embargoes only, days | 2018 "timely open fixes"; 2018, 2022 complaints that embargoes bypass testing; 2026 AI-found bugs public |
| Scope cleanup | Did not exist before 2023 | 2023 cautious adoption; 2024-2025 opposes complex guard variants and mindless conversion |
| Tone | Through 2017: open abuse (the 2017 hardening mail calls people morons) | After 2018 same positions, more explanation, less abuse |

## Not in corpus

Searched and not found (do not quote these from memory):

- A single general statement on retries/backoff policy; only case-by-case remarks.
- A general view on exceptions in C++ or other languages as an error-handling mechanism (his C++ comments in the
  corpus are about the language, not error handling). The exceptions transfer above is inferred from his Rust and
  BUG_ON mails.
- A direct general statement on TOCTOU for user memory; found only the 2015 `READ_ONCE` mail (the value tested must be
  the value used) and the sg double-read analysis (2018).
- An explicit statement about assertion policy in user-space services; the transfer is inferred.
- The coding-style.rst rule "Do not add new code that uses any of the BUG() variants" is in the corpus but in a
  multi-author document, so it is not quoted as his words.
- The well-known OpenBSD "monkeys" line (2008, `alpine.LFD.1.10.0807150907480.3017@woody.linux-foundation.org`)
  and the 2017 hardening "morons" line (`CA+55aFykjza0...`) *are* in the corpus; they are not quoted because the
  reasoning around them is more useful.

## What I looked for and did not find

- Praise of a specific hardening feature as a model: found only general support for generic class-wide
  mitigations (2017) and for syzbot/KASAN as bug finders.
- Fuzzing policy beyond KCSAN, syzbot and KASAN remarks.
- A position on `Result`/`?`-style propagation in Rust beyond the allocation-failure and panic mails.
- Statements on timeouts as such (only one 2003 borderline-timeout mail and a 2015 suggestion).
