# Compatibility: never break users

Load this when: a diff changes something outside code can observe (public function semantics, error codes, CLI flags or output, wire or file formats, config keys or defaults, schemas, endpoints) or removes or deprecates one, or a regression is answered with a new fix instead of a revert.

Basis: he said this about the kernel's user-space ABI and git's formats, protocol and output. Library, CLI and config applications are a close reading; database schema and REST/gRPC applications are inferred.

## Quick scan

1. Does any existing caller, script or stored file see a different result, documented or not?
2. Is new behaviour behind a new explicit opt-in, or does it change an old call, flag or default?
3. Does this fix one case by breaking another, or answer a regression with a new fix instead of a revert?
4. Does a new interface reject unknown flags and fields from day one? Does it take a bare boolean?
5. Does it expose more surface (output field, knob, debug hook) than needed, or change parsed output?
6. Do new options default off, and does an existing config still produce the same result?
7. Is something removed because a date passed, rather than on evidence nobody uses it?
8. Can old and new versions of each side run in either order, with no flag day?
9. Internal API change: are all callers converted, and does a semantic change rename it?
10. Does a real workload get slower, not just a microbenchmark?

## 1. Behaviour users depend on is the contract, and breaking it is the change's bug

**Severity:** reject      **Basis:** his words (kernel ABI, git). Library, CLI and config transfer is close; schema and REST/gRPC transfer is inferred.
**Rule:** If an existing caller, script, config or stored file worked before and does not after, the change is wrong. This holds whatever the docs said, whatever the author intended, and even if the caller relied on a bug. Never answer with *the client was misusing it* or *just upgrade your tool*.
**Look for:**
- A changed error code or exception type, return value, sort order, rounding, whitespace or field order in output, exit status, or accepted-input set, justified as *more correct*, *spec-compliant* or *cleanup*.
- Fixing a long-standing quirk (a parser now rejecting trailing commas) without asking who relies on it.
- Review replies that point at the docs (*never documented*, *private*, *undefined behaviour*) or tell reporters to update their side.
- Inferred examples: Python `raise ValueError` where callers caught `KeyError`; `--json` output gaining a wrapper; a renamed column old queries hit; a REST field changing type.
**Why:** People must always feel safe upgrading. A regression costs downstream far more than an old quirk. Documentation that disagrees with behaviour is wrong documentation; something becomes interface by being useful and available.
**Unless:**
- Nobody notices: no broken workflow, no regression (proving that is usually harder than not changing it).
- Security fixes, the one named exception; still keep the old visible behaviour where possible.
- Unnoticed for years: too late to revert.
- One or two expert users who can work around it.
- Only a test changed: a red flag, not a regression.
- Out-of-tree or private code that bypassed the published interface; theoretical breakage.
**He said:** "If it used to work, it should continue to work, even if it wasn't _meant_ to work." (2008-06-24, `alpine.LFD.1.10.0806232004480.2926@woody.linux-foundation.org`)

## 2. New behaviour needs a new opt-in, not a changed default and not a version check

**Severity:** reject when the change alters old behaviour; rework to put it behind an opt-in      **Basis:** his words (syscalls, flags). Library and CLI transfer is close; REST/gRPC transfer is inferred.
**Rule:** Leave the old call, flag or default doing what it did. Add a new flag, parameter, function or subcommand that says *I want the new behaviour*. Callers should detect a feature by trying it and falling back, never by comparing version numbers.
**Look for:**
- Changing what an existing flag or argument value means, or what `flags=0` or the no-option default does.
- An `api_version` switch for consumers to branch on instead of an explicit opt-in; versions do nothing for shipped binaries.
- Client code that does `if lib.__version__ >= ...` or parses `--version` to decide behaviour.
- Inferred example: adding `strict=False` to `load()` is fine; flipping it to `True` later is not.
**Why:** The old interface must be kept essentially forever anyway; explicit opt-in leaves the choice with the caller.
**Unless:** Security, or an implementation that genuinely cannot be kept. Never change for its own sake; he applies that to library developers too.
**He said:** "When we add NEW BEHAVIOUR, we don't add it to old interfaces when that breaks old user mode!" (2007-08-31, `alpine.LFD.0.999.0708310055010.25853@woody.linux-foundation.org`)
**He said:** "Absolutely *no* user space shjould ever care about kernel versions. If you want to use a new system call or something, just *use* if, and then if it fails, fall back to the old one." (2018-08-03, `CA+55aFyFXxN3Qkt+=Ke5Mqctbc3+iX5_HzeH0gHFZK8tDpa=Uw@mail.gmail.com`)

## 3. A fix that breaks another working case is not a fix, so revert first

**Severity:** reject      **Basis:** his words (kernel). Transfer to any shared codebase is close.
**Rule:** Things that used to work outrank things that never worked. Do not trade one user's breakage for another's fix. When a regression is traced to a change and no safe fix is obvious, revert it quickly (his rule of thumb is within a week, before the next pre-release) and rethink.
**Look for:**
- Making a new device, input or spec case work by changing a path existing users take, argued as mattering more.
- A regression report answered with a new, larger fix while releases go by, or a NAK of a plain revert.
**Why:** A revert can only affect people for whom the change never worked; a new fix may break untested users. Known, consistent bugs beat bugs that move around.
**Unless:**
- Cases that never worked can keep not working; that is not a regression.
- Already shipped in an earlier release: reverting just before the next one can be more dangerous. Found after a decade: not reverted as a regression.
- A known, acceptable real fix beats a revert.
**He said:** "Things that used to work are simply a million times more important than things that historically didn't work." (2013-02-23, `CA+55aFxcqczXZf7zxJ0xjDsnLMbS8uu9Jp5BDOdnR5tqf==nrA@mail.gmail.com`)

## 4. New interfaces must be extensible and enforce their rules from day one

**Severity:** rework      **Basis:** his words (syscalls, uapi structs). Library, CLI and format transfer is close; REST/gRPC and schema transfer is inferred.
**Rule:** A new interface gets room to grow: a flags or options argument, or an extensible struct or message. Unknown bits, fields and values are rejected from the first release, so they can be given meaning later. Validation added after release is itself a breaking change.
**Look for:**
- A bare boolean parameter on a new public function or endpoint; use flags or options.
- Flags or options accepted but never checked (missing C `if (flags & ~KNOWN) return -EINVAL;`).
- A wire or on-disk struct with implicit padding or internal types; keep the external layout separate from the in-memory one.
- A patch to a released interface that starts rejecting input it used to accept silently.
- Semantics shaped by the current implementation's quirk rather than a clear concept.
**Why:** Without hard checks an interface is stuck with whatever callers assume, and unchecked bits can never be reused.
**Unless:** Flags exist for future extension, not as a substitute for design. He objects to piles of random flags with no coherent meaning just as much.
**He said:** "This is why system calls and ABI's need to have hard rules that they actually check, because if they don't, they are stuck with the semantics that people assume." (2026-04-23, `CAHk-=wh=B3fqU9AaBsyViZR=eVTG5qa2CGyN=qxPROVxu9Gctg@mail.gmail.com`)
**He said:** "Nobody should ever use 'bool' as a system call argument. Anything that takes a boolean should take a 'flags' field with bits." (2026-06-04, `CAHk-=wip3mwLOHOYJ9TtjDxOaq9YUXmuCg2AycyASGgeY6qqUw@mail.gmail.com`)

## 5. Every visible thing becomes interface, so expose little and freeze what is parsed

**Severity:** rework (grumble for small additions)      **Basis:** his words (ioctls, /proc, tracepoints, git output). CLI, log and metric transfer is close.
**Rule:** Anything others can script against becomes contract: output text, field layout, metric and log names, debug hooks, entry points. Keep the surface thin, prefer automatic behaviour to a knob, keep machine-read output fixed, and keep a meaningless field with a neutral value rather than delete it.
**Look for:**
- A new endpoint, command multiplexer or tunable where automatic behaviour would do.
- Format changes to script-parsed output (`--porcelain`, `--json`, CSV columns, log lines).
- A removed or reordered field in a status file or report; keep it, report 0 or empty.
- Internal state exposed via debug or trace output.
- A *self-describing format* offered as the excuse for changing a layout.
**Why:** Tools root around for the values they want and break when those vanish. The thinner the interface, the freer the implementation.
**Unless:** Human-only output (decorations, prose messages) is not expected to be parsed. A trace or debug hook becomes contract only once real tools rely on it, but at that point it does.
**He said:** "If you made an interface that can be used without parsing the interface description, then we're stuck with the interface. Theory simply doesn't matter." (2011-05-06, `BANLkTim9YvResB+PwRp7QTK-a5VNg2PvmQ@mail.gmail.com`)

## 6. Option defaults: new features off, existing configs unchanged, no questions users cannot answer

**Severity:** rework (reject if an upgrade silently changes what an existing config produces)      **Basis:** his words about kernel build configuration; transfer to application config keys and CLI options inferred.
**Rule:**
- New features default off.
- When existing behaviour is moved behind a new option, that option defaults on, so old configs keep their result.
- Do not ask questions that need knowledge of the internals; ask about the user's situation and derive the rest.
- When an option's meaning or default changes, rename the key rather than silently reinterpret the old value.
**Look for:**
- A new feature flag or config key defaulting to enabled, with no reason why everyone wants it.
- A config split or rename after which an upgraded config file quietly loses something it had.
- A new setting added because the developer could not decide the right value.
**Why:** Developers always want their own feature on, and an upgrade should leave a setup producing what it did.
**Unless:** Default on is right for code that existed before and was merely made optional, for things nearly every user needs, and for pure dependencies of something already enabled.
**He said:** "I'd really like the basic rule to be that all new features start out as 'default n'." (2012-01-07, `CA+55aFwsTfGRkKASqa_LFQwGZnYyTdVTzb4MG=2Ywv+bG1E1Qw@mail.gmail.com`)
**He said:** "Dammit, if the developer doesn't know, then a user sure as hell doesn't either." (2024-07-16, `CAHk-=wj+4yA5jtzbTjctrk7Xu+88H=it2m5a-bpnnFeCQP7r=A@mail.gmail.com`)

## 7. Remove something only on evidence of no users, not because a deadline passed

**Severity:** reject (removal on a schedule alone)      **Basis:** his words (kernel interfaces). Transfer to API versions, flags and config keys is close; dropping schema columns is inferred.
**Rule:** Compatibility has no time limit, and a sunset date is not evidence of non-use. Either it is unused and can go now, or there is no reason to remove it. Acceptable evidence is a removal nobody notices: warn first if you like, remove early in a cycle, and restore it or leave a do-nothing stub if anyone complains.
**Look for:**
- A diff that says *deprecated since vN, removing*, with no usage data.
- Calling something *legacy* when current clients still use it.
- A removal where a no-op stub (an accepted-but-ignored flag, an empty file or field) would satisfy the remaining callers.
**Why:** Time does not end dependence; only non-use does, and the sooner you find out the better. Removal schedules invite removing things people merely dislike.
**Unless:** Platform support with no real users left can go (and return if someone shows up). Something removed in a shipped major release after long notice is not owed a return.
**He said:** "There is no time limit. It's not about time. It's about not breaking user space." (2012-11-13, `CA+55aFwSxwjqK8CScNBWvzk=ExDqREAGAyRoZLW4zjOu4dyxqw@mail.gmail.com`)

## 8. No lock-step upgrades: formats and protocols work across versions

**Severity:** reject      **Basis:** his words (kernel and user space, git repository format and protocol). Client/server and file-format transfer is close; schema migrations are inferred.
**Rule:** New code must work with old peers, files and consumers; nothing may force both sides to upgrade together. Writers produce what older readers can read; protocols extend by negotiation.
**Look for:**
- A release that needs the client, plugin or worker upgraded at the same moment.
- A format change that strands older versions sharing the data, or a protocol change with no old-peer fallback.
- Inferred: a schema migration and code change that must deploy atomically. Prefer expand, migrate, then contract.
- Free-form extension fields whose meaning will drift between consumers.
**Why:** Lock-step upgrades stop users upgrading and stop bisection, since nobody can tell which side broke. Fields with drifting meanings become an unresolvable mess.
**Unless:** A new feature may require the newer version of the other side.
**He said:** "But if you have a TWO-WAY dependency, you're screwed. That means that you have to upgrade in lock-step, and that just IS NOT ACCEPTABLE." (2006-02-22, `Pine.LNX.4.64.0602220848280.30245@g5.osdl.org`)

## 9. Internal APIs are free to change: convert every caller and make the break loud

**Severity:** rework      **Basis:** his words (in-kernel APIs). Transfer to internal modules in any repository is close.
**Rule:** Stability covers external interfaces only; internals may change at any time (the contrast that stops false alarms from rule 1). Whoever changes an internal API fixes all callers in the same change, and renames or retypes it when semantics change so stale callers fail to compile. A parallel *new_foo* beside *foo* means owning both forever.
**Look for:**
- Behaviour changed but name and type did not, so callers compile and are silently wrong.
- A new variant beside the old one with callers unconverted, or shims kept for callers that could be updated.
- Do not flag internal refactors as compat breaks just because signatures change.
**Why:** Internal freedom makes fixes and cleanups possible; compiler errors keep it safe. Still, no change just to be difficult.
**Unless:** Headers or modules that outside code actually includes or imports are external, even if they were meant to be internal. Treat them under rule 1.
**He said:** "Here's the only thing that works: if you change the API, you have to fix up all existing users." (2025-08-26, `CAHk-=wgOXd-meRuz5Gv2oz0W0wBUOpMO5CK9eifjfdR5Xz_-Fw@mail.gmail.com`)

## 10. Performance regressions count when real workloads see them

**Severity:** rework (revert once a real workload confirms the slowdown)      **Basis:** his words (kernel). Transfer to services and libraries is inferred.
**Rule:** A real workload getting slower is a regression, even if the program doing it is inefficient. Winning on a different benchmark does not answer it. A slowdown seen only on a microbenchmark is a reason to watch, not to block or revert.
**Look for:**
- A reply to a production slowdown that points at a microbenchmark win.
- A change blocked only on a synthetic benchmark, with no workload behind it.
**Why:** Real programs decide what matters, and odd user programs never go away, so fix the slowdown rather than scold the program.
**Unless:** A bad or purely synthetic benchmark. Wait until a real workload complains.
**He said:** "It doesn't matter one whit if SLUB is lots faster, if it's faster for cases that never matter." (2007-12-21, `alpine.LFD.0.9999.0712211442000.21557@woody.linux-foundation.org`)
