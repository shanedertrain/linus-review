# Design judgement

Load this when: a diff adds an abstraction, module, interface, option, endpoint, service boundary, persisted
field or file format; when it rewrites or migrates something; or when it is justified by a future need or a
spec, not a present user.

**Basis key.** The Basis line under each principle is one of:
- *his words about tool/app code*: said about git, sparse, subsurface or user-space programs. These apply directly.
- *his words, general*: he framed it as a rule of software in general.
- *kernel, transfer inferred*: he said it about kernel code. Applying it elsewhere is our reading, and so is any
  non-C example.

## Quick scan

1. Is there a real user or a measured problem today, or only *this could happen*?
2. Is there generic machinery (interface, registry, options bag, shared helper) with one caller?
3. Could this land as smaller steps that each work, with the old path alive until callers move?
4. Does the common path pay for a rare caller? Is the correct use of the interface the easy one?
5. Is the decision made in the layer that has the information?
6. Does the abstraction or the new boundary hide what callers need, or force information through a channel?
7. Does a spec, not real behaviour, drive this?
8. Was the data model reviewed before the code, with exact types and relationships?
9. Is a guess, a derived value or a redundant copy being stored as fact?
10. Is the format strict and unambiguous? Will corruption or a failed write be detected?
11. Is a bug fixed by adding a case where removing state would make it go away?
12. As reviewer: am I blocking on something that is not this change's business?

## 1. A real user and real numbers, today

**Severity:** rework. Reject if it adds permanent public surface (API, option, format field) nobody uses yet.
**Basis:** kernel, transfer inferred
**Rule:** The change must answer a present problem, shown by a real caller, a bug report or a measurement on
the real workload. A hypothetical case, a micro-benchmark of the mechanism, or *merge now and it will prove
itself* is not a reason.
**Look for:**
- *For flexibility*, *in case someone needs*, *will let us later*, with no caller in the diff.
- A benchmark of the primitive in a tight loop instead of the application that wanted it.
**Why:** Without a real user you cannot know the semantics are right, and once it is in, nobody takes it out.
**Unless:**
- **Races and locking.** Rare is no excuse there; he calls dodgy locking a serious bug whether or not it matters
  in practice (said about CGit, a user-space tool).
- A security hole is real once the attack can be described.
- When users and numbers appear, the bar is met.
**He said:** "But people didn't post code, people didn't post numbers, and people didn't point to actual real uses, just "this could happen"." (2017-10-13, `CA+55aFy54Sk63VkS3HFnd4MPiSbgV6==NaYwr+D9sjG6KZGmHQ@mail.gmail.com`)

## 2. No generic machinery for one caller

**Severity:** rework.
**Basis:** kernel, transfer inferred. In subsurface he duplicated the XML save code for the git format rather than
force a shared abstraction (his commit, 2014).
**Rule:** Code with one user lives in that user. No interface, framework, registry or extension point before
real users shape it. An interface that can *expose anything* means the author does not know what is needed.
**Look for:**
- An abstract base or trait with one implementation.
- A plugin registry with one plugin.
- A new `utils` or `common` module whose only caller is in the diff.
- A grab-bag parameter, such as `get_info(kind, **kwargs) -> dict` or `options: Record<string, unknown>`.
-
- An unsafe helper made public when only one careful caller can use it.
**Why:** Infrastructure no need has shaped is usually wrong. A shared one-user helper gets misused by people who do
not know its conditions.
**Unless:**
- A mechanism that removes a real, general problem may land before all its users are known.
- An abstraction with several real users is welcome.
- A thin typed convenience for the most common case is fine.
**He said:** "It's a huge sign of over-design and "I don't know what the hell I want to expose, so I'll make this generic thing that can expose anything, and then I start adding random fields"." (2020-08-17, `CAHk-=wig0ZqWxgWtD9F1xZzE7jEmgLmXRWABhss0+er3ZRtb9g@mail.gmail.com`)

## 3. Smallest working step; evolve, don't flip

**Severity:** rework.
**Basis:** his words, general. His post against up-front design was on the git list, about git. The bisection
detail was said about kernel code.
**Rule:** Each step builds and works. Add the new interface beside the old one, move callers one at a time, and
delete the old one when unused. His order of preference:
- incremental changes with no flag day;
- then the same interface with A/B choice;
- a total rewrite last.
**Look for:**
- One PR that replaces a subsystem.
- A series whose last patch switches everything over.
- Old API removed in the same change that adds the new one.
- A framework before any working use.
**Why:** Up-front designs are wrong in ways only use reveals. Every intermediate point must be viable, so that
bisection names the step that broke. A flag day tells you almost nothing.
**Unless:**
- A rewrite that is measurably faster and cleaner can be taken; he has taken such rewrites on the numbers.
- A rewrite its owners want, with the old code deleted rather than carried.
- A rare flag day, about once or twice a year.
**He said:** "So "designing" stuff is way overrated. You can spend years designing somethign that is total crap, just because you didn't actually try it out and _realize_ that it wasn't what the user wanted" (2007-03-21, `Pine.LNX.4.64.0703211020070.6730@woody.linux-foundation.org`)

## 4. Common case first: cheap path, rare caller pays, hard-to-misuse interface

**Severity:** rework. Reject when the cost lands in a hot path.
**Basis:** kernel (block layer, epoll, MSI, CPU hotplug), transfer inferred
**Rule:** Shared paths serve the overwhelming majority. A caller with an unusual need does the extra work or opts
in. It does not add a branch, lock, hook or include that everyone pays for. Interfaces:
- Make the common case cheap.
- Do not make a required step a second call.
- Expose as few states as possible.
**Look for:**
- `if tenant == 'acme'` or `if (dev->quirk_x)` in shared code.
- `enable(dev)` plus a separate `enable_safe_mode(dev)` that half the callers forget. Make it a parameter.
- A public enum or a hook for every internal state.
-
**Why:** Engineering is balancing. If 99.99% never care, the rest do their own lifting. Every exposed state becomes
something callers depend on.
**Unless:**
- A small, documented special case beats complex infrastructure built to avoid it. He proposed such hacks
  himself.
- Internal states can exist and be documented; the objection is to exposing them.
**He said:** "It is off the default case, and _you_ do a bit of extra work instead of asking everybody else to do your heavy lifting for you." (2002-02-08, `a41kvr$836$1@penguin.transmeta.com`)

## 5. Policy in the layer that has the knowledge

**Severity:** rework.
**Basis:** kernel, transfer inferred. His test for a system call versus a library (a protection domain, or
performance, nothing else) was a general comp.arch post.
**Rule:** The shared layer provides mechanism and reports facts; the layer with the information decides. A
component states what it needs and lets the owning layer decide how to meet it. It does not toggle the other
layer's behaviour. Fix the component causing a problem instead of building workarounds elsewhere.
**Look for:**
- A library hard-coding retry, timeout, naming, encoding or UX policy.
- Module A switching off module B's feature while A is busy.
- A generic layer doing what one backend needs.
**Why:** Policy pushed down assumes every caller wants the same thing.
**Unless:** Whatever needs a protection boundary (privilege, isolation) stays in the trusted layer.
**He said:** ".. basically, what I'm arguing for is really to try to fix the underlying *reason* for problems, not add new code and new infrastructure elsewhere just because /proc/pid/smap and friends are being difficult." (2026-05-22, `CAHk-=whMQsyjB6DOyWB73jPR4wrtcc++kZy4=hGQiRE+GxKh=A@mail.gmail.com`)

## 6. Abstractions and boundaries must not hide what matters

**Severity:** rework. A convenience that hides a context rule (blocking, locking, allocation) is refused.
**Basis:**
- His words about tool/app code: the C++ object-model point (git list).
- His words, general: splitting into modules (comp.arch, on OS design).
- Kernel, transfer inferred: the rest. Services and processes are our application.
**Rule:** A layer must pass down what callers know and must not hide costs or constraints they must respect.
Split a system into communicating parts only when you must. The interaction is where the complexity goes.
**Look for:**
- A wrapper dropping deadline, priority, cancellation or context.
- A wrapper that assumes the least capable backend.
- An async wrapper hiding a blocking call. An ORM hiding N+1 queries.
- A component moved into a separate service *for modularity* while it shares state or invariants with its
  neighbours.
**Why:** An early abstraction becomes something all your code depends on and cannot be fixed. Communication
complexity often swamps the pieces.
**Unless:**
- A special-purpose abstraction built on the right data structures is good; git is one.
- A thin shim that asks another layer for policy, with real work left in place, has worked (FUSE, sched_ext).
**He said:** "I claim that you want to start communicating between independent modules no sooner than you absolutely HAVE to, and that you should avoid splitting things up until you really need to, because that communication complexity often swamps the complexity of the actual pieces involved in it." (2003-07-04, `news:1057372217.336719@palladium.transmeta.com`)

## 7. Reality beats the spec

**Severity:** rework. A spec argument used to reject a fix for real behaviour is overridden.
**Basis:** kernel and hardware, transfer inferred. The fsync post was written with his git hat on, about
application code.
**Rule:** Code to what real peers and programs do. Do not mirror a spec's layers in the code, and do not settle
arguments by quoting it. Make ordinary, imperfect caller code just work.
**Look for:**
- *Per section X the peer is wrong*, set against a fix that makes a real peer work.
- Classes copied from a standard's layers.
- A validator rejecting what real producers emit.
- An API whose safe use needs a dance most callers skip.
**Why:** A spec is for talking about things, not for implementing them.
**Unless:**
- Specs written down from real code translate back fine.
- Read the docs, but do not assume they are complete.
**He said:** "Theory and practice sometimes clash. And when that happens, theory loses. Every single time." (2009-03-26, `alpine.LFD.2.00.0903252017100.3032@localhost.localdomain`)

## 8. Data model first

**Severity:** rework, at the model.
**Basis:** his words about tool/app code (git), stated by him as a general rule
**Rule:** Review schema and types before code. A few structures with exact meaning; the code follows from them.
**Look for:**
- Persisted fields with loose meaning (`notes`, `related_to`, free-text `status`).
- In a distributed system, IDs that need one authoritative node (sequential IDs across replicas).
**Why:** He credits git's success to designing the code around the data.
**Unless:** Free-form data is fine where the model says it is free-form, such as a message body.
**He said:** "Bad programmers worry about the code. Good programmers worry about data structures and their relationships." (2006-07-27, `Pine.LNX.4.64.0607270936200.4168@g5.osdl.org`)

## 9. Store facts; derive interpretations when asked

**Severity:** rework. Reject for a store meant to last.
**Basis:** his words about tool/app code (git renames, 2005 to 2011)
**Rule:** Persist only what is unambiguously true. Compute guesses (renames, *related* links, classifications)
at query time, so that better algorithms improve old data and the record does not depend on how it was
created. Do not store what can be cheaply recomputed.
**Look for:**
- A *moved from* link written by today's heuristic.
- An ML label or score saved as primary data.
- A value stored next to something it is derived from, so the two can disagree.
**Why:** Storing the guess freezes today's algorithm into the data forever.
**Unless:**
- Redundant data is fine when recomputing it is expensive (a cache with a rebuild path).
- A feature users insist on can be built on top of the facts, labelled approximate.
**He said:** "You're freezing your (crappy) algorithm at tree creation time, and basically making it pointless to ever create something better later, because even if hardware and software improves, you've codified that "we have to have crappy information"." (2005-04-15, `Pine.LNX.4.58.0504150753440.7211@ppc970.osdl.org`)

## 10. Formats strict and unambiguous; integrity checked

**Severity:** rework. Reject when user data can be silently lost.
**Basis:** his words about tool/app code (git formats and close() checks; subsurface save format)
**Rule:**
- A format is rigid enough that a reader does the right thing or rejects the input outright.
- Never save two representations that can conflict.
- Line-oriented text merges cleanly.
- Refuse a feature that cannot be made exact under the model; git refused keyword expansion and file identity.
- Check writes. Use hashes as consistency checks. Trust the local copy over incoming data.
**Look for:**
- A value and an alternative form of it both written.
- A lenient parser guessing at malformed core data.
- Ignored results from `close()`, `fsync()`, `flush()` or rename.
-
- Remote data silently overwriting local data.
**Why:** An ambiguous format leaves a permanent question about what the data means. Git checking `close()` exposed
real filesystem data loss.
**Unless:**
- At an import boundary with messy real-world input, skip the bad record and continue (he did this in subsurface).
- Expensive full re-verification can be off by default.
**He said:** "And in fact saving it actually makes the output format ambiguous: if we give both size and working pressure, what does 'size' mean?" (2011-09-04, `ecff0922d43edeb361769755d49e84d1b02caa90`)

## 11. Fix by simplifying the model, not by adding cases

**Severity:** grumble, as a suggestion. This is how he writes his own application code, not a gate.
**Basis:** his words about tool/app code (subsurface and sparse commits)
**Rule:**
- Remove derived state and special cases so the bug disappears.
- Split monster loops even at some cost in speed off the hot path.
- Relax an invariant real data violates rather than *fix up* the data destructively.
**Look for:**
- A cached flag kept in sync at special moments.
- One loop doing four jobs.
- Normalisation that destroys user data.
**Why:** Loops written with no special cases leave the bug nowhere to live.
**Unless:** Hot paths can justify the complex version. Quick hacks are fine when their known limits are written
down.
**He said:** "get rid of some of the edge conditions by just writing the loops more clearly, so that they simply don't have special cases." (2013-01-25, `cb0d6d6eaf549d593557490eb690bb22e91de151`)

## 12. Reviewer limits

**Severity:** n/a. This governs how the reviewer reports.
**Basis:** kernel maintainers, transfer inferred
**Rule:** Saying no to unused permanent surface is the job (principle 1). A reviewer does not decide who may use
the code. Do not block on a disliked consumer, and do not make acceptance depend on fixing unrelated,
pre-existing problems. Report those separately.
**He said:** "Developers who do some patch series for X and find that interesting - or get paid for that - are *not* necessarily then just going to do Y just because the maintainer notices it." (2026-07-17, `CAHk-=wjCcHUr=-Ycsey0khWnn68O6D=ZN-bE+8Sq4NetXpFuPA@mail.gmail.com`)
