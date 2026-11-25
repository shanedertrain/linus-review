# Performance, concurrency and memory

Load this when: the diff claims a speedup, adds a cache, pool, fast path, lock, atomic, barrier, inline hint or
layout change, adds work to a path every caller or request pays for, or fixes a race or changes the order of
writes to state shared between threads, tasks or processes.

## Quick scan
1. Does the performance claim name a real workload with numbers, and is the added complexity worth that gain?
2. Does every caller now pay for something only some callers use, and is the fast case small and the rest out of line?
3. Is cold code being micro-optimised, or a slow shared primitive worked around instead of fixed?
4. Is a lock hot because of how data is shared, and is the fix a cleverer lock instead of less sharing?
5. Is lock-free or atomic code used where a plain lock would do, and does each barrier name its pair?
6. Is a race argued safe because tests never hit it?
7. Does the change slow a measured real workload, or get faster by being wrong?
8. Does a hot path dispatch through a callback or plugin layer that a cached answer could skip?
9. Does the hot path touch more memory than it needs?
10. Does big-deployment scaling work slow the ordinary single-box case?
11. Is there heap or side-work per item on the hot path, or a large stack frame on a deep call chain?

## 1. Speed claims need real-workload numbers; complexity must buy a measured gain
**Severity:** rework (reject when real complexity comes with no numbers)      **Basis:** his words; transfer inferred
**Rule:** A change justified by speed must show numbers from a workload someone runs, measured the way the code
really runs. Without them, take the simpler version. A microbenchmark locates a cost; it does not justify complexity.
**Look for:**
- *Should be faster*, *may help under load*, or a loop timing of one function as the only evidence.
- A cache layer, object pool, lock-free queue or special-case path backed by one synthetic test.
- Benchmarks that skip real costs: data never touched, RAM disk, warm caches for code that runs cold, one run.
- Bigger code (unrolling, tables) justified by hot-loop timings; when caches are cold, smaller is faster.
**Why:** The cost of the patch (size, subtlety, bugs) is certain and the speedup hypothetical. Hot loops warm the
I-cache and predict every branch, so they reward the code that loses in use.
**Unless:** Large, real effects found by microbenchmarks still count, and fixing many measured small costs adds up.
Strong real numbers beat his own dislike of an approach; shown a real load, he changes his mind.
**He said:** "Yes, I see the microbenchmark numbers, but those are pretty much irrelevant to real loads." (2013-11-18, `CA+55aFwhX-6DzxKMPk=NTmSGt1GNHE6XTHZcss+Q=hC-epC7cQ@mail.gmail.com`)
"I'll take "real numbers" over my personal dislikes any day." (2009-02-25, `alpine.LFD.2.00.0902250753030.3111@localhost.localdomain`)

## 2. Optimise the common case; keep it small and inline, the rest out of line
**Severity:** rework (grumble for a stray inline)      **Basis:** his words about kernel code, transfer inferred
**Rule:** Find what happens most (feature off, uncontended, small input) and keep that path short, behind one cheap
test; the rare case goes out of line and stays plain. Users of a feature must not slow everyone else. Inline only
that tiny fast check, or code that constants fold away; never large, cold or still-calling bodies.
**Look for:**
- Auth, tracing, metrics or feature-flag work added to every request when the feature is usually off.
- Common and rare cases interleaved, with setup only the rare case needs.
- `inline` / `#[inline(always)]` on non-trivial or cold functions, or a whole function inlined when only its first test is hot.
```c
if (unlikely(needs_slow_path(x)))
        return slow_path(x);      /* out of line */
return fast_result(x);
```
**Why:** On hot paths what matters is cache misses and mispredicted branches, paid on every call. The rare case is
slow anyway. I-cache cost from inlining can outweigh the cycles saved.
**Unless:** Check the presumed common case really is common. If an inline really matters, show profiles.
**He said:** "I care about the speed of the *non*audit path. And you just slowed it down unnecessarily." (2008-07-07, `alpine.LFD.1.10.0807070927090.11076@woody.linux-foundation.org`)
"The inexact matches should be a case of "make them correct". Screw performance." (2004-02-18, `Pine.LNX.4.58.0402181457470.18038@home.osdl.org`)

## 3. Keep cold code plain; make shared core primitives fast
**Severity:** rework      **Basis:** his words; transfer inferred
**Rule:** Code that is not hot (setup, config, CLI, admin paths, error paths) should be the simplest correct code.
Effort goes into the shared primitives everyone calls (logger, serializer, formatter, allocator), including their
generated code, so callers do not grow their own buggy fast paths. Efficiency comes first from data-structure shape.
**Look for:** size special cases or unchecked accessors in code run once; callers re-implementing a slow shared
helper; early-exit shortcuts in cold code that create subtle ordering rules.
**Why:** Rare code runs cold, so hot-loop tuning does not apply. A slow core primitive breeds workarounds, and the
workarounds carry bugs.
**Unless:** If cold code becomes hot, rewrite it then. For core code, reading compiler output is expected.
**He said:** "In random non-core code, I want people to write it clearly and maintainably. I very much do not want random drivers doing micro-optimizations etc." (2025-01-07, `CAHk-=whe12v6dDjhYcOcfHEorwZ90+cbzD1sKLRzNyB8CWsaPw@mail.gmail.com`)

## 4. Locking: remove contention by design; plain locks first; state lock order
**Severity:** rework      **Basis:** his words about kernel code, transfer inferred
**Rule:** A contended lock is a data-sharing problem: split the data, take only the one lock the common case needs,
keep locks next to their data, or delete the lock. Do not answer contention with a cleverer lock type. Prefer a
plain mutex to a reader-writer lock for short sections. When two locks of one kind can be held together, document the order.
**Look for:** one global mutex around a shared map or pool; a new adaptive, queued or RW lock to speed it up;
`RwLock` around a few non-blocking lines; locking two accounts or nodes with no stated order.
**Why:** Contention comes from bad locking plus benchmarks; the uncontended case is the common one. RW locks cost
more than plain ones and their parallelism mostly shows as extra cache-line bouncing.
**Unless:** RW locks suit long, truly parallel readers; fairness fixes are legitimate; read-mostly data can be
published by atomic pointer swap of immutable snapshots (the RCU pattern). Unlock order does not matter.
**He said:** "And contention pretty much happens in one situation, and one situation only: in a combination of (a) bad locking and (b) benchmarks." (2023-01-16, `CAHk-=whjFwzEq0u04=n=t7-kNJdX0HkAOjAMjmLXDDycJ+j9yQ@mail.gmail.com`)

## 5. Use a lock; lockless code needs a hot-path reason and paired, commented ordering
**Severity:** rework (reject hand-rolled lockless code with no measured need)      **Basis:** his words; language examples inferred
**Rule:** Default to a mutex, channel or library primitive. Lock-free code belongs only on a measured hot path,
built from standard patterns (release/acquire, snapshot publish, sequence counters), with every barrier commented
with what it pairs with. Atomics are not free: one locked instruction costs tens of cycles uncontended, so two
can cost more than a lock.
**Look for:**
- `Ordering::Relaxed`, `memory_order_*`, `volatile` or fences with no comment naming the other side; ordering on one side only.
- Hand-rolled flags, ring buffers or spin loops in place of a mutex, condvar or channel.
- Shared atomic counters or `Arc` clones on every request; prefer per-thread or sharded counters.
**Why:** People get ordering wrong both ways: too little breaks, too much is slow. He gets it wrong too.
**Unless:** He champions lockless code in core paths with large measured wins; under real contention an atomic add
can beat a lock.
**He said:** "End result: use a lock. Seriously. Anything else is going to be buggy, or going to be incredibly subtle." (2019-09-18, `CAHk-=wj85tOp8WjcUp6gwstp4Cg2WT=p209S=fOzpWAgqqQPKg@mail.gmail.com`)
"You can never do ordering on just one side." (2008-10-17, `alpine.LFD.2.00.0810171235310.3438@nehalem.linux-foundation.org`)

## 6. Passing tests prove nothing about a race
**Severity:** reject      **Basis:** his words; transfer direct
**Rule:** For concurrent code, ask what invariant prevents the bad interleaving and what enforces it. A race that
is hard to hit is still a bug, and the worst kind.
**Look for:** check-then-act on shared state outside the lock or refcount that guarantees it; a fast path safe only
because the other side is slow; *ran it for a week* or *the race detector is quiet* as the argument; assertions
that test the racy condition and so never fire.
**Why:** Such code works in testing and looks right, which is what makes it dangerous.
**Unless:** Racy reads for approximate statistics nobody relies on are fine.
**He said:** "It is a very dangerous pattern, because it likely works in practice during testing, and looks like it might work. But it is completely and unfixably wrong." (2020-08-05, `CAHk-=wg9dzJOkvysjgdHv5eFJU76EFAwCxNenRxTtq6VWof98Q@mail.gmail.com`)

## 7. A real performance regression is a bug; fast but wrong is worthless
**Severity:** reject (revert if merged)      **Basis:** his words; transfer direct
**Rule:** A measured slowdown on a real workload is a regression, and being merged is no defence. Do not wave away a
performance cost with a correctness or security concern nobody has. Equally, speed from skipping a needed check
or relying on undefined behaviour is not speed.
**Look for:** a throughput or p99 drop accepted because the change fixes something else; hardening on hot paths
with large cost and no threat model; fast paths that drop an invariant.
**Why:** Performance is a feature users notice.
**Unless:** Real correctness always wins. A regression no real workload shows can be left alone.
**He said:** "Performance is a feature too." (2008-05-07, `alpine.LFD.1.10.0805070800120.32269@woody.linux-foundation.org`)
"Speed doesn't matter for garbage." (2018-03-06, `CA+55aFy-imLQ9WeA880qR_DqKTpCiH2-3ou6_NScBGOKGE=-fQ@mail.gmail.com`)

## 8. Indirection on hot paths blocks optimisation; cache the common answer in front
**Severity:** rework on hot paths; not raised elsewhere      **Basis:** his words about kernel code, transfer inferred
**Rule:** Callbacks, vtables, trait objects and hook chains on a hot path cost more than the call: nothing can be
inlined or optimised across them. Keep the generic interface, but put a cache or flag in front so the common case
never calls down.
**Look for:** a trivial operation turned into dynamic dispatch; a callback per item where a loop would do; a hook
chain per request with no cheap *no hooks registered* check.
**Why:** A generic interface over many implementations cannot be fast itself; a cache in front of it can. Since
Spectre mitigations the indirect call is also expensive in itself.
**Unless:** Callbacks are fine when a loop would need complex conditionals, and off the hot path.
**He said:** "we can't do inlining, we can't optimize locking, we can't do anything clever." (2013-05-26, `CA+55aFyAW5tGqZA8kx7kMrMp0Zm0H1ohXVM4thZPOcnZeoosSg@mail.gmail.com`)

## 9. Count the memory the hot path touches
**Severity:** rework      **Basis:** his words about kernel code, transfer inferred
**Rule:** On cached hot paths, cost is cache lines touched and dependent loads chained. Keep the bit the fast path
needs on the object it already has. Objects that exist in millions must not grow casually. Do not force cache-line
alignment on types that are embedded or put in arrays.
**Look for:** `obj.ops.fn` or `obj.meta.x` loaded only to learn there is nothing to do; a new field on a per-row or
per-connection struct for one feature; `alignas(64)` or `#[repr(align(64))]` on embedded types.
**Why:** Even cached loads do not all fit in L1, so pointer chasing shows up in profiles on cached workloads.
**Unless:** Only for paths profiles show are hot; layout tricks cost maintenance. Rarely matters for I/O-bound services.
**He said:** "just the pointer chasing is expensive, especially since even cached loads aren't small enough to fit in L1." (2011-07-22, `alpine.LFD.2.02.1107221023170.29055@i5.linux-foundation.org`)

## 10. Scaling work must not slow the ordinary case
**Severity:** reject      **Basis:** his words about kernel code, transfer inferred
**Rule:** Changes for the largest deployments are welcome only if the typical one (one box, few cores) pays nothing
measurable. Ask for numbers on the typical deployment.
**Look for:** sharding, distributed caches, per-core structures or pools added to something that usually runs small.
**Why:** Single-thread performance still matters.
**Unless:** A tiny, unmeasurable single-thread cost is acceptable when it removes real contention.
**He said:** "So you're potentially making things worse for just about everybody, in order to fix a problem that almost nobody can actually see." (2013-02-13, `CA+55aFwxYK-BLH0crhySHaQvAYHOH-VGUi7WTd1aq-24+WTDYw@mail.gmail.com`)

## 11. Hot-path memory: small buffers inline, side-work out, small frames
**Severity:** rework      **Basis:** his words about kernel code, transfer inferred
**Rule:** For data that is usually small, use a fixed buffer for the common size and fall back to the heap. Keep
allocation side-work (accounting, hooks) off the hot path. Move rarely needed large locals into helpers so deep
call chains do not carry them. (Panicking on allocation failure belongs to the robustness reference.)
**Look for:** a heap allocation per item where `SmallVec`, an SSO string or a stack array covers the common case;
a large buffer in a function that also calls deep slow paths, or on small thread or ISR stacks.
**Why:** The stack buffer is enormously faster than an allocator call, and stack space is shared by the whole chain.
**Unless:** Kernel allocator policy (small allocations effectively never fail) is specific to the kernel's reclaim
design; never cite it as a reason to skip failure handling elsewhere.
**He said:** "it's, oh, about infinitely faster to do than to use kmalloc()." (2008-11-17, `alpine.LFD.2.00.0811171522030.18283@nehalem.linux-foundation.org`)

## Position changes
- Indirect calls: in 2002 he expected them to stay cheap; since Spectre (2018 on) he counts them among the main hot-path costs.
- Memory ordering: acquire/release is now his preferred form over separate read/write barrier pairs (2024).
- Transactional memory and software prefetch: once tried, now rejected as fixes; manuals do not reflect real CPUs, so ask for measurements.
