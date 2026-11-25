# Robustness: error handling, failure behaviour, debugging and security

Load this when: a diff touches crash/panic/assert calls, error returns, cleanup paths, allocation failure, input
validation, retries, log messages, security checks, or fixes a tool report or flaky bug.

## Quick scan

1. Does it end the process or system for something that could fail one operation instead?
2. Is error-path cleanup complete, in reverse order, visible, and unconditional where guards or RAII are used?
3. Is untrusted input bounded at the boundary, and trusted internal data left alone?
4. Is a failure that matters left unchecked, or junk handling forced onto results nobody can act on?
5. Is there a check or assert for something that *cannot happen*, and can it?
6. Does a warning fire and then the bad thing happen anyway, or fire repeatedly?
7. Does the fix name the cause, or add a delay, retry or special case until the symptom goes away?
8. Was code changed only to quiet a compiler, linter, sanitizer or analyzer?
9. Will a new log line help someone act, or hide real messages?
10. Can the author say why the change works?
11. Does a security check block on first violation, or cost a lot with no measured threat?

## 1. Fail the operation, not the system; allocation failure is an error return

**Severity:** reject for a new crash on a recoverable path in shared or core code; rework elsewhere
**Basis:** his words about kernel code, including kernel Rust; user-space `panic!`/`unwrap`, exceptions and service policy are transfer inferred
**Rule:** Do not kill the process, service or machine because an assumption failed or a resource ran out. Return an
error and fail that one request. Crash only when continuing would spread corruption; turning warnings into crashes
is the operator's configuration, not the code's choice.
**Look for:**
- New `BUG_ON`/`panic`/`abort`/`exit`/release-build `assert`. Inferred: Rust `unwrap()`/`expect()` on I/O, parse,
  network or allocation results, `panic!` in a library; `sys.exit`/`process.exit` in a library; an exception that
  kills a worker with no error reply and no log.
- Exhaustion treated as fatal: crash on a failed allocation, *table full*, counter overflow. Return `-ENOMEM`,
  `Err(..)`, a 503.
- Plugins, drivers and other non-core modules that can bring down their host; *kill on anomaly* with no off switch.

**Why:** A crashed system reports nothing (it often dies holding locks, with no log), and a user-triggerable crash
is a denial-of-service hole. Non-core code cannot know what the rest of the system needs.
**Unless:** continuing would corrupt persistent state; failure during early startup; an operator opted into
fail-fast. Inferred: a supervised worker may exit after failing the request cleanly and logging why.
**He said:** "Running out of memory simply MUST NOT cause an abort.  It needs to just result in an error return." (2021-04-14, `CAHk-=wh_sNLoz84AUUzuqXEsYH35u=8HV3vK-jbRbJ_B-JjGrg@mail.gmail.com`)
**He said:** "a working machine is about a million times easier to debug on than a dead one" (2002-09-10, `news:fa.mau2div.140088o@ifi.uio.no`)

## 2. Error unwinding and scope-based cleanup

**Severity:** rework for wrong order, leaks or undoable partial setup; grumble for style
**Basis:** his words about kernel C and `cleanup.h` guards; `defer`/RAII/`finally`/`with` are transfer inferred
**Rule:** Undo setup in exact reverse order through one error exit (labels in C; `defer`, destructors, `finally`,
context managers elsewhere) rather than deep nesting. When the unwind steps are too many to see, split the function.
Teardown must cope with whatever a partial setup left. Guards and automatic cleanup suit only a resource that is
always released at scope end.
**Look for:** nested success checks where early exits would be flat; a dozen labels in one function; label order not
mirroring setup; an error path that skips a release or releases something never acquired; partial state only the
success path can tear down; `goto` for ordinary control flow; a guard where one return path keeps the lock;
custom maybe-release guard types; mass rewrites of working error handling into guards with no bug fixed.

```c
a = get_a(); if (!a) return -ENOMEM;
b = get_b(); if (!b) goto put_a;
if (start(b)) goto put_b;
return 0;
put_b: release_b(b);
put_a: release_a(a);
return -ENOMEM;
```
**Why:** Gotos are often more readable than indentation, but cleanup in the wrong order is an easy, common mistake,
so the structure must stay visible; past a point the fix is helper functions, not more labels. Conditional
automatic cleanup is dangerous, and mindless conversions made ugly code worse.
**Unless:** trivial flow where a plain return is clearer. Replacing a plain goto-exit pattern with a guard in new or
clearly simpler code is the intended use.
**He said:** "I like "goto error", but at some point you can't see the unwinding any more" (2010-06-02, `alpine.LFD.2.00.1006012137390.8175@i5.linux-foundation.org`)
**He said:** "If a sane 'guard' model doesn't work for some code, the answer is not to make an insane guard model. The answer is to not use 'guard' in code like that." (2024-02-27, `CAHk-=win7bwWhPJ=iuW4h-sDTqbX6v9_LJnMaO3KxVfPSs81bQ@mail.gmail.com`)

## 3. Validate untrusted input at the boundary; trust internal callers

**Severity:** reject for an unchecked untrusted size, count or index; rework for misplaced or redundant checks
**Basis:** his words about user input to the kernel; API and service use is transfer inferred
**Rule:** Data crossing a trust boundary gets a sanity check with a practical limit, not just *does not overflow*.
Read it once and use the value you checked, with the check next to the use. Track where data came from; do not
re-validate trusted callers.
**Look for:** external lengths used to allocate or index with no upper bound; check-then-reread of shared or user
memory (time-of-check/time-of-use); validation on one path but not another to the same operation; layers of defensive
checks on internal data that hide where validation really happens.
**Why:** Limits must reflect practical issues, and checks far from the use, or missing in one caller, are common bugs.
Defensive code on trusted data is just bogus code.
**Unless:** trusted sources (admin settings, internal subsystems): trust them. Wraparound is not automatically a bug;
`a + b < a` is a valid overflow check.
**He said:** "User space input absolutely has to be validated for sanity." (2025-04-09, `CAHk-=whLixL8-iYt1qH0-YvEnVsYtryZaN5Da0qoBBhKsBnumw@mail.gmail.com`)

## 4. Check the errors that matter; do not force checks that do not

**Severity:** rework for an unchecked failure that matters; grumble at forced pointless checks
**Basis:** his words; `#[must_use]` and lint rules are transfer inferred
**Rule:** Check errors that happen and need action (I/O, allocation, copies from untrusted memory). Do not force
every caller to check everything; a callee whose errors are that serious should handle them itself. Never *handle*
an error by retrying a non-idempotent call.
**Look for:** ignored results that change what must happen next; blanket `must_check`/`#[must_use]` followed by junk
handling; retrying `close()` on `EINTR` (in threaded code it may close another file).
**Why:** Forced checks that callers cannot act on produce bogus code and more bugs than they prevent.
**Unless:** forcing is right where skipping the check is a real and obvious security issue, or where errors are
common and need action. A pre-check (`access_ok`) does not excuse ignoring the later copy's result.
**He said:** "I think "must_check" is an abomination. It makes the callee dictate what the caller has to do, but dammit, if the callee really "knows" its errors are that serious, it should damn well handle them itself." (2007-07-19, `news:fa.lazKVQYX9tVjZPb69scMJ09zsrA@ifi.uio.no`)

## 5. Cannot-happen checks and asserts: delete them or handle the case

**Severity:** rework
**Basis:** his words about kernel code; `assert`/`unreachable!`/`debug_assert!` are transfer inferred
**Rule:** If it truly cannot happen, write no code for it; if you are not sure, it can, so handle it or warn once
(see 6). Asserts are development aids, not error handling. When one fires, first ask whether the assert is wrong.
**Look for:** fatal checks the surrounding code already guarantees; new error returns for impossible cases that every
caller must propagate; release-build `assert` as validation; logic rewritten only because an assert fired; debug-only
checks nobody ever runs enabled.
**Why:** Such a check is dead code or an untested crash path, and *this can't happen* does happen once code changes.
**Unless:** asserts in development and test builds are fine.
**He said:** "BUG_ON() is not a debug aid. If it's a "cannot happen" condition, you don't write any code for it at all. And if it's a "I'm not sure this cannot happen", you either handle it (like this patch does), or you do a "WARN_ON()" with proper cleanup." (2020-11-08, `CAHk-=wh3_NkjfHmhTSMsHVxVji1+Fp_f_SByFRspR+KW4uqWWQ@mail.gmail.com`)

## 6. Warn once and stay consistent; once reachable, make it a real error

**Severity:** rework
**Basis:** his words about kernel code; logging and metrics are transfer inferred
**Rule:** For a should-not-happen case, warn once with a backtrace, then skip or fail the action; never go on and do
the bad thing. When input or odd hardware can trigger it, replace the warning with an ordinary error return.
**Look for:** a warning or `log.error` followed by use of the invalid value; a repeatable warning with no once or rate
limit; a known-reachable condition still treated as a warning.
**Why:** One warning gives the backtrace without flooding logs if users can trigger it; a warning followed by
corruption only documents the damage.
**Unless:** exiting on warnings is an operator setting; a kill-on-warn mode users can trigger becomes an attack.
**He said:** "So rather than warn about us doing bad things, stop doing the bad things and return -EIO." (2023-01-04, `cb7a95af78d29442b8294683eca4897544b8ef46`)

## 7. Fix the root cause; delays, retries and special cases need a reason

**Severity:** reject when nobody tried to find the cause; grumble at a labelled stopgap
**Basis:** his words. The retry part rests on about seven case-by-case remarks (2003 to 2023), not a stated policy:
use it as a strong default.
**Rule:** A fix names the cause and removes it. A delay, retry, longer timeout, exception list or silenced detector
that makes a symptom vanish is not a fix unless someone looked and the stopgap is labelled. Every retry states what
transient condition it waits out and why the count is what it is.
**Look for:** `sleep`, bigger timeouts or retries added because they stop a flake; magic or nested retry counts;
retrying permanent errors (out of memory, I/O error); a watchdog or health check silenced instead of fixed.
**Why:** Papering over makes people less likely to fix the real problem, and an old retry can hide a race long after
anyone remembers why it exists.
**Unless:** sometimes no proper fix exists and the workaround is the best solution; band-aids for theoretical worst
cases and clearly marked temporary stopgaps are fine; retrying a transaction after real hardware errors can be right.
The reverse case is not papering over: a known bug in hardware, firmware or a dependency you cannot change must be
worked around (in his view a driver that ignores a BIOS bug is buggy); prefer probing over vendor tables.
**He said:** "We don't "fix" things by papering over some symptom. We try to fix the _actual_ underlying problem." (2017-08-15, `CA+55aFyHVV=eTtAocUrNLymQOCj55qkF58+N+Tjr2YS9TrqFow@mail.gmail.com`)

## 8. Do not change code only to silence a tool

**Severity:** reject for a warning fixed without understanding the code; rework otherwise
**Basis:** his words; linter and type-checker examples are transfer inferred
**Rule:** Act on a tool report only if it is interesting, correct and valid; otherwise fix the tool, its config or
the cause of the false report. Never fix a warning without understanding the code.
**Look for:** dummy initialisers, casts, sprinkled `READ_ONCE`; inferred: `#[allow]`, `eslint-disable`,
`type: ignore`, `as any`, non-null `!`, sanitizer suppressions; commits titled *fix warning* that say nothing about
what was wrong; correct idioms rewritten for a checker.
**Why:** Added code adds bugs; sign-warning fixes and dummy initialisers have hidden or created real bugs.
**Unless:** tools that find real bugs (KASAN, syzbot) are welcome; fixing what they found is the point.
**He said:** "People shut up warnings by adding code. Adding code tends to add bugs." (2007-07-19, `news:fa.VQX6eUxuNQf8Oq/rUVzh1vD9+90@ifi.uio.no`)

## 9. Log messages must be actionable information

**Severity:** rework; he treats new log spam as a regression
**Basis:** his words; service logging is transfer inferred
**Rule:** Print only what helps someone run or debug the system.
**Look for:** info lines on every normal probe or request; error severity for expected failures; uninterpreted hex
dumps or whole payloads; messages a client can trigger in a loop.
**Why:** Noise hides the real messages.
**Unless:** messages genuinely useful for debugging. Rate limiting does not fix a flood that should not exist; for a
should-never-happen message a very long limit (once a day) is reasonable.
**He said:** ""Informational" messages aren't informational, they're just annoying, and they hide the _real_ stuff." (2001-06-28, `Pine.LNX.4.33.0106280956030.15199-100000@penguin.transmeta.com`)

## 10. Understand the code before changing it

**Severity:** reject when the author cannot explain why the change works
**Basis:** his words; transfers directly
**Rule:** A fix explains the mechanism and why the change addresses it. Trial-and-error changes, and copied code
whose steps the author cannot explain, are not fixes.
**Look for:** commit messages with no cause; copied code with unexplained steps; permanent debug output in production
paths left from chasing one bug.
**Unless:** debuggers and print debugging are fine as tools; the rule is about understanding.
**He said:** "Stop making random changes that just happen to work on the one machine you tested it on." (2023-12-14, `CAHk-=wiKooX5vOu6TgGPEwdX--k0DyE4ntJDU4QzbVFMWGVXFw@mail.gmail.com`)

## 11. Security bugs are bugs: warn before enforcing; make measures earn their cost

**Severity:** reject for new enforcement that breaks working users, or hot-path cost with no threat or numbers
**Basis:** his words about kernel hardening and mitigations; report-only rollout of WAF, CSP or auth rules is transfer inferred
**Rule:** Fix a security bug's root cause like any bug. New hardening warns first and enforces only after the
legitimate cases are known. Weigh each measure's real attack against its cost in usability, debuggability and speed;
ask for numbers; reject measures that only look secure.
**Look for:** checks that kill, block or panic on first violation; hardening on by default with no warning period;
blocking one exploit input but not the bug; redaction that mainly blinds bug reports; expensive hot-path mitigations
with no benchmark.
**Why:** New rules hit legitimate cases nobody knew about: warning finds them, killing breaks users.
**Unless:** acute exploitable holes get fixed even if behaviour breaks; enforcement is fine after a long warning
period; generic mitigations for whole bug classes are welcome, ideally as a user choice.
**He said:** "We don't kill processes or forbid them from doing things that might be bad. We start by warning about them, to see what "might be bad" cases are actually normal, and not actually bad at all." (2017-11-29, `CA+55aFyybavkF8ccQKJsoVAF+MG=J5=e9PxXKU=J_hqCQRZnug@mail.gmail.com`)

## Position changes

- His 2000 preference for `BUG()` over `assert()` is outdated: from 2002, firmly by 2012 to 2022, any crash-on-check
  is wrong and WARN_ON_ONCE plus real handling is current.
- Scope-based cleanup arrived in 2023; his reservations about complex guard variants (2024, 2025) are current.
