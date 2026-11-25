# Theme: design

Linus Torvalds's engineering judgement above the level of a single patch, how it shows in the user-space programs
he wrote himself (git, sparse, subsurface), and the design of git as he explained it in 2005 to 2007.

Every quote below is in `analysis/design.quotes.jsonl` and passes `scripts/verify_quotes.py` (150/150). Each
evidence line gives the document `id`, its date and its URL. "Read" counts below are documents read in full or in
their substantive part (his own lines), not search hits.

**Where the statements were made.** This theme carries the skill's claim to apply outside the kernel, so every
principle is tagged:

- **[kernel]**: said about kernel code. It transfers only by analogy.
- **[tool/app]**: said about git, sparse, subsurface or user-space programs in general. It applies directly.
- **[general]**: he framed it as a general rule of software or engineering (Usenet comp.arch, management-style,
  the 2001 "Software evolves" post).

Part A covers general design judgement (principles 1 to 13), Part B the design of git (14 to 19), and Part C his
application code (20 and 21).

---

## Part A. General design judgement

### 1. Solve the problem someone actually has, and make them show it [kernel, general; tool for the fsync case]

**Principle.** A change has to be justified by a real, present user or failure, with data from a real load. A
problem that "could happen", a hypothetical device, or a micro-benchmark is not a reason to add code or
complexity, and a theoretical objection is not a reason to block a practical fix.

**What triggers it in a review.**
- A PR description that says "this will let us later...", "in case someone needs...", "for flexibility", with no
  caller, bug report or measurement.
- Benchmarks of the mechanism alone (how fast a per-thread counter increments) instead of the application that motivated it.
- Review objections of the form "this is not guaranteed in theory" set against a change that fixes a measured
  problem.
- A configuration knob or branch added for a case nobody has reported.

**His reasoning.** Without a real user you cannot know whether the semantics are even right: the first real user
may find them "subtly incompatible" (rseq, 2017). Theoretical worries have historically cost more than they saved:
every random-number problem he can remember came from "some theoretical crypto person" removing real security (2020).
Imagined cases also push complexity into generic code that real devices do not need (async suspend, 2009).

**How serious.** He refuses to merge until real users and numbers appear ("I'm *still* not interested in having
this merged"). When the theoretical argument is used to block a practical fix, he overrides it himself ("I then
have to step in").

**Limits and exceptions.**
- **Races and locking are an explicit exception.** "Rare" is not an excuse there, because a rare race can hit one
  user constantly and is very hard to debug (2006, on CGit, a user-space tool).
- Security holes count as real once you can describe the attack: in kdbus he separated "a real and serious bug"
  (capability translation across namespaces) from complaints that were "off the mark" (2015,
  `CA+55aFwqhbN=1Tm71AFHtXeOUut5gcLpqRmH=6R1H92grDsVrw@mail.gmail.com`).
- The bar can be met. rseq was refused in 2017 for lack of real users, and the 2018 threads show him reviewing its
  4.18 fixups ("LGTM", `CA+55aFzgnTMzssSKEkoLy+Mh29aAa4sFXiV=ouXZ8ivVKEJomw@mail.gmail.com`).

**Outside the kernel.** This transfers directly. Ask for the caller, the ticket, the production trace or the
benchmark of the real workload. Treat speculative generality as a cost. Do not apply it to concurrency
correctness, where a race is a bug however rare it is.

**Evidence.**
- "You're listing totally theoretical problems, and ignoring all the _real_ problems that trying to freeze kernel
  threads has _caused_." (`alpine.LFD.0.98.0704271612380.9964@woody.linux-foundation.org`, 2007-04-27,
  https://lore.kernel.org/all/alpine.LFD.0.98.0704271612380.9964%40woody.linux-foundation.org/)
- "And RIGHT means caring about reality, not theory." and "So instead of asking "why is the slow path relevant",
  the question should be "why is some theoretical BS relevant", when history says it has never ever mattered."
  (`CAHk-=wiSw7zYVUxiGT=_TPx1fqtNNYgu0L6rC=GaSGpCDnDbVw@mail.gmail.com`, 2020-08-08,
  https://lore.kernel.org/all/CAHk-%3DwiSw7zYVUxiGT%3D_TPx1fqtNNYgu0L6rC%3DGaSGpCDnDbVw%40mail.gmail.com/)
- "But people didn't post code, people didn't post numbers, and people didn't point to actual real uses, just
  "this could happen"." and "Because without real-world uses, it's not obvious that there won't be somebody who
  goes "oh, this isn't quite enough for us, the semantics are subtly incompatible with our real-world use case"."
  (`CA+55aFy54Sk63VkS3HFnd4MPiSbgV6==NaYwr+D9sjG6KZGmHQ@mail.gmail.com`, 2017-10-13,
  https://lore.kernel.org/all/CA%2B55aFy54Sk63VkS3HFnd4MPiSbgV6%3D%3DNaYwr%2BD9sjG6KZGmHQ%40mail.gmail.com/)
- "I mean in general - something where you actually have hard data that some device really needs anythign more
  than my one-liner, and really _needs_ some complex infrastructure." (`alpine.LFD.2.00.0912150722310.14385@localhost.localdomain`,
  2009-12-15, https://lore.kernel.org/all/alpine.LFD.2.00.0912150722310.14385%40localhost.localdomain/)
- Limit: "Even if you can argue that "it doesn't matter" (and you may even be right), I personally tend to just
  consider dodgy locking to be a serious bug _whether_ it really matters or not."
  (`Pine.LNX.4.64.0612110929510.12500@woody.osdl.org`, 2006-12-11, git list, about CGit,
  https://lore.kernel.org/all/Pine.LNX.4.64.0612110929510.12500%40woody.osdl.org/)

**How well supported.** About 25 messages, 2002 to 2026: freezer 2007, random32 2020, rseq 2017, hazard pointers
2024, btree 2023, LSM 2007 ("Real usage scenarios with LSM modules, please speak up!"), async suspend 2009, memory
hotplug 2005, Rust 2025 ("how many problems has rust caused you in the last year?"), sendfile 2001, page
replacement 2006. Strong and stable across eras.

---

### 2. Software evolves; change it in small, bisectable steps, and accept a rewrite only for a measured win [general, kernel; git list for the 2007 post on up-front design]

**Principle.** Prefer a series of steps in which the code keeps working after each one. When an interface has to
change, add the new one beside the old and migrate the callers. Big up-front designs are usually wrong in ways
you only discover by using them. Flag-day switch-overs and total rewrites are a last resort.

**What triggers it in a review.**
- One commit (or one PR) that rewrites a subsystem, or a series whose last patch is "enable the new
  implementation" for everything at once.
- A migration that removes the old API in the same change that adds the new one, so nothing can be compared or
  bisected.
- A design document or framework that lands before any working use of it.

```
# raises it
PR #812: "New storage engine" (14k lines), last commit flips USE_NEW_ENGINE=1 for all tables
# what he asks for
1/n add the new interface beside the old one
2/n convert one caller (one table, one time source), ship, let it bake
...  convert the rest one at a time; drop the old interface when nothing uses it
```

**His reasoning.** Nobody, himself included, knows the right destination: "Too strong a strong vision can kill
you" (2001). Designers "concentrate on the problems of the previous generation" and build what users said they
wanted, not what they needed once they tried it (2007, git list). Evolution requires "bisectability": every
intermediate point must be viable, which is what makes a regression attributable (2008). A flag day gives a
bisection result of "the switch-over", which "tells you hardly anything" (2007). His ranked order of preference is
(a) incremental, (b) the same interfaces with A/B choice, (c) a total rewrite (2021).

**How serious.** He asks for the series to be redone one step at a time, delays merges, and holds up a rewrite
until it can be bisected or compared. He rarely refuses outright on this ground alone.

**Limits and exceptions.**
- He accepted Andrea Arcangeli's VM rewrite in the middle of 2.4, against his own stated reservations, because it
  gave "(a) better performance and (b) much cleaner" code (2001).
- He accepted the multi-generational LRU because "numbers talk" and the idea was not "so far out" (2022).
- A total rewrite is acceptable when the people who own the code really want it. Then delete the old code rather
  than carry it as dead weight (2021, fscache).
- A rare flag day is allowed. In 2008 he wanted a flag day "once or twice a year" at most.
- Making a decision reversible is itself the goal (management-style, principle 13).

**Outside the kernel.** This transfers directly: strangler-fig migrations, expand-and-contract schema changes,
feature flags per caller, "keep main green", one logical change per commit so that `git bisect` works. A reviewer
should ask "what does bisection show if this breaks?"

**Evidence.**
- "Software evolves. It isn't designed. The only question is how strictly you _control_ the evolution, and how
  open you are to external sources of mutations." (`Pine.LNX.4.33.0111301907010.1296-100000@penguin.transmeta.com`,
  2001-12-01, https://lore.kernel.org/all/Pine.LNX.4.33.0111301907010.1296-100000%40penguin.transmeta.com/)
- "So "designing" stuff is way overrated. You can spend years designing somethign that is total crap, just because
  you didn't actually try it out and _realize_ that it wasn't what the user wanted" (git list, Libification
  thread: `Pine.LNX.4.64.0703211020070.6730@woody.linux-foundation.org`, 2007-03-21,
  https://lore.kernel.org/all/Pine.LNX.4.64.0703211020070.6730%40woody.linux-foundation.org/)
- "In other words, exactly *because* evolution requires "bisectability" (any non-viable point in between is a dead
  end by definition) and does things incrementally, it doesn't do big flips." and "It involved adding the new
  interface, and letting the old one live in parallel."
  (`alpine.LFD.1.00.0802121133210.2920@woody.linux-foundation.org`, 2008-02-12,
  https://lore.kernel.org/all/alpine.LFD.1.00.0802121133210.2920%40woody.linux-foundation.org/)
- "(a) actual incremental changes where the code keeps working all the time, and no flag days (b) same interfaces,
  so at least you can do A/B testing and people can choose one or the other (c) total rewrite"
  (`CAHk-=wg2LQtWC3e4Z4EGQzEmsLjmk6jm67Ga6UMLY1MH6iDcNQ@mail.gmail.com`, 2021-10-22,
  https://lore.kernel.org/all/CAHk-%3Dwg2LQtWC3e4Z4EGQzEmsLjmk6jm67Ga6UMLY1MH6iDcNQ%40mail.gmail.com/)
- "I'd much rather see one time source at a time being converted, and enabled then and there, so that when people
  report problems and do a bisection, if it was HPET that broke, you get the commit that changed HPET."
  (`alpine.LFD.0.999.0707111510030.20061@woody.linux-foundation.org`, 2007-07-11,
  https://lore.kernel.org/all/alpine.LFD.0.999.0707111510030.20061%40woody.linux-foundation.org/)
- Exceptions: "I still don't like some of the VM changes, but integrating Andrea's VM changes results in (a) better
  performance and (b) much cleaner inactive page handling in particular."
  (`Pine.LNX.4.33.0109171608310.1108-100000@penguin.transmeta.com`, 2001-09-18,
  https://lore.kernel.org/all/Pine.LNX.4.33.0109171608310.1108-100000%40penguin.transmeta.com/) and "But yes,
  numbers talk, and I get the feeling that we just need to try it."
  (`CAHk-=whAOM+xQm9vMe33qf8X1LX2QQZ7RBgKe_KH2C3LB=6Jdw@mail.gmail.com`, 2022-01-11,
  https://lore.kernel.org/all/CAHk-%3DwhAOM%2BxQm9vMe33qf8X1LX2QQZ7RBgKe_KH2C3LB%3D6Jdw%40mail.gmail.com/)

**How well supported.** About 20 messages, 2001 to 2025 (2001 evolution thread x2, 2001 VM, 2007 timers, 2007
Libification, 2007 CFS "series of independent patches", 2008 linux-next, 2021 fscache, 2022 MGLRU, 2025 LTTng
"merge it incrementally"). Consistent for 25 years.

---

### 3. Reality beats the spec; code to what implementations actually do [kernel, general; tool for fsync]

**Principle.** A specification or standard is an approximation, useful for discussion. When it disagrees with what
real hardware, real programs or real users do, the spec loses. Do not organise code around a spec's abstractions,
and do not win an argument by quoting it. Design for how code is actually written, not for how a standard says it
should be.

**What triggers it in a review.**
- "Per RFC/spec section X this is the client's fault" used to reject a fix for a misbehaving real peer.
- A class hierarchy or module layout copied from the layers of a spec (the OSI-model smell).
- A strict validator that rejects inputs real producers emit. A guarantee that serialises everything because a
  standard technically requires it although no user depends on it.
- An API whose correct use needs a careful dance (`fsync`, temp file, rename) that 99% of callers will not do.

**His reasoning.** He compares it to science: a theory with known holes is at best an approximation (2005).
Hardware is tested against one real implementation (Windows), not against the spec, so the only behaviour that
works is the behaviour that implementation exercises (2005). Spec layers are "a way to _talk_ about things, not to
implement them". Most code is "badly written" by the standard's lights, so systems should make that code "just
work" (2009). His latest position (2026) is that kernel API specs should be generated from reality and used only
for automated checking.

**How serious.** He dismisses spec-based arguments outright, keeps hardware features off by default, and rejects
designs that force callers into spec purity.

**Limits and exceptions.**
- Specs that were written from working code (the C preprocessor) translate back into code fine (2005).
- "read the documentation, but don't actually assume it's complete": documentation is still read (2006).
- He says the problem is worse in the kernel: "user-level programming is so much simpler than kernel programming"
  because you can "think" about your algorithms (2006). That weakens the transfer for pure algorithmic code.
- He does follow standards when users depend on them: the UTF-8 argument was "practical", not anti-standard
  (2004).

**Outside the kernel.** This transfers strongly: Postel-style tolerance toward real peers, browser and HTTP
quirks, vendor APIs that disagree with their docs, file formats as other tools actually write them. It also gives
a reviewer a rule: "the spec says" is not a reason to break a working integration.

**Evidence.**
- "When reality and specs clash, the spec has zero meaning. Zilch. Nada. None." and "And that's important. Specs
  are a basis for _talking_about_ things. But they are _not_ a basis for implementing software."
  (`Pine.LNX.4.58.0509291247040.3308@g5.osdl.org`, 2005-09-29,
  https://lore.kernel.org/all/Pine.LNX.4.58.0509291247040.3308%40g5.osdl.org/)
- "A lot of people seem to think that spec abstractions should be translated into code abstraction. Not so. It
  often makes no sense to do so at all." and the exception: "There are exceptions. I suspect that pretty much all
  of them are specs that _used_ to be code (ie they are documentation of real implementations)."
  (`Pine.LNX.4.64.0510031531170.31407@g5.osdl.org`, 2005-10-03,
  https://lore.kernel.org/all/Pine.LNX.4.64.0510031531170.31407%40g5.osdl.org/)
- "This should be the #1 rule for every kernel programmer: read the documentation, but don't actually assume it's
  complete, or that it is always true." and the limit: "One of the big reasons user-level programming is so much
  simpler than kernel programming is that you can basically "think" about your algorithms."
  (`Pine.LNX.4.64.0611150739110.3349@woody.osdl.org`, 2006-11-15,
  https://lore.kernel.org/all/Pine.LNX.4.64.0611150739110.3349%40woody.osdl.org/)
- "So rather than come up with new barriers that nobody will use, filesystem people should aim to make "badly
  written" code "just work" unless people are really really unlucky. Because like it or not, that's what 99% of all
  code is." and "Theory and practice sometimes clash. And when that happens, theory loses. Every single time."
  (said "with my 'git' hat on": `alpine.LFD.2.00.0903252017100.3032@localhost.localdomain`, 2009-03-26,
  https://lore.kernel.org/all/alpine.LFD.2.00.0903252017100.3032%40localhost.localdomain/)
- "Instead, it's a "everybody pays the price for giving stupid things a pointless semantic guarantee"."
  (on POSIX write atomicity: `CAHk-=wjnW96+oP0zhEd1zjPNqOHvrddKkwp0+CuS5HpZavfmMQ@mail.gmail.com`, 2024-02-26,
  https://lore.kernel.org/all/CAHk-%3DwjnW96%2BoP0zhEd1zjPNqOHvrddKkwp0%2BCuS5HpZavfmMQ%40mail.gmail.com/)
- "We are *NEVER* going to change the API _to_ some spec. The spec needs to match reality, we're not changing
  reality to match a spec." (`CAHk-=wg-5cWvYgmnE2WH4yys8tB5AwwRQU6kW0r5VoRYBLT7TA@mail.gmail.com`, 2026-11-16,
  https://lore.kernel.org/all/CAHk-%3Dwg-5cWvYgmnE2WH4yys8tB5AwwRQU6kW0r5VoRYBLT7TA%40mail.gmail.com/)

**How well supported.** About 14 messages, 2004 to 2026 (SAS thread x4 2005, MSI 2006 x2, fsync 2009, POSIX 2024,
API spec 2026, UTF-8 2004 x2, gcc/memory model 2007 and 2012 seen in search). Unchanged over 20 years.

---

### 4. Pragmatism over purity: judge an architecture by its whole-system cost, not its elegance [general; Usenet comp.arch and LKML]

**Principle.** Pick the design that works and performs for the whole system, even when it is less elegant on
paper. Splitting a system into separately communicating parts makes each part simpler and the whole harder.
Layering pays only when it does not force information that would otherwise be at hand through cumbersome channels.
"everything is a trade-off" except not breaking users.

**What triggers it in a review.**
- A proposal to split a component into services, processes or plugins "for modularity", where the parts share
  state and must stay coherent (caches, locks, invariants).
- Arguments of the form "each piece becomes simple" that never price the interaction: retries, partial failure,
  versioning, cross-boundary debugging.
- A rewrite justified by one perceived flaw ("an agenda") that ignores what the old design solved implicitly.
- A rule applied with "hardline religious fervor" that ties together unrelated behaviours (the printk/PREEMPT_RT case).

**His reasoning.** The complexity is in the "interaction between the parts"; microkernel arguments compare one
subsystem with the whole OS (1999, 2003). You lose the ability to debug the parts together, and you create
data-coherency problems the original design never had (2003). Layering is "often good" but not always (2003).
Redesigning around one fix produces "a whole new of issues - usually things that were solved by the original
approach" (2002).

**How serious.** In the kernel he rejects such restructurings and the people pushing them. With printk in 2022 he
refused the pull and warned about future pulls from that tree.

**Limits and exceptions.**
- In 1992 he conceded that microkernels are "nicer" and that Linux "looses" on theory and aesthetics; he chose
  availability and simplicity.
- He accepts user-space policy shims when the kernel keeps the mechanism and the worries do not materialise
  (FUSE, and sched_ext in 2024).
- "I'm pragmatic: I'd happily be proven wrong by somebody actually showing something" (2003). Evidence can move
  him.

**Outside the kernel.** This transfers strongly to microservices against monoliths, plugin architectures, and
splitting a library into processes. The 2003 rule ("start communicating between independent modules no sooner
than you absolutely HAVE to") is about as direct a service-boundary rule as he has written. The
protection-domain and performance criteria for a boundary are in principle 7.

**Evidence.**
- "True, linux is monolithic, and I agree that microkernels are nicer." and "From a theoretical (and aesthetical)
  standpoint linux looses." (`news:1992Jan29.231426.20469@klaava.Helsinki.FI`, 1992-01-29,
  https://github.com/oldlinux-web/oldlinux-files/blob/master/mail-archive/linux-activists/Linus%20in%20Minix-group.txt)
- "Bzzt! Wrong! The above argument completely ignores the fundamental issue of interaction between the parts, which
  is where all the complexity comes in in the first place." (`https://yarchive.net/comp/microkernels.html#3`,
  1999-02-28, https://yarchive.net/comp/microkernels.html#3)
- "I claim that you want to start communicating between independent modules no sooner than you absolutely HAVE
  to, and that you should avoid splitting things up until you really need to, because that communication
  complexity often swamps the complexity of the actual pieces involved in it."
  (`news:1057372217.336719@palladium.transmeta.com`, 2003-07-04, https://yarchive.net/comp/microkernels.html#8)
- "No. I'm arguing for the side that thinks that layering is often good, but that does not mean that ALL layering
  is good." and "Layering is often bad - if it means that you have to use cumbersome communication channels to
  forward information that otherwise would just have been available to you naturally."
  (`news:1057474131.367543@palladium.transmeta.com`, 2003-07-05, https://yarchive.net/comp/microkernels.html#12)
- "They have "an agenda", and that's the _worst_ thing you can have when designing software."
  (`aso4kq$2ka$1@penguin.transmeta.com`, 2002-12-05, https://lore.kernel.org/all/aso4kq%242ka%241%40penguin.transmeta.com/)
- "There is exactly one thing you should hold sacred: don't break people's setups. All the rest is just
  engineering, and a HUGE part of "engineering" is to realize that everything is a trade-off."
  (`CAHk-=wie+VC-R5=Hm=Vrg5PLrJxb1XiV67Efx-9Cr1fBKCWHTQ@mail.gmail.com`, 2022-08-03,
  https://lore.kernel.org/all/CAHk-%3Dwie%2BVC-R5%3DHm%3DVrg5PLrJxb1XiV67Efx-9Cr1fBKCWHTQ%40mail.gmail.com/)
- Limit: "It mostly just was (and is) a shim-layer that asks user space for policy, while still using the kernel
  infrastructure for most real work. Did those worries actually materialize? No. No they did not."
  (`CAHk-=wiRgsFsrnTR8XShrS_-aYS--4DSrRPmaWtYJ55-fmjznA@mail.gmail.com`, 2024-06-21,
  https://lore.kernel.org/all/CAHk-%3DwiRgsFsrnTR8XShrS_-aYS--4DSrRPmaWtYJ55-fmjznA%40mail.gmail.com/)

**How well supported.** About 14 messages, 1992 to 2024 (Minix 1992, yarchive 1998 to 1999 x3, comp.arch 2003 x4,
2002, printk 2022, sched_ext 2024, UTF-8 2004).

---

### 5. No infrastructure without users; code with one user stays with that user [kernel; overdesign rule general]

**Principle.** Do not add generic infrastructure, frameworks, extension points or syscalls until real users need
them. If a helper has one caller, it belongs in that caller, not in a shared header. Do not over-design ("expose
anything"); build the simple, specific thing.

**What triggers it in a review.**
- A new `utils/`, `common/` or `core/` module, a plugin registry or a generic "provider" interface with one
  implementation.
- An API that takes an open-ended bag ("attributes", "options", "metadata" with type tags) because the author does
  not yet know what callers need.
- An "example" or demo user added to justify infrastructure.
- A tricky or unsafe helper exported for general use when only one special caller can use it safely.

```python
# raises it
class StorageBackend(ABC): ...          # one implementation, no second in sight
class PluginRegistry: ...               # registers exactly that one
def get_info(kind: str, **kwargs) -> dict:  # "expose anything"
# what he asks for: the concrete function in the module that uses it
```

**His reasoning.** Features cannot be removed once in ("Nobody takes out features"; see principle 11).
Infrastructure without users is "TOTALLY MISDESIGNED FROM THE VERY START" because nothing shaped it (utrace,
2010). An open-ended interface is "a huge sign of over-design" (fsinfo, 2020). A one-user helper in a generic
header invites misuse by people who do not know its special conditions (2018). New capabilities are adopted
through "a nice gradual ramp-up", which means a portable user-space library first (2004).

**How serious.** He refuses merges (UIO driver, utrace, fsinfo, hazard pointers). The usual instruction is "just
copy it" or "roll your own version" inside the user.

**Limits and exceptions.**
- Notification queues were merged "even if it wasn't clear how many or who would use them", because they solved a
  fundamental problem (no more polling `/proc/mounts`) (2020).
- In 2004 he allowed a filesystem-first approach "as an academic exercise and as a learnign experience and
  prototyping work", if it is treated as a prototype.
- An abstraction with several real users is welcome (the VFS, USB in user space in 2006).

**Outside the kernel.** This transfers directly: YAGNI, the rule of three, no premature `interface`/`ABC`. Keep a
helper next to its only caller, keep shared libraries small, and refuse "metadata" or `**kwargs` grab-bag APIs.

**Evidence.**
- "No features just for features sake." and "I'm really not convinced about the user-mode thing unless somebody
  can show me a good reason for it. Not just some "wouldn't it be nice" kind of thing."
  (`Pine.LNX.4.64.0612131252300.5718@woody.osdl.org`, 2006-12-13,
  https://lore.kernel.org/all/Pine.LNX.4.64.0612131252300.5718%40woody.osdl.org/)
- "So give me a populist argument that makes sense for tons of actual users, not some f*cking "here's a cool
  infrastructure that developers can do random crazy out-of-tree crap with"."
  (`alpine.LFD.2.00.1001250930320.3574@localhost.localdomain`, 2010-01-25,
  https://lore.kernel.org/all/alpine.LFD.2.00.1001250930320.3574%40localhost.localdomain/)
- "We don't just merge random infrastructure without a use-case and an argument for it."
  (`CAHk-=wi76E2xxvOaZtgN2FK9YKmbK1ru_1atL8eBCs34z7UigA@mail.gmail.com`, 2024-09-18,
  https://lore.kernel.org/all/CAHk-%3Dwi76E2xxvOaZtgN2FK9YKmbK1ru_1atL8eBCs34z7UigA%40mail.gmail.com/)
- "So  honestly, with only one user, I think the serialization code should be solidly in that one user, not in
  kernel/smp.c." (`CAHk-=wj5rEZFvaLgs-ZtsCX9++mFNYKox21SBfF8vrSQG4WbPA@mail.gmail.com`, 2024-03-13,
  https://lore.kernel.org/all/CAHk-%3Dwj5rEZFvaLgs-ZtsCX9%2B%2BmFNYKox21SBfF8vrSQG4WbPA%40mail.gmail.com/) and "I
  don't want any crazy and unsafe stuff in the generic header file that absolutely *nobody* should ever use."
  (`CA+55aFx+4D5bBYSKb5jKjJ8SP=osGB=PCf8vW3RZH+R5fp5jgQ@mail.gmail.com`, 2018-05-22,
  https://lore.kernel.org/all/CA%2B55aFx%2B4D5bBYSKb5jKjJ8SP%3DosGB%3DPCf8vW3RZH%2BR5fp5jgQ%40mail.gmail.com/)
- "Overdesigning is a disease. It's fundamentally wrong." (`AANLkTikoD1OPjVcyvAAJ0QO6dGJxv40Np6LgRQ7X4tMM@mail.gmail.com`,
  2010-07-06, https://lore.kernel.org/all/AANLkTikoD1OPjVcyvAAJ0QO6dGJxv40Np6LgRQ7X4tMM%40mail.gmail.com/) and
  "It's a huge sign of over-design and "I don't know what the hell I want to expose, so I'll make this generic
  thing that can expose anything, and then I start adding random fields"."
  (`CAHk-=wig0ZqWxgWtD9F1xZzE7jEmgLmXRWABhss0+er3ZRtb9g@mail.gmail.com`, 2020-08-17,
  https://lore.kernel.org/all/CAHk-%3Dwig0ZqWxgWtD9F1xZzE7jEmgLmXRWABhss0%2Ber3ZRtb9g%40mail.gmail.com/)
- "The way you get people to take advantage of something is to have a nice gradual ramp-up, not a sudden new
  feature that they can't realistically use." (`Pine.LNX.4.58.0409020030220.2295@ppc970.osdl.org`, 2004-09-02,
  https://lore.kernel.org/all/Pine.LNX.4.58.0409020030220.2295%40ppc970.osdl.org/)
- Exception: "Plus the notification queues had other uses, even if it wasn't clear how many or who would use
  them." (same 2020-08-17 message)

**How well supported.** About 20 messages, 2002 to 2026 (UIO 2006, utrace 2010, kvmtool 2013, rculist 2018,
fsinfo 2020 x3, statfs 2010, smp 2024, hazard pointers 2024, btree 2023, klibc 2003, reiser4 2004, LSM 2007, page
replacement framework 2006, process_mrelease 2026). One of the best-supported principles.

---

### 6. An abstraction must carry the information its users need and must not hide what matters [kernel, tool/app for git and C++]

**Principle.** A layer that cannot pass down what the layers above know, or that hides costs and constraints the
caller must understand, is a bad layer whatever its tidiness. Abstraction has a price: indirection, lost
information, and lock-in when it turns out to be inefficient.

**What triggers it in a review.**
- A wrapper that drops a parameter the lower layer needs (priority, deadline, context, allocation constraints) or
  that assumes the least capable backend.
- A "convenient" API that hides context-sensitive rules from the caller (blocking in async code, allocation under
  a lock, a transaction boundary).
- A driver/registration layer or a vtable around something that is one cheap operation.
- Adoption of a heavy library or ORM for a core path where "there *is* no abstraction" is the point.

**His reasoning.** cpufreq's layer "_thinks_ that all hardware is stupid" because it can only express a hard
frequency, not a policy (2002). A heavy layer around a single instruction defeats its purpose (2011). In C++ code
the abstraction you adopt early becomes impossible to fix later because "all your code depends on" it (2007, git
list). Making the kernel allocator look like user-space `malloc` is "the wrong kind of easy" because the caller
must know about locking context (2026). A general database is slower than a special-purpose structure because it
"they have to solve a much more generic issue" (2005).

**How serious.** He asks for a rework of the interface. For hidden-context conveniences he says no flatly.

**Limits and exceptions.**
- A thin type-safe convenience that only removes boilerplate for "the most common case" is fine
  (`kzmalloc_obj()`, same 2026 message).
- "If you design your data structures and abstractions right" a special-purpose abstraction is good: git "did my
  own special-case abstraction" (2005).
- He wants abstraction layers to exist where hardware varies ("Think of this as a driver abstraction layer",
  2002). The objection is to a layer that is too thin in information, not to layering.

**Outside the kernel.** This transfers strongly: leaky abstractions, ORMs hiding N+1 queries, async wrappers
hiding blocking calls, interface types that erase capabilities. Ask "what does the caller need to know that this
hides?" and "what does the backend need that this cannot express?"

**Evidence.**
- "If you want to build infrastructure for upper layers, then that infrastructure has to be able to pass down
  sufficient information from those upper layers." and "The current abstraction layer _thinks_ that all hardware is
  stupid, and is thus not actually usable with smart hardware. See?"
  (`Pine.LNX.4.33.0208281400330.16824-100000@penguin.transmeta.com`, 2002-08-28,
  https://lore.kernel.org/all/Pine.LNX.4.33.0208281400330.16824-100000%40penguin.transmeta.com/)
- "Exactly. I do *not* want a abstraction layer just because somebody wants to use it."
  (`CA+55aFz1pnqdrXCEQThZc3S2r6kQPiDtOKacJQtHpPbjpXkmqg@mail.gmail.com`, 2013-02-11,
  https://lore.kernel.org/all/CA%2B55aFz1pnqdrXCEQThZc3S2r6kQPiDtOKacJQtHpPbjpXkmqg%40mail.gmail.com/)
- "But don't make it something heavy-weight, when the whole *point* of having the hardware is to make it
  light-weight." (`CA+55aFwMGwVsD1Gexahio2pWd0PpaHAbvFroB3w0=JOQf1zQ_A@mail.gmail.com`, 2011-07-30,
  https://lore.kernel.org/all/CA%2B55aFwMGwVsD1Gexahio2pWd0PpaHAbvFroB3w0%3DJOQf1zQ_A%40mail.gmail.com/)
- "inefficient abstracted programming models where two years down the road you notice that some abstraction wasn't
  very efficient, but now all your code depends on all the nice object models around it, and you cannot fix it
  without rewriting your app." (git list: `alpine.LFD.0.999.0709061839510.5626@evo.linux-foundation.org`,
  2007-09-06, https://lore.kernel.org/all/alpine.LFD.0.999.0709061839510.5626%40evo.linux-foundation.org/)
- "Yes, it might be "easier to use". But that's the wrong kind of easy."
  (`CAHk-=wiSmgwwLKCqJwGS-dVHnSLU8W+7q1UQq-G9=TBGGZbuhQ@mail.gmail.com`, 2026-07-09,
  https://lore.kernel.org/all/CAHk-%3DwiSmgwwLKCqJwGS-dVHnSLU8W%2B7q1UQq-G9%3DTBGGZbuhQ%40mail.gmail.com/)
- "Databases aren't magical. Quite the reverse. They easily end up being _slower_ than doing it by hand, simply
  because they have to solve a much more generic issue." (`Pine.LNX.4.58.0504081047200.28951@ppc970.osdl.org`,
  2005-04-08, https://lore.kernel.org/all/Pine.LNX.4.58.0504081047200.28951%40ppc970.osdl.org/)

**How well supported.** About 12 messages, 2002 to 2026 (cpufreq 2002, kvmtool 2013, arch random 2011, C++ 2007
x3, malloc 2026, database 2005, MSI 2006).

---

### 7. Put policy in the layer that has the knowledge; the kernel provides mechanism [kernel; the syscall/library criteria are general]

**Principle.** Decisions about what to do (naming, encoding, when to suspend, what is "allowed") belong in the
layer that has the information, usually user space or the specific subsystem. The lower or core layer provides
the mechanism and reports facts. When a component needs something from another, it should state the requirement
("I need low DMA latency") and let the layer that knows decide how to meet it, rather than reach in and toggle the
other layer's behaviour.

**What triggers it in a review.**
- Core code hard-coding a decision that differs by deployment or user (naming schemes, character-set enforcement,
  retry policy, UI behaviour) where it should expose data and let the caller decide.
- One module disabling another's feature ("turn off frequency scaling while USB is busy") instead of declaring a
  constraint.
- A generic layer doing work only one bus or driver needs (async ordering in the device core rather than the USB
  layer).
- New workaround infrastructure added somewhere else instead of fixing the component that causes the problem.

**His reasoning.** The kernel often knows less about a device than user space does, and "naming of a device is
about pretty much nothing _but_ policy" (2004). Enforcing UTF-8 in the kernel "_assumes_" everyone cares about
complex character sets, "That's what "making policy" is all about" (2004). A system call is justified by exactly
two things: a protection domain and performance. Everything else is a library (2003). Only the cpufreq layer knows
which CPUs have slow relocks (2007).

**How serious.** He rejects the change and asks for the decision to move ("I really don't want to push things any
further than absolutely necessary").

**Limits and exceptions.**
- Things that need a protection domain cannot move to a library, however much "policy" they contain: `namei` and
  TCP stay in the kernel (2003).
- He wants stable ordering in the core for debuggability, which is a deliberate core policy (2009).
- He moved suspend X/console handling into ordinary device phases so that X would not need "special cases"
  (2006). The aim is to remove policy from special paths, not to push everything outward.

**Outside the kernel.** This transfers well: libraries should not decide UX, retry or timeout policy for their
callers; services should expose data and let clients decide; components should declare needs (SLOs,
constraints) instead of reaching into each other. The 2003 protection-domain-plus-performance test is a usable
rule for when something must be a server-side or privileged operation and when it can be client library code.

**Evidence.**
- "An inactivity timer or low battery notification will just notify the proper deamon, and the policy on what to
  do should be in user space." (`Pine.LNX.4.33.0110240953010.8278-100000@penguin.transmeta.com`, 2001-10-24,
  https://lore.kernel.org/all/Pine.LNX.4.33.0110240953010.8278-100000%40penguin.transmeta.com/)
- "In particular, the kernel should never have policy encoded in it, and naming of a device is about pretty much
  nothing _but_ policy." (`Pine.LNX.4.58.0401051224480.2153@home.osdl.org`, 2004-01-05,
  https://lore.kernel.org/all/Pine.LNX.4.58.0401051224480.2153%40home.osdl.org/)
- "The kernel should not assume that everybody cares about complex character sets."
  (`Pine.LNX.4.58.0402161205120.30742@home.osdl.org`, 2004-02-16,
  https://lore.kernel.org/all/Pine.LNX.4.58.0402161205120.30742%40home.osdl.org/)
- "That's partly why I realy did suggest that we do the async stuff purely in the USB layer, rather than try to put
  it deeper in the device layer." (`alpine.LFD.2.00.0912090728200.3560@localhost.localdomain`, 2009-12-09,
  https://lore.kernel.org/all/alpine.LFD.2.00.0912090728200.3560%40localhost.localdomain/)
- "Just disabling things blindly on cpufreq events, when what it actually wants to do is say "I need low DMA
  latency", and then the cpu-freq layer (which can know about these things) may decide internally"
  (`alpine.LFD.0.999.0708202201580.30176@woody.linux-foundation.org`, 2007-08-21,
  https://lore.kernel.org/all/alpine.LFD.0.999.0708202201580.30176%40woody.linux-foundation.org/)
- "These two (and _only_ these two - if you ignore binary compatibility issues that may force other decisions on
  you) are what determine whether it is a "true" system call or a library."
  (`news:1057474131.367543@palladium.transmeta.com`, 2003-07-05, https://yarchive.net/comp/microkernels.html#12)
- ".. basically, what I'm arguing for is really to try to fix the underlying *reason* for problems, not add new code
  and new infrastructure elsewhere just because /proc/pid/smap and friends are being difficult."
  (`CAHk-=whMQsyjB6DOyWB73jPR4wrtcc++kZy4=hGQiRE+GxKh=A@mail.gmail.com`, 2026-05-22,
  https://lore.kernel.org/all/CAHk-%3DwhMQsyjB6DOyWB73jPR4wrtcc%2B%2BkZy4%3DhGQiRE%2BGxKh%3DA%40mail.gmail.com/)

**How well supported.** About 16 messages, 2000 to 2026 (OOM 2000, driver model 2001, udev 2004, UTF-8 2004 x3,
cpufreq/USB 2007, async 2009 x3, PM infrastructure 2009, comp.arch 2003, kdbus 2015, sched_ext 2024,
process_mrelease 2026).

---

### 8. Core code must not bend for a rare case; the rare case does the extra work [kernel; the principle transfers]

**Principle.** Shared paths are tuned and kept simple for the overwhelming majority. A caller with an unusual need
(huge requests, hot-pluggable memory, a debug helper, one odd architecture) handles the extra work itself or opts
in through configuration. It does not get a branch, a hook or a cost in the code everyone runs.

**What triggers it in a review.**
- `if (customer == X)` or `if (device->quirk_foo)` in a hot shared path. Hooks in core code for one plugin.
- Every request paying for a check or lock that only an edge feature needs.
- A global header or include added so that one developer's debugging convenience works everywhere.
- A "general case" design for a configuration almost nobody runs.

**His reasoning.** "the first rule of engineering is to work out the balances": if 99.99% will never care and the
code is fragile, the 0.01% configure things themselves (2005). Merging is cheap and splitting is not, so callers
with big I/O must build requests up rather than make every driver split them (2002). Everyone pays for a guarantee
only "stupid things" rely on (2024, principle 3).

**How serious.** He refuses or reverts ("we say NO, HELL NO!!"), and the trace_printk case (2026) was refused
outright.

**Limits and exceptions.**
- He will take "an admittedly ugly hack", a one-line special case, over "some complex infrastructure" when the
  special case is small and documented (2009). The rule is against cost and complexity in the common path, not
  against every special case.
- Special-case glue for an odd user (autofs) can become normal core infrastructure once it has proved itself over
  years (2024 sched_ext message).

**Outside the kernel.** This transfers directly: feature flags for enterprise tenants inside the request hot path,
middleware every request passes through for one endpoint, per-customer branches in shared libraries. Push the cost
to the caller that needs it.

**Evidence.**
- "You have to realize that the first rule of engineering is to work out the balances. The undeniable fact is, that
  99.99% of all users will never care one whit, and memory management is complex and fragile." and "We simply DO
  NOT CARE about some theoretical "general case", because the general case is (a) insane and (b) impossible to
  cater to without excessive complexity." (`Pine.LNX.4.64.0511030955110.27915@g5.osdl.org`, 2005-11-03,
  https://lore.kernel.org/all/Pine.LNX.4.64.0511030955110.27915%40g5.osdl.org/)
- "Another way of saying it: if you have 4MB worth of IO, it's YOUR resposibility to do the work to make it fit the
  controller. It is off the default case, and _you_ do a bit of extra work instead of asking everybody else to do
  your heavy lifting for you." (`a41kvr$836$1@penguin.transmeta.com`, 2002-02-08,
  https://lore.kernel.org/all/a41kvr%24836%241%40penguin.transmeta.com/)
- "And people who add debugging printk's can add a header file to their own hackery, rather than hurt everybody
  else." (`CAHk-=wi-3VeFyitR_ut6ERbHO9KEWYtRG4ghSv8_2nVr-W=3LA@mail.gmail.com`, 2026-06-19,
  https://lore.kernel.org/all/CAHk-%3Dwi-3VeFyitR_ut6ERbHO9KEWYtRG4ghSv8_2nVr-W%3D3LA%40mail.gmail.com/)
- Limit: "So I suggested an admittedly ugly hack to take care of it - rather than some complex infrastructure."
  (`alpine.LFD.2.00.0912150722310.14385@localhost.localdomain`, 2009-12-15,
  https://lore.kernel.org/all/alpine.LFD.2.00.0912150722310.14385%40localhost.localdomain/)

**How well supported.** About 12 messages, 2002 to 2026 (bio 2002, memory hotplug 2005, async 2009 x2, rculist
2018, smp 2024, POSIX 2024, trace_printk 2026, cpufreq 2007). Overlaps principles 5 and 7.

---

### 9. Design interfaces around the common case, and make the correct choice the explicit one [kernel; epoll and allocator rules general]

**Principle.** Make the common case cheap and simple; complexity is acceptable only off that path and only if
there is a cheap test for which path you are on. Do not make an interface "nice" in a way that costs everyone. Do
not split a required step into a separate call that people will forget. Expose as few internal states as
possible. Do not design an interface before you know enough.

**What triggers it in a review.**
- An API whose default is expensive (level-triggered, always-copy, always-validate) when a cheap default would
  serve most callers.
- A required safety step expressed as a second function the caller must remember (`enable()` then
  `enable_safe_mode()`).
- Public enums or lifecycle hooks exposing every internal state, so that callers start depending on the ordering.
- A cache that stores positives only, when caching "nothing special here" would cover 99% of lookups.

```c
/* raises it: the safe behaviour depends on remembering a second call */
dev_enable_msi(dev);
dev_disable_intx(dev);      /* forgotten in half the drivers */
/* what he proposed: the choice is part of the one call */
dev_enable_msi(dev, MSI_FLAG_HAS_INTX_DISABLE);
```

**His reasoning.** `poll()` is "piggy" "because it tries to be "nice" to the programmer"; edge-triggered events
let the rare caller do the extra work (2000). The biggest win of the ACL cache was the negative entry, and
"complexity could be ok. As long as the common case isn't complex" (2013). Splitting a call into two "is just a
recipe for disaster, since somebody will forget" (2006). Too many exposed hotplug states let random drivers "be
clever" (2013). For device-to-device transfers, "know when you don't know enough" (2001).

**How serious.** He asks for interface changes before merge, and sometimes writes the alternative patch himself.

**Limits and exceptions.**
- He accepts complex models as long as the simple case is fast and detectable (2013).
- Rarely needed internal states can exist and be documented, provided they are not exposed (2013).

**Outside the kernel.** This transfers directly to API design: defaults, required parameters instead of
remembered follow-up calls, minimal public surface, negative caching, and not committing to an interface for
hardware or partners you do not have yet.

**Evidence.**
- "One of the reasons why poll() is such a piggy interface is exactly because it tries to be "nice" to the
  programmer." and "Advantage: performance again. The common case doesn't take the performance hit."
  (`Pine.LNX.4.10.10010260936330.2460-100000@penguin.transmeta.com`, 2000-10-26,
  https://lore.kernel.org/all/Pine.LNX.4.10.10010260936330.2460-100000%40penguin.transmeta.com/)
- "So complexity could be ok. As long as the common case isn't complex, and as long as there's a simple way to
  check that." (`CA+55aFxueg-wBRdUw=S=TOAnHy3BorGYMzffiDkjU90BCTzcig@mail.gmail.com`, 2013-05-26,
  https://lore.kernel.org/all/CA%2B55aFxueg-wBRdUw%3DS%3DTOAnHy3BorGYMzffiDkjU90BCTzcig%40mail.gmail.com/)
- "The answer to the "can" question is: merging can be fast, splitting fundamentally cannot."
  (`a41kvr$836$1@penguin.transmeta.com`, 2002-02-08, https://lore.kernel.org/all/a41kvr%24836%241%40penguin.transmeta.com/)
- "Making them call another function is just a recipe for disaster, since somebody will forget."
  (`Pine.LNX.4.64.0611151127560.3349@woody.osdl.org`, 2006-11-15,
  https://lore.kernel.org/all/Pine.LNX.4.64.0611151127560.3349%40woody.osdl.org/)
- "So 11 states (although some of those seem to have lots of substates, so there may be many more) is too many to
  *expose*. It's not necessarily too many to "have and document", if you see the difference."
  (`CA+55aFypNfzA1HZMmAiyFo48MhUTr+gt+1uvM7SHFzXh60-KQQ@mail.gmail.com`, 2013-01-31,
  https://lore.kernel.org/all/CA%2B55aFypNfzA1HZMmAiyFo48MhUTr%2Bgt%2B1uvM7SHFzXh60-KQQ%40mail.gmail.com/)
- "An important point in interface design is to know when you don't know enough."
  (`Pine.LNX.4.10.10101181120070.18387-100000@penguin.transmeta.com`, 2001-01-18,
  https://lore.kernel.org/all/Pine.LNX.4.10.10101181120070.18387-100000%40penguin.transmeta.com/)

**How well supported.** About 12 messages, 2000 to 2026 (epoll 2000, sendfile 2001 x2, bio 2002, MSI 2006 x2, VFS
lookup 2013, hotplug 2013, malloc 2026, kdbus 2015).

---

### 10. A working, tested patch and real numbers beat any proposal [kernel, general]

**Principle.** Arguments are settled by code that works and by measurements on real workloads. A plan, a promise
to unify later, or "merge it and it will improve" is not a reason to merge. A reviewer may (and he often does)
answer with a small concrete patch instead of more discussion.

**What triggers it in a review.**
- "We'll clean this up after it's merged" or "once it's in, others will adopt it".
- Long design debate with no prototype, or a claimed performance improvement without numbers.
- A disagreement a 20-line patch would settle, which the reviewer can write.

**His reasoning.** Code in tree is permanent, so it must prove itself first: "we don't put patches in in the hope
that they will prove themselves later" (2002). Promises to unify have a track record of not happening ("I don't
believe in fairy tales", 2025). He repeatedly sketches the patch himself (HZ in 2005, firmware loading in 2012,
the async one-liner in 2009, statfs in 2010).

**How serious.** No merge until the code or the numbers exist.

**Limits and exceptions.**
- Code is necessary but not sufficient. In CFS against SD (2007) the maintainer's responsiveness to problem
  reports mattered "much much MUCH more" than the code. Who will maintain it counts (principle 13).
- "talk is cheap, and code rules" was also used about who does the work deciding a licence question (klibc,
  2003). It is a social rule as much as a technical one.

**Outside the kernel.** This transfers directly: ask for a spike or prototype, demand benchmarks on representative
workloads, and decline "merge now, generalise later" for anything public. A review that includes a concrete diff
is in keeping with his practice.

**Evidence.**
- "Nobody takes out features, they are stuck once they get in. Which is exactly why my job is to say "no", and why
  there is no "accepted unless proven bad"." and "The basic issue is that we don't put patches in in the hope that
  they will prove themselves later." (`Pine.LNX.4.44.0210312233190.5595-100000@home.transmeta.com`, 2002-11-01,
  https://lore.kernel.org/all/Pine.LNX.4.44.0210312233190.5595-100000%40home.transmeta.com/)
- "In other words, talk is cheap, and code rules." (`Pine.LNX.4.44.0303071459260.1309-100000@home.transmeta.com`,
  2003-03-07, https://lore.kernel.org/all/Pine.LNX.4.44.0303071459260.1309-100000%40home.transmeta.com/)
- "If people can unify this and merge it incrementally, that's one thing. Until then, you're just making stuff up.
  "Show me the code", in other words." (`CAHk-=wgZ=Ssx4qoeuaHet1vx+8M36j0a3q2aw5ePapWm=KnSfQ@mail.gmail.com`,
  2025-07-14, https://lore.kernel.org/all/CAHk-%3DwgZ%3DSsx4qoeuaHet1vx%2B8M36j0a3q2aw5ePapWm%3DKnSfQ%40mail.gmail.com/)
- "Really. I dare you guys. First one to send me a tested patch gets a gold star."
  (`Pine.LNX.4.58.0507141718350.19183@g5.osdl.org`, 2005-07-15,
  https://lore.kernel.org/all/Pine.LNX.4.58.0507141718350.19183%40g5.osdl.org/)
- "I'd really suggest somebody show better real-life numbers with a new algorithm _before_ we do anything like
  this." (`Pine.LNX.4.64.0603231243160.26286@g5.osdl.org`, 2006-03-23,
  https://lore.kernel.org/all/Pine.LNX.4.64.0603231243160.26286%40g5.osdl.org/)
- Limit: "And you have to realize that to me, as the top-level maintainer and one who seldom actually does big
  coding things, but just ends up making sure that people work with others, and fix the problems that crop up,
  *that* kind of behaviour is much much MUCH more important than the code itself."
  (`alpine.LFD.0.999.0707281109120.3442@woody.linux-foundation.org`, 2007-07-28,
  https://lore.kernel.org/all/alpine.LFD.0.999.0707281109120.3442%40woody.linux-foundation.org/)

**How well supported.** About 14 messages, 2002 to 2025, plus a dozen where he answers with a patch.

---

### 11. The maintainer's job is mostly to say no, but no maintainer owns who uses the code [kernel; transfers to any project owner]

**Principle.** Saying no is the default. Whether there will be users, whether there are numbers, whether it is too
experimental, and whether it is being added only because it can be, are standing questions. Customer and manager demands are not requirements. The power to
say no covers your own code, not who may build on it, and it is not a lever to extract unrelated work.

**What triggers it in a review.**
- New public API, endpoint, option or syscall-like surface with no demonstrated need.
- A feature justified by "a customer asked for it" with no general user.
- The reverse, which a reviewer should not do: blocking a change because you dislike its consumer (a new language
  binding, an integration), or making acceptance conditional on fixing unrelated pre-existing problems.

**His reasoning.** Features are permanent (principle 10), so the filter must be at the gate. Customers and
managers asking for the insane general case are like "voices in your head that tell you to shoot the pope" (2005). Against
over-reach: "as a maintainer you are in charge of your code, sure - but you are not in charge of who uses the end
result and how" (2025). Tying acceptance to unrelated fixes "really doesn't work, and has caused friction" because
the contributor will not do Y just because X was posted (2026).

**How serious.** The refusals are final. He overrides maintainers who over-reach, and in 2025 merged over the
objection.

**Limits and exceptions.** These are the two limits above, both recent and both stated as current position, plus
"I said that the threshold should be high, not that it should be impossible" (2008).

**Outside the kernel.** This transfers directly. For a review agent the 2026 point is concrete: report
pre-existing issues separately and do not make them a condition of approving this change.

**Evidence.**
- "My job is to say "too late for the merge window", or "too experimental", or "you need to show numbers" or "are
  there going to be any _users_ for this"?" (`alpine.LFD.0.999.0707281109120.3442@woody.linux-foundation.org`,
  2007-07-28, https://lore.kernel.org/all/alpine.LFD.0.999.0707281109120.3442%40woody.linux-foundation.org/)
- "Guys, a kernel developer needs to know when to say NO." and "When you hear voices in your head that tell you to
  shoot the pope, do you do what they say? Same thing goes for customers and managers."
  (`Pine.LNX.4.64.0511030955110.27915@g5.osdl.org`, 2005-11-03,
  https://lore.kernel.org/all/Pine.LNX.4.64.0511030955110.27915%40g5.osdl.org/)
- "Let's not add system calls just because we can." (`CAHk-=wiPx0UJ6Q1X=azwz32xrSeKnTJcH8enySwuuwnGKkHoPA@mail.gmail.com`,
  2020-08-12, https://lore.kernel.org/all/CAHk-%3DwiPx0UJ6Q1X%3Dazwz32xrSeKnTJcH8enySwuuwnGKkHoPA%40mail.gmail.com/)
- Limit: "So let me be very clear: if you as a maintainer feel that you control who or what can use your code, YOU
  ARE WRONG." (`CAHk-=wgLbz1Bm8QhmJ4dJGSmTuV5w_R0Gwvg5kHrYr4Ko9dUHQ@mail.gmail.com`, 2025-02-21,
  https://lore.kernel.org/all/CAHk-%3DwgLbz1Bm8QhmJ4dJGSmTuV5w_R0Gwvg5kHrYr4Ko9dUHQ%40mail.gmail.com/)
- Limit: "Developers who do some patch series for X and find that interesting - or get paid for that - are *not*
  necessarily then just going to do Y just because the maintainer notices it."
  (`CAHk-=wjCcHUr=-Ycsey0khWnn68O6D=ZN-bE+8Sq4NetXpFuPA@mail.gmail.com`, 2026-07-17,
  https://lore.kernel.org/all/CAHk-%3DwjCcHUr%3D-Ycsey0khWnn68O6D%3DZN-bE%2B8Sq4NetXpFuPA%40mail.gmail.com/)

**How well supported.** About 12 messages, 2002 to 2026.

---

### 12. Own the bug; fix first, don't argue that the other side is wrong [kernel, general]

**Principle.** When your change is bisected as the cause of a breakage, it is your bug. Fix or revert it promptly.
Do not argue that the user, the application or the compliance tool was "really" at fault. He applies the same
standard to his own mistakes.

**What triggers it in a review.** A response to a regression report that blames callers ("they were relying on
undefined behaviour"), defends the change on spec grounds, or proposes the "correct" behaviour that still breaks
the reporter. Weeks of argument on a bisected regression.

**His reasoning.** Arguing delays the fix and shows the wrong priorities: "You should have tried to fix the
problem immediately" (2009). Excuses for breakage are "just shameful. It's not how we work" (2012). Maintainers
"not willing to own up to problems" lose his trust (2012, about Kay Sievers and udev).

**How serious.** Very serious. He applies the fix himself, bypasses the maintainer, and publicly rebukes them
(2012: "I'll apply it directly and immediately myself"). His tone in these messages before 2018 is one he has
since apologised for. The substance stands; the skill should copy the substance, not the register.

**Limits and exceptions.** Owning the bug does not mean accepting a bad fix. In 2009 he argued for the "nicer fix,
that also makes more conceptual sense". This principle overlaps heavily with the regressions (never break user
space) theme, which another miner covers; it is included here only for the responsibility aspect.

**Outside the kernel.** This transfers directly: blameless but accountable incident handling, revert-first on
bisected regressions, no "works as designed" for breaking changes to consumers.

**Evidence.**
- "What I'm so unhappy about is that your whole reaction to it - from the beginning - was to blame anything but the
  patch that caused it, and that it was bisected down to." and "You should have tried to fix the problem
  immediately, without arguing against fixing the kernel. Without blaming user space. Without making idiotic
  excuses for bad kernel behavior." (`alpine.LFD.2.01.0907281158120.3186@localhost.localdomain`, 2009-07-28,
  https://lore.kernel.org/all/alpine.LFD.2.01.0907281158120.3186%40localhost.localdomain/)
- "The fact that you then try to make *excuses* for breaking user space, and blaming some external program that
  *used* to work, is just shameful." (`CA+55aFy98A+LJK4+GWMcbzaa1zsPBRo76q+ioEjbx-uaMKH6Uw@mail.gmail.com`,
  2012-12-23, https://lore.kernel.org/all/CA%2B55aFy98A%2BLJK4%2BGWMcbzaa1zsPBRo76q%2BioEjbx-uaMKH6Uw%40mail.gmail.com/)
- "Yeah, that bugzilla shows the problem with Kay as a maintainer too, not willing to own up to problems he
  caused." (`CA+55aFweE2BgGjGkxLPkmHeV=Omc4RsuU6Kc6SLZHgJPsqDpeA@mail.gmail.com`, 2012-10-03,
  https://lore.kernel.org/all/CA%2B55aFweE2BgGjGkxLPkmHeV%3DOmc4RsuU6Kc6SLZHgJPsqDpeA%40mail.gmail.com/)
- Self-applied: "I think this was only the second time I had a forced push to fix some stupidity of mine. So it's
  not exactly _common_, but it's embarrassing." (`CAHk-=wiHFbAaqS0h_D-9d1=Yc-iq96wE-hrrqOfptGNUZx-GRg@mail.gmail.com`,
  2020-10-02, https://lore.kernel.org/all/CAHk-%3DwiHFbAaqS0h_D-9d1%3DYc-iq96wE-hrrqOfptGNUZx-GRg%40mail.gmail.com/)

**How well supported.** About 9 messages read for this theme, 2009 to 2021. The regressions miner will have many
more.

---

### 13. Trust people with a track record; keep process light and make decisions reversible [kernel process, git talk, management-style]

**Principle.** Merging works through a network of trusted people, each vouching for the next hop. Trust is earned
by sustained good judgement ("good taste"), not by a title. Process should be the minimum that works; noisy
automation is worse than humans filtering. A tool is trusted only because of the people running it. Decisions
should be kept small by keeping them undoable.

**What triggers it in a review.**
- Proposals to add mandatory gates for everything (trivial fixes included).
- Automated reports (bots, linters, AI reviewers) that generate unfiltered noise for maintainers.
- Treating a role (CODEOWNERS, MAINTAINER) as proof of trust.
- Irreversible decisions (data migrations without a rollback, public API commitments) taken casually.

**His reasoning.** Humans work with "5-10 people" (2002). The Signed-off-by chain "documents that chain of trust"
because you know the next hop but not the full chain (2004). "I don't think process is appropriate for everything", and
gating trivial fixes "would just slow everybody down" (2008). Bug trackers without humans to "de-noisify" bury the
useful reports (2007). With AI review: "we'd trust the person or group who is orchestrating the tool!" (2026). From
management-style: big decisions are the ones you cannot undo.

**How serious.** This shapes who he pulls from and how fast, and what process he accepts. It is not a per-patch
rule.

**Limits and exceptions.**
- He did add process when it paid: Signed-off-by (2004), the merge window, linux-next, and an explicit wish in
  2008 for "some more process in general".
- Trust is per area: architecture maintainers are trusted "as long as they only affect their own architecture"
  (2002).
- Andrea is "absolutely stunning, but sometimes somewhat erratic", which "just means that I have to think a lot
  more about his patches" (2002). Trust is graded, not binary.

**Outside the kernel.** This transfers directly to review culture: review depth scaled to the author's record and
the blast radius, bots and AI findings filtered before they reach people, and reversibility as a design goal. For
the skill itself: be the de-noising human, not more noise.

**Evidence.**
- "Being listed as MAINTAINER doesn't mean you are automatically trusted." and "They've shown what I call "good
  taste" for a long time." (`Pine.LNX.4.33.0201290914270.7701-100000@athlon.transmeta.com`, 2002-01-29,
  https://lore.kernel.org/all/Pine.LNX.4.33.0201290914270.7701-100000%40athlon.transmeta.com/)
- "So the _path_ the patch came in through actually documents that chain of trust - we all tend to know the "next
  hop", but we do _not_ necessarily have direct knowledge of the full chain."
  (`Pine.LNX.4.58.0405222341380.18601@ppc970.osdl.org`, 2004-05-23,
  https://lore.kernel.org/all/Pine.LNX.4.58.0405222341380.18601%40ppc970.osdl.org/)
- "So one of my _personal_ reasons I don't want to put too much process in place is that I don't think process is
  appropriate for everything" (`alpine.LFD.1.10.0804301919080.5994@woody.linux-foundation.org`, 2008-05-01,
  https://lore.kernel.org/all/alpine.LFD.1.10.0804301919080.5994%40woody.linux-foundation.org/)
- "But I think the real fix is to have real humans that help de-noisify the bug reports."
  (`alpine.LFD.0.98.0704281601060.9964@woody.linux-foundation.org`, 2007-04-28,
  https://lore.kernel.org/all/alpine.LFD.0.98.0704281601060.9964%40woody.linux-foundation.org/)
- "I only need to trust 5 10 15 people if I have a network of trust that covers those five 10 15 people that are
  outstanding and I know they're outstanding I can pull from them" (Google talk, `https://www.youtube.com/watch?v=4XpnKHJAok8`,
  given 2007-05-03, corpus date 2007-05-14, https://www.youtube.com/watch?v=4XpnKHJAok8)
- "(*) IMPORTANT NOTE: I do not believe in "trusting the AI tool". The reason we'd trust the tool is not because we
  trust the AI, but because we'd trust the person or group who is orchestrating the tool!"
  (`CAHk-=wjCcHUr=-Ycsey0khWnn68O6D=ZN-bE+8Sq4NetXpFuPA@mail.gmail.com`, 2026-07-17,
  https://lore.kernel.org/all/CAHk-%3DwjCcHUr%3D-Ycsey0khWnn68O6D%3DZN-bE%2B8Sq4NetXpFuPA%40mail.gmail.com/)
- "It helps to realize that the key difference between a big decision and a small one is whether you can fix your
  decision afterwards." (management-style.rst, corpus snapshot 2026-11-25,
  https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/plain/Documentation/process/management-style.rst)

**How well supported.** About 14 documents, 2002 to 2026 (patch penguin 2002 x2, DCO 2004, Slow DOWN 2008 x2,
bugzilla 2007, Al Viro 2007, Google talk 2007, CFS 2007, AI review 2026, management-style).

---

## Part B. The design of git (2005 to 2007, and the 2007 Google talk)

Almost all of Part B is **[tool/app]**: said about a user-space program he designed and wrote. It is the strongest
evidence that his principles apply outside the kernel.

The talk transcript (`source = 'talk'`) is captioned without punctuation or speaker marks, and the captioning
garbles words ("shaan" for SHA-1, "comess" for compress). Quotes from it are copied exactly as captioned.

### 14. Get the data model right first; the code follows from it [tool/app, stated as general]

**Principle.** Design around a small number of clear, rigid data structures with exact semantics, and let the
code be whatever manages them. A program with a simple data model and an explicit "mental model" stays
understandable and lets others reimplement it. A program that accretes loosely defined data does not.

**What triggers it in a review.**
- New persisted fields or tables with fuzzy meaning ("notes", "related_to", "status" with free text) that code
  will start interpreting.
- Parsing free-form text for structured meaning ("a line starting with REF:").
- Abstraction layers wrapped around the core data structures where the data structures are the point.
- A schema change reviewed as a code change. It deserves more scrutiny, not less.

**His reasoning.** "great programs come not out of great coding, but out of great data structures", and rigid
formats let programs "either do the right thing or unambiguously say "that's crap"" (2005). Data-first design is
"one of the reasons git has been fairly successful", and it makes the format easy for others to implement (2006).
Git is "a filesystem" with an SCM on top; the core encodes only "very very limited relationships" (2005). Good
design comes from "a few basic concepts", not from being clever (2006).

**How serious.** He refused proposals that blur the model ("I'm violently opposed", 2006 "prior" links), and has
held to this from the first week of git.

**Limits and exceptions.**
- Free-form data is fine where the model says it is free-form: the commit message body is where "explanations of
  _why_" go, and git "doesn't care what the format is" (2005).
- Scripts above the core may record "extra crap" as informational (2005).
- The on-disk encoding can change. Only the hashed content model is fixed (principle 15).

**Outside the kernel.** This transfers directly; it is the central transferable claim. Review the schema and the
types before the code. Prefer closed, typed representations over stringly-typed metadata.

**Evidence.**
- "The thing is, great programs come not out of great coding, but out of great data structures. The whole git
  philosophy bases itself on getting the data structure right." (`Pine.LNX.4.58.0504231252450.2344@ppc970.osdl.org`,
  2005-04-23, https://lore.kernel.org/all/Pine.LNX.4.58.0504231252450.2344%40ppc970.osdl.org/)
- "In fact, I'm a huge proponent of designing your code around the data, rather than the other way around, and I
  think it's one of the reasons git has been fairly successful (*)." and "Bad programmers worry about the code.
  Good programmers worry about data structures and their relationships."
  (`Pine.LNX.4.64.0607270936200.4168@g5.osdl.org`, 2006-07-27,
  https://lore.kernel.org/all/Pine.LNX.4.64.0607270936200.4168%40g5.osdl.org/)
- "The git model really is about tracking data, not about tracking what happened to _create_ that data." and
  "There are too many messy SCM's out there that do not hav ea "philosophy". Dammit, I'm not interested in creating
  another one. This thing has a mental model, and we keep to that model."
  (`Pine.LNX.4.58.0504141102430.7211@ppc970.osdl.org`, 2005-04-14,
  https://lore.kernel.org/all/Pine.LNX.4.58.0504141102430.7211%40ppc970.osdl.org/)
- "git tracks your content it never ever tracks a single file you cannot track a file in git" (Google talk,
  2007-05-03, https://www.youtube.com/watch?v=4XpnKHJAok8)
- "the way to do good basic design isn't actually to be really smart about it, but to try to have a few basic
  concepts." (`Pine.LNX.4.64.0610172014250.3962@g5.osdl.org`, 2006-10-18,
  https://lore.kernel.org/all/Pine.LNX.4.64.0610172014250.3962%40g5.osdl.org/)
- "a willingness to not abstract away the data structures and algorithms, because those are the *whole*point* of
  core git." (`alpine.LFD.0.999.0709070203200.5626@evo.linux-foundation.org`, 2007-09-07,
  https://lore.kernel.org/all/alpine.LFD.0.999.0709070203200.5626%40evo.linux-foundation.org/)

**How well supported.** About 15 git-list messages, 2005 to 2008, plus the talk. Echoed in sparse (2004) and
subsurface (2011 to 2022) commits (principle 20).

---

### 15. Store hard facts, derive interpretations at query time, and the data outlives the code [tool/app]

**Principle.** Persist only what is unambiguously true (content, parents, authorship). Compute heuristic or
interpretive information (renames, copies, "related" commits, line history) when it is asked for. The stored data
then never encodes today's weak algorithm, history created by any path is equivalent, and better algorithms
improve old data retroactively. Do not store redundant data that can be cheaply recomputed.

**What triggers it in a review.**
- Persisting a derived or guessed value (a classification, a "moved from" link, a cached score) as if it were
  primary data, especially when the derivation will improve.
- Data whose meaning depends on how it was created ("written by tool A versus tool B").
- Storing both a value and something derivable from it, so the two can disagree.

```sql
-- raises it: the guess is frozen into the record
ALTER TABLE files ADD COLUMN renamed_from_id INT;  -- set by today's heuristic at write time
-- what he did in git: store the trees; compute renames at diff/log time with -M/-C
```

**His reasoning.** Recording renames at commit time means "freezing your (crappy) algorithm at tree creation
time"; the "where did this come from" question belongs at "_search_ time" (2005). Because rename detection is
after-the-fact, "we can change the heuristics _after_ seeing examples, and the examples magically correct
themselves!" (2007 git commit). Storing renames makes "your repository depend on how you *created* your data,
rather than on what the data is" (2011). Only the hashed form is fixed; "How we then *encode* the data on disk is
totally immaterial" (2007). He dropped permission bits from use, "although the data format was retained" (2007).

**How serious.** This is foundational, and he defended it repeatedly from 2005 to 2011.

**Limits and exceptions.**
- Redundant data is acceptable when recomputing it is not cheap: the 2011 generation-numbers thread turns on
  exactly that ("if it doesn't have a negative impact on performance").
- He later implemented `git log --follow` while calling its file-identity model "broken" (2007). Users wanted it,
  so he built it on top of the hard data without changing the store.

**Outside the kernel.** This transfers strongly: event sourcing, keeping raw inputs, computing views, derived
columns as caches with a rebuild path, and not baking ML/heuristic output into the source of truth. In subsurface
he applied it to device IDs: "purely a hash of the real serial number" (2021, commit `6c4e890960036b127eab513ca967e9454bc63d54`,
read but not quoted in the JSONL).

**Evidence.**
- "You're freezing your (crappy) algorithm at tree creation time, and basically making it pointless to ever create
  something better later, because even if hardware and software improves, you've codified that "we have to have
  crappy information"." and "And that "where did this come from" decision should be done at _search_ time, not
  commit time." (`Pine.LNX.4.58.0504150753440.7211@ppc970.osdl.org`, 2005-04-15,
  https://lore.kernel.org/all/Pine.LNX.4.58.0504150753440.7211%40ppc970.osdl.org/)
- "The rename detection is an "after-the-fact" thing, not something that actually gets saved in the repository,
  which is why we can change the heuristics _after_ seeing examples, and the examples magically correct
  themselves!" (git commit `9ae8fcb36ac9fde8e048a304cc3717f2c7914e78`, 2007-11-30,
  https://git.kernel.org/pub/scm/git/git.git/commit/?id=9ae8fcb36ac9fde8e048a304cc3717f2c7914e78)
- "Git tracks not "intent", but "hard data"." (`Pine.LNX.4.64.0703191259420.6730@woody.linux-foundation.org`,
  2007-03-19, https://lore.kernel.org/all/Pine.LNX.4.64.0703191259420.6730%40woody.linux-foundation.org/)
- "Once you start adding data that has no clear semantics, you're screwed. At that point, it's a "track guesses"
  game, not a "track contents" game." (`Pine.LNX.4.64.0604251004410.3701@g5.osdl.org`, 2006-04-25,
  https://lore.kernel.org/all/Pine.LNX.4.64.0604251004410.3701%40g5.osdl.org/)
- "It's fundamentally stupid because it will FOREVER SCREW UP YOUR DATA, and because it will make merging an
  unmitigated disaster and make your repository depend on how you *created* your data, rather than on what the
  data is." and "For example, redundant data takes disk space and network bandwidth, and if something can be
  recomputed cheaply (ie if it doesn't have a negative impact on performance), then redundant data is just bad."
  (`CA+55aFwqFhzd_cmbFxkCyNXhF99igBqdr8p4J76hLz=m4=ZNWg@mail.gmail.com`, 2011-07-17,
  https://lore.kernel.org/all/CA%2B55aFwqFhzd_cmbFxkCyNXhF99igBqdr8p4J76hLz%3Dm4%3DZNWg%40mail.gmail.com/)
- "The SHA1 itself just depends on "$type $size\0$data" (no deflate phase), and that one is easy and cheap to
  calculate. How we then *encode* the data on disk is totally immaterial."
  (`alpine.LFD.0.9999.0711270821280.5869@woody.linux-foundation.org`, 2007-11-27,
  https://lore.kernel.org/all/alpine.LFD.0.9999.0711270821280.5869%40woody.linux-foundation.org/)

**How well supported.** About 14 messages and commits, 2005 to 2011 (renames 2005 x3, 2006 x3, 2007 x4, 2011,
`--follow` 2007, `-C` blame 2006, the from-scratch thread 2007).

---

### 16. Integrity is a requirement: verify everything, fail loudly, trust your own copy [tool/app]

**Principle.** A tool that stores people's work must guarantee that what comes out is what went in, and must
detect corruption rather than silently pass it on. Use strong content hashes as a consistency check, have rigid
formats that reject garbage, check every error return on the data you care about, and trust local data over
incoming data.

**What triggers it in a review.**
- Persisting or transmitting data without checksums or validation on read.
- Ignored return values on `close()`, `fsync()`, `write()` or rename in code that writes user data.
- Lenient parsers that "guess" at malformed input in a core format.
- Sync logic that lets remote data overwrite local data on conflict by default.

**His reasoning.** Integrity was one of his three hard requirements for any SCM (talk). SHA-1 in git "isn't even a
security feature it's purely a consistency check" (talk). Rigid formats make reliable programs (2005). On a
collision, "earlier will override" because "you should primarily trust only your _own_ repository" (2006). Git
"tries to be really anal": checking `close()` found a CIFS data-loss bug (2009).

**How serious.** This was a selection criterion: alternatives were "not worth using" if they failed it. Core
formats never relaxed.

**Limits and exceptions.**
- Paranoia is a cost. He proposed turning the full SHA-1 collision re-check off by default because it was
  expensive on large repositories: "It's not like anybody has ever shown a SHA1 collision" (2007).
- `fsync()` on object files was off by default because ext3 made it unusable, and the design tolerates losing a
  new object (2009).
- Checks go where data matters most: "only for the core git object files that we care about so much" (2009).

**Outside the kernel.** This transfers directly to any storage, sync or backup code: content hashes, atomic
rename, error checks on close/flush, and refusing malformed records.

**Evidence.**
- "if you're not distributed you're not worth using it's that simple if you perform badly you're not worth using
  it is that simple and if you cannot guarantee that the stuff I put into an SCM comes out exactly the same you're
  not worth using" (Google talk, 2007-05-03, https://www.youtube.com/watch?v=4XpnKHJAok8)
- "the shaan as far as git is concerned isn't even a security feature it's purely a consistency check the security
  parts are elsewhere" (Google talk, 2007-05-03, https://www.youtube.com/watch?v=4XpnKHJAok8; "shaan" is the
  caption's rendering of "SHA-1")
- "It means that we have very very fixed formats so that programs can either do the right thing or unambiguously
  say "that's crap"." (`Pine.LNX.4.58.0504231252450.2344@ppc970.osdl.org`, 2005-04-23,
  https://lore.kernel.org/all/Pine.LNX.4.58.0504231252450.2344%40ppc970.osdl.org/)
- "However, the "earlier will override" is very much what you want from a security standpoint: remember that the
  git model is that you should primarily trust only your _own_ repository."
  (`Pine.LNX.4.64.0608281034440.27779@g5.osdl.org`, 2006-08-28,
  https://lore.kernel.org/all/Pine.LNX.4.64.0608281034440.27779%40g5.osdl.org/)
- "For example, the latest one came from git actually checking the error code from 'close()'."
  (`alpine.LFD.2.00.0903252017100.3032@localhost.localdomain`, 2009-03-26,
  https://lore.kernel.org/all/alpine.LFD.2.00.0903252017100.3032%40localhost.localdomain/)
- Limit: "That whole "verify no SHA1 hash collision" code is really pretty damn paranoid. Maybe we shouldn't have
  it enabled by default." (`Pine.LNX.4.64.0704031304420.6730@woody.linux-foundation.org`, 2007-04-03,
  https://lore.kernel.org/all/Pine.LNX.4.64.0704031304420.6730%40woody.linux-foundation.org/)

**How well supported.** About 12 documents, 2005 to 2017 (talk, 2005 x3, 2006 x2, 2007 x2, 2009, SHAttered 2017
x3 read in search).

---

### 17. Performance is a feature that changes how people work, and it cannot be bolted on later [tool/app]

**Principle.** Speed is designed in from the data structures up. A tenfold or hundredfold speed-up is not "the same
thing faster": it changes behaviour (merge daily instead of yearly). Measure the operation that matters (merging,
not branching; I/O, not CPU) and optimise that, for realistic usage.

**What triggers it in a review.**
- "We'll optimise later" for a core path whose data layout fixes its cost.
- Benchmarks of the cheap operation rather than the one users wait on.
- Designs that force full traversal where incremental output is possible (the topo-order case).
- Conversely, effort spent on usage patterns nobody has.

**His reasoning.** "if you can do something really fast really well people start using it different" (talk).
Subversion optimised branch creation, "the wrong thing you're measuring", when merging was the problem (talk).
performance "isn't a secondary feature. It's also not something you can add later by optimizing. It's also a
mindset issue" (2008). Be incremental because "IO costs" are "the first-order effects" (2007). A built-in diff cut
`git diff` from 24.8 s to 4.6 s, and he published the numbers with the downsides (2006 commit).

**How serious.** Performance was a hard requirement for any SCM (principle 16). He rejected designs and languages
on efficiency grounds (C++ in 2007, Monotone in the talk).

**Limits and exceptions.**
- "Fast enough" is fine for unrealistic workloads. He accepted 3 commits per second because replacing quilt was
  not a realistic use (2005).
- He trades disk for cache ("I much prefer to waste some CPU time to save disk cache", 2005) and accepts code
  complexity where performance needs it ("doing it well is complicated", talk).
- In subsurface he chose readability over speed where the code is not hot (principle 20).

**Outside the kernel.** This transfers directly to latency-sensitive tools, CLIs, developer tooling and UI
interactions. Ask which operation users actually wait on.

**Evidence.**
- "a lot of thing people seem to think that performance is about doing the same thing just doing it faster and
  that's not true that's not what performance is all about if you can do something really fast really well people
  start using it different" (Google talk, 2007-05-03, https://www.youtube.com/watch?v=4XpnKHJAok8)
- "nobody's interested in branching branches are completely useless unless you merge them" (Google talk,
  2007-05-03, https://www.youtube.com/watch?v=4XpnKHJAok8)
- "And the thing is, "performance" isn't a secondary feature. It's also not something you can add later by
  optimizing." (`alpine.LFD.1.00.0801251407010.5056@hp.linux-foundation.org`, 2008-01-25,
  https://lore.kernel.org/all/alpine.LFD.1.00.0801251407010.5056%40hp.linux-foundation.org/)
- "See? You shouldn't care about CPU usage, you should care about IO costs! Those are the first-order effects."
  (`alpine.LFD.0.999.0711010910090.3342@woody.linux-foundation.org`, 2007-11-01,
  https://lore.kernel.org/all/alpine.LFD.0.999.0711010910090.3342%40woody.linux-foundation.org/)
- Limit: "Yeah, I realize that it still takes you half a minute to commit the 100 quilt patches, but I just can't
  bring myself to think it's a huge problem in the kind of usage patterns I think are realistic."
  (`Pine.LNX.4.58.0504200957030.6467@ppc970.osdl.org`, 2005-04-20,
  https://lore.kernel.org/all/Pine.LNX.4.58.0504200957030.6467%40ppc970.osdl.org/)

**How well supported.** About 12 documents, 2005 to 2008 (talk, write-tree 2005 x2, SCM saga 2005 x3, libxdiff
2006, object allocator 2006, gitk 2007, case-folding 2008).

---

### 18. Distributed means every copy is equal; no trunk, no central gatekeeping [tool/app; the social side is general]

**Principle.** No repository is more important than any other. Branching and committing are local and private;
integration happens by pulling from people you trust. Designs that assume a central trunk (stable revision
numbers, a special first parent, central branch namespaces) carry hidden costs in workflow and in psychology.

**What triggers it in a review.** In tools and data systems: identifiers that only work if one node is
authoritative (sequential IDs across replicas); a "primary" assumption baked into a sync protocol; a global
namespace forcing naming rules on private work.

**His reasoning.** Central systems create a "commit access" class and "endless hours of politics"; distribution
removes that, makes offline work and cheap branches natural, and makes backups a side effect (talk). Stable
revision numbers require a "trunk mentality", and "THAT is the true cost" (2006). The pull model prevents the
maintainer's queue from congesting (2005).

**How serious.** This was a design goal and a hard requirement ("if you're not distributed you're not worth
using").

**Limits and exceptions.**
- In the talk he concedes that "if you're in a tightly controlled corporate environment centralized systems work
  better" and have worked for 35 years. His claim is "cannot work as well", not "cannot work".
- Very large monorepos fit git badly; he advised splitting at content boundaries (talk).

**Outside the kernel.** This applies to distributed data design (UUIDs or content addresses rather than central
sequences, merge-friendly formats; see the subsurface git format) and to team workflows. It is less a code-review
rule than a design-review rule.

**Evidence.**
- "distrib being distributed very much means that you do not have one central location that keeps track of your
  data no single place is more important than any other single place" (Google talk, 2007-05-03,
  https://www.youtube.com/watch?v=4XpnKHJAok8)
- "I'll just point out that one of my design goals for git was to make every single repository 100% equal. That
  means that there MUST NOT be a "trunk", or a special line of development." and "No. The _cost_ of the revision is
  the "trunk mentality". THAT is the true cost." (`Pine.LNX.4.64.0610172014250.3962@g5.osdl.org`, 2006-10-18,
  https://lore.kernel.org/all/Pine.LNX.4.64.0610172014250.3962%40g5.osdl.org/)
- "It comes from the "Linus pulls" model where people just told me that they were ready, instead of the "everybody
  pushes to Linus" model, where the destination gets congested at times."
  (`Pine.LNX.4.58.0504070747580.28951@ppc970.osdl.org`, 2005-04-07,
  https://lore.kernel.org/all/Pine.LNX.4.58.0504070747580.28951%40ppc970.osdl.org/)

**How well supported.** About 7 documents, 2005 to 2007, the talk being the main one.

---

### 19. What git rejected: features whose semantics cannot be made exact [tool/app]

**Principle.** Refuse a feature, however popular, if it cannot be made correct under the data model: it will be
broken in some workflow, and the breakage spreads. Supporting a bad interface from the old tool holds the new one
back. When users insist, build it on top, clearly labelled, without changing the core.

**What he rejected, with his reasons (all read in full):**

| Rejected | Why | Doc |
|---|---|---|
| File identity / rename tracking | Two identities meeting under one name; history depends on how data was created | 2006-03-01, 2005-04-14, 2011-07-17 |
| Stable revision numbers | Imply a trunk (principle 18) | 2006-10-18 |
| Keyword expansion (`$Id$`) | Diffs break either way; branch switching rewrites every file | 2007-04-17 |
| Database back end | Slower, hard to replicate; immutable files rsync trivially | 2005-04-08, 2007-11-27 |
| Weak-semantics links ("prior" commits) | Not fsck-able, no clear semantics | 2006-04-25 |
| Ownership and full permission bits | Not appropriate for a distributed project; umask differences | 2007-08-22 |
| CVS-style annotate interface | "just a mistake"; blame `-C` follows moved code | 2006-07-27, 2006-11-28 |
| C++ for the core | Abstractions you cannot fix later; core is raw data structures | 2007-09-06, 2007-09-07 |

**Limits.** He accepted keyword *un*expansion as stateless and opt-in (2007). He built `--follow` despite calling
its model broken (2007). The rejections target the stored model; conveniences layered above it are negotiable.

**Outside the kernel.** For a reviewer: a feature that "mostly works" but is wrong under merge, concurrency or
replication should be pushed to an optional layer, not into the core model.

**Evidence.**
- "JUST THE FACT THAT YOU TRY TO TRACK FILE "IDENTITY" HISTORY IS BROKEN." (`Pine.LNX.4.64.0603010859200.22647@g5.osdl.org`,
  2006-03-01, https://lore.kernel.org/all/Pine.LNX.4.64.0603010859200.22647%40g5.osdl.org/)
- "See? Keywords simply *cannot* work. They're broken. Either you can ignore them (and not show them in diffs), in
  which case the diff is broken, or you can not ignore them (and show them in diffs) in which case the diff is
  *also* broken, just differently." (`Pine.LNX.4.64.0704170833560.5473@woody.linux-foundation.org`, 2007-04-17,
  https://lore.kernel.org/all/Pine.LNX.4.64.0704170833560.5473%40woody.linux-foundation.org/)
- "For example, the CVS "annotate" ABI is just a mistake, and trying to support that would just have held git back
  from realizing that you can be so much more." (`Pine.LNX.4.64.0607271232090.4168@g5.osdl.org`, 2006-07-27,
  https://lore.kernel.org/all/Pine.LNX.4.64.0607271232090.4168%40g5.osdl.org/)
- "But the ownership thing we've never even tried to support, since it was so obviously not something that was
  appropriate for a distributed project." (`alpine.LFD.0.999.0708221618510.30176@woody.linux-foundation.org`,
  2007-08-22, https://lore.kernel.org/all/alpine.LFD.0.999.0708221618510.30176%40woody.linux-foundation.org/)
- Limit: "Put another way: I think the model is broken, but given the broken model, I think this patch does just
  about as well as you can do." (git commit `750f7b668f33c9e8decbdd8141115328992d6fea`, 2007-06-19,
  https://git.kernel.org/pub/scm/git/git.git/commit/?id=750f7b668f33c9e8decbdd8141115328992d6fea)

**How well supported.** About 14 documents, 2005 to 2011.

Note on ABIs: in the 2006 libification thread he wrote that ABIs are "often _way_ overhyped" and that bad ones
should be fixed. That is about library and internal interfaces in an open-source tool. It does not contradict his
kernel user-space ABI rule, which the regressions theme covers; the skill should keep the two apart.

---

## Part C. His application code (subsurface, sparse and git commits)

These are **[tool/app]** throughout. I read about 45 commit messages in full: about 22 subsurface (2011 to 2022),
about 13 sparse (2003 to 2014), and about 10 git (2005 to 2009).

**Authorship caveat.** The 2022 sparse commits (`177a7a9e...`, `0356ac84...` and the other 2022-08-23 "bitwise:"
commits) carry the note "bvanassche: Rewrite commit message in imperative mood". Their wording is not his, and none
is quoted. Sparse commit `5119a12a...` (2014) carries only Christopher Li's Signed-off-by, so its authorship is
unclear, and it is not quoted either.

### 20. In application code he fixes bugs by simplifying the model, not by adding cases [tool/app]

**Principle.** When code is fragile, remove derived state and special cases so that the bug "just goes away". Split
monster functions even at some cost in speed when the path is not hot. Keep saved formats unambiguous,
non-redundant and merge-friendly. Preserve type information. Be robust to bad input (skip the bad record, keep
going), and relax a model that real data violates rather than "fix up" the data destructively.

**What triggers it in a review.**
- Cached or derived flags that can drift from the data they summarise (`same_cylinder`, `last_pressure` set "at
  changes").
- One loop doing four jobs. An unused computed value left over from old code.
- Saving both a value and an alternative representation of it, so the format becomes ambiguous.
- `void *` or untyped callbacks that hide size mismatches.
- One bad record aborting a whole import.
- Normalisation that destroys user data to satisfy an internal invariant.

```c
/* before (pattern he removed): derived state kept in sync at special moments */
if (sample->cylinder != last_cyl) { last_pressure[cyl] = p; same_cylinder = 0; }
/* after: no derived flag, no special case */
last_pressure[sample->cylinder] = sample->pressure;  /* "just set the damn thing on every single sample" */
```

**His reasoning (from the commits).** Simpler loops "simply don't have special cases", and the reported bug "just
goes away" (2013). The fixup loop is "only done once per dive", so readability wins, and the cleanup exposed two
more bugs (2016). Saving working pressure "makes the output format ambiguous" (2011). The git save format is
line-based "so that you can merge these files automatically" (2022). Enforcing trip ordering "really does destroy
the actual dive data", so he relaxed the rule instead (2012). In sparse, a richer hierarchical structure made "the
data structure a bit more complex, but it simplifies some of the code" (2004). A "valid optimization" was removed
because "it screws up the type system" (2004).

**How serious.** These are his own commits. They show what he fixes when he is the author, not a reviewer's
enforcement level.

**Limits and exceptions.**
- He commits "quick hack" fixes with their limits spelled out ("This isn't right if you switch back to the same
  cylinder multiple times", `e919a0f2eac8bc4471b499b73a77c95e81240fd9`, 2011, read but not quoted).
- He duplicated the XML save code for the git format rather than share it, because "trying to share it seemed just
  too painful" (`689fe36030537ab57d3a5a1a55baf86675d5ecdb`, 2014, read but not quoted). Duplication over a forced
  abstraction is consistent with principle 5.

**Outside the kernel.** This applies directly; it is application code. It is the most concrete guide in this theme
to what a "Linus-style" refactor of an app looks like.

**Evidence.**
- "get rid of some of the edge conditions by just writing the loops more clearly, so that they simply don't have
  special cases." and "As a result, the bug Mika noticed just goes away."
  (subsurface `cb0d6d6eaf549d593557490eb690bb22e91de151`, 2013-01-25,
  https://github.com/subsurface/subsurface/commit/cb0d6d6eaf549d593557490eb690bb22e91de151)
- "And the thing is, this isn't even all that performance-critical: it's only done once per dive and dc, and there
  is no reason to have a single illegible and complex loop." and "Yes, this way we walk the samples multiple times,
  but the end result is that the code is much easier to understand." (subsurface `f92e2e752f6e16af518b3e2e5221bf401221751a`,
  2016-04-01, https://github.com/subsurface/subsurface/commit/f92e2e752f6e16af518b3e2e5221bf401221751a)
- "And in fact saving it actually makes the output format ambiguous: if we give both size and working pressure,
  what does 'size' mean?" (subsurface `ecff0922d43edeb361769755d49e84d1b02caa90`, 2011-09-04,
  https://github.com/subsurface/subsurface/commit/ecff0922d43edeb361769755d49e84d1b02caa90)
- "That is very much by design, so that you can merge these files automatically, and not worry about what it does
  to the context" (subsurface `05e1294be9f4ffaf33cb32988cf6d2eac9356b17`, 2022-07-31,
  https://github.com/subsurface/subsurface/commit/05e1294be9f4ffaf33cb32988cf6d2eac9356b17)
- "Dirk had a patch to do this, but it really does destroy the actual dive data" (subsurface `96db56f89c76ffc2ede8605f4b0febb0c2261c5a`,
  2012-12-30, https://github.com/subsurface/subsurface/commit/96db56f89c76ffc2ede8605f4b0febb0c2261c5a)
- "This makes the data structure a bit more complex, but it simplifies some of the code, and makes it possible to
  evaluate complex initializers without going insane." (sparse `3c83edc32120201e1b35970be88ea1711cf30093`,
  2004-09-23, https://git.kernel.org/pub/scm/devel/sparse/sparse.git/commit/?id=3c83edc32120201e1b35970be88ea1711cf30093)
- Also in the JSONL: type safety (`f46f9139a82fd93bcdb84735649b804c27b0b9c1`, 2014-06-07), keep parsing after a bad
  dive (`958dce33263ecda91fae0f5d25494ec2ca5808ba`, 2019-09-11), and the type system over a premature optimisation
  (sparse `20adf96e0de9a8316fa487037a00fd40bbc9ce01`, 2004-07-25).

**How well supported.** About 25 commits, 2004 to 2022, across three projects. These are statements about
application code by construction.

---

### 21. He states trade-offs, downsides and limits in his own change descriptions, and cuts noise [tool/app]

**Principle.** A change description should say what is known to be wrong or missing, what the alternatives were,
why this one was chosen, and whether it is safe by default. Do not oversell micro-optimisations. Diagnostics that
produce noise about the tool's own limitations should be off by default.

**What triggers it in a review.**
- A PR that claims only upsides for a change with known gaps.
- "Experimental" behaviour enabled by default.
- No mention of the alternatives considered.
- New warnings or lints that fire constantly on correct code. For a review skill that applies to its own output:
  low-value findings that drown the real ones.

**His reasoning (from the commits).** "in the interest of full disclosure, I should also point out a few
downsides", followed by the missing-newline bug and different diff output (2006). Auto-CRLF is "simple, and it _is_
safe, since it's all off by default" (2007). A rename fix is "not pretty, it's not smart, but it seems to work"
(2007). A UI fix is "the least confusing of the possibilities", after he lists the alternatives (2013). A strtod
speed-up of half a percent is offered with "I'm sending it out to see if anybody cares" (2014). A sparse warning
"about a sparse limitation rather than a real feature" goes off by default (2009). Keeping types matters: "Not
pretty, but better than the alternative (which is to drop type information)" (2006).

**How serious.** This is self-practice, but it matches what he asks of others ("I want an explanation, and I want
it to be in many small pieces", 2007 CFS message).

**Outside the kernel.** This applies directly to PR descriptions and to the review skill's own reporting
discipline.

**Evidence.**
- "Now, in the interest of full disclosure, I should also point out a few downsides:" (git `3443546f6ef57fe28ea5cca232df8e400bfc3883`,
  2006-03-25, https://git.kernel.org/pub/scm/git/git.git/commit/?id=3443546f6ef57fe28ea5cca232df8e400bfc3883)
- "But it _is_ simple, and it _is_ safe, since it's all off by default." (git `6c510bee2013022fbce52f4b0ec0cc593fc0cc48`,
  2007-02-13, https://git.kernel.org/pub/scm/git/git.git/commit/?id=6c510bee2013022fbce52f4b0ec0cc593fc0cc48)
- "It's not pretty, it's not smart, but it seems to work. There's something to be said for keeping it simple and
  stupid." (git `9ae8fcb36ac9fde8e048a304cc3717f2c7914e78`, 2007-11-30,
  https://git.kernel.org/pub/scm/git/git.git/commit/?id=9ae8fcb36ac9fde8e048a304cc3717f2c7914e78)
- "So on the whole, I don't love this patch, but it seems to be the least confusing of the possibilities."
  (subsurface `c9113a1f429e74717c90261458a8aadde7e391f8`, 2013-06-09,
  https://github.com/subsurface/subsurface/commit/c9113a1f429e74717c90261458a8aadde7e391f8)
- "The half a percent speedup on loading time isn't really noticeable or even measurable outside of profiling
  startup costs, but rather than carry this along in my tree or just throw it away, I'm sending it out to see if
  anybody cares." (subsurface `2d0cf4a87a3876678cc93f71c6438106f85898b9`, 2014-02-10,
  https://github.com/subsurface/subsurface/commit/2d0cf4a87a3876678cc93f71c6438106f85898b9)
- "It's a very annoying warning, and it's about a sparse limitation rather than a real feature, so don't do it by
  default." (sparse `59df2fd69755fe8fb36420ea163f9aa52346e61a`, 2009-06-18,
  https://git.kernel.org/pub/scm/devel/sparse/sparse.git/commit/?id=59df2fd69755fe8fb36420ea163f9aa52346e61a)

**How well supported.** About 15 commits, 2003 to 2014.

---

## Changes of position over time

| Topic | Earlier | Later / current | Evidence |
|---|---|---|---|
| Microkernels and user-space policy | 1992: microkernels "nicer", Linux loses on theory. 1999: "don't have any advantages". 2002: "crap like microkernels" | 2003: "layering is often good, but that does not mean that ALL layering is good". 2024: accepts FUSE and sched_ext as shims that ask user space for policy, because the feared problems "did not" materialise | Principle 4 quotes; sched_ext 2024 |
| Systems languages | 2007: C++ "horrible", C "the only sane choice" for git | 2025: backs Rust in the kernel and overrides a maintainer blocking Rust users. The objection was always to abstractions and mindset, not to non-C as such | 2007-09-06; 2025-02-21, 2025-02-23 |
| Process | 2008: wary of process ("I don't think process is appropriate for everything") | 2026: willing to explore AI-run "trivial trees" if trusted people run them; wants pre-existing issues kept out of gating | 2008-05-01; 2026-07-17 |
| Specs | 2005: "When reality and specs clash, the spec has zero meaning" | 2026: specs acceptable only as machine-checked descriptions generated from reality | 2005-09-29; 2026-11-16 |
| Tone | Before 2018, often abusive (Mauro 2012, "f*cking" in 2010) | After his 2018 break, the same positions in milder wording (2024 to 2026 messages refuse just as firmly). The skill should take the substance and current tone | Principle 12 |
| Design versus evolution | Constant, 2001 to 2008 to 2021 | Constant: incremental first, rewrite only for a measured win | Principle 2 |

## Not in corpus

Searched for verbatim and not found (do not quote them):

- "Talk is cheap. Show me the code." as one sentence (the famous 2000 LKML line). The corpus has "talk is cheap,
  and code rules" (2003), "Talk is cheap." (2002, 2007) and ""Show me the code", in other words" (2025)
  separately.
- "Given enough eyeballs, all bugs are shallow" (that is Eric Raymond's line in any case).
- "Nobody should start to undertake a large project" (no hits).
- "Intelligent design" as his own framing of Linux development: the 2008 hit uses "intelligent designer" against
  Greg KH. The famous phrase "Linux is evolution, not intelligent design" was not found in that form.
- A quotable statement on "show me the user" as a phrase: the 2006 CGit hit is about races, not users. The idea is
  well supported in other words (principle 1).
- His own longer statement of why he wrote subsurface or how it differs from kernel work. Commits exist, but no
  essay or mail on application design philosophy was found under `subsurface` searches.

## What I looked for and did not find, and where evidence is thin

- **Frameworks in application code specifically.** Apart from the 2007 C++/STL/Boost posts and the "duplicate
  rather than share" subsurface commit, he says little about application frameworks (ORMs, GUI toolkits). The
  subsurface gtk commits complain about gtk selection semantics ("gtk selections are annoying",
  `4b5b732f2cf8a63445a610642285304526850c91`, 2013) but draw no general rule. Treat principle 6 as kernel and git
  evidence applied by analogy to application frameworks.
- **Explicit statements that a principle applies to application code.** Direct statements: 2007 Libification
  (designing is overrated), 2006 data structures (good programmers worry about data structures), the 2009 fsync post (make badly written code just work), 2003 comp.arch (system call or library), and the talk. Everything else in Part A is said about
  the kernel. The application evidence for it is his own behaviour in subsurface, sparse and git.
- **Sparse commit messages are short** (median under 200 characters) and mostly technical. They support principles
  20 and 21 only.
- **Principle 12 (own the bug)** is thin here by design; the regressions theme should carry it.
- **Principle 18 (distributed)** rests mainly on the talk and two mails; adequate but not deep.
- **Trust versus process:** good evidence on trust; less on concrete process he rejected beyond 2008 and the 2026
  AI thread.

## Reading log (approximate)

About 190 documents read in full or in their own-text part, plus about 1,500 search hits scanned by subject, over
roughly 40 search phrasings: theoretical/real, show me, framework/abstraction/infrastructure, policy/mechanism,
microkernel/layering, pragmatic, spec/standard/POSIX, special case/one user, common case, say no, overdesign,
rewrite/incremental/flag day/bisect, trust/process/bureaucracy, blame/own up, data structures, renames, SHA-1,
performance, distributed/trunk, keyword expansion, C++, and subsurface, sparse and git commit sampling by length.
The Google talk transcript was read in full (57k characters).

Breakdown: LKML and other kernel lists about 105, git list about 38, Usenet and yarchive about 9, talk 1,
kernel-docs 1, commits about 45.
