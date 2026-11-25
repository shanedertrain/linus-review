# Theme: performance, concurrency and memory (`perf`)

Mined from `corpus.db` for the `linus-review` skill. Every quote below is verbatim from Linus's own (unquoted) text and is listed in `analysis/perf.quotes.jsonl`. The verifier passes all of them. IDs are corpus document IDs; for lore mail the ID is the Message-ID.

**How to read this file.** There are 18 principles, roughly in the order a reviewer meets them: evidence (1 to 2), code shape on hot paths (3 to 8), concurrency (9 to 12), trade-offs (13 to 14), memory (15), scope (16 to 18). The single most transferable idea is that **every performance claim must name the workload and the profile, and every optimisation's complexity must be paid for by a measured gain on that workload**. Most of the other principles are consequences of it.

**Severity scale used below.** NAK or refuse < revert after merge. In practice: *revert* (shipped regression), *refuse or NAK* (won't merge until fixed or justified), *rework* (asks for a different shape, often writes it), *grumble and merge* (pulls with a public complaint).

## 1. Demand real numbers from real loads; a microbenchmark only locates a cost

**Principle.** An optimisation that adds complexity has to come with numbers from a workload someone actually runs. A microbenchmark is fine for finding where a cost lives or for checking that nothing got worse, but on its own it does not justify new complexity. "It may be faster" or "in theory this fixes things" counts as no evidence at all.

**What triggers it in a review.**
- A performance patch whose changelog has no numbers, or only cycle counts, a loop timing one call, or "this should help under load".
- Benchmarks that never touch the data (zero-copy, page flipping), that run on a RAM disk, or that hammer one object from every thread.
- A new lock type, allocator mode, cache or fast path that is justified by one synthetic test.
- Claims that a change will fix problems "we don't even know about".

**His reasoning.** A microbenchmark can show any improvement you like ("infinite TLB walk improvement"). Loads that skip the real costs (cache misses, page faults, data touching) produce "wonderful benchmark numbers" that never show up in use. The patch size and the added complexity are real, measurable costs; a hypothetical speedup is not. He also points out that a change can make unknown loads worse, so "it will help loads we haven't tested" cuts both ways.

**How serious.** Very. He NAKs ("I'm going to NAK these kinds of changes unless you can actually show real improvement on real loads", 2013), refuses complex features until real numbers arrive (THP 2010, qrwlock 2013), and pulls with a public complaint when the numbers are thin (io_uring zero-copy, 2022).

**Limits and exceptions.** This is not blanket contempt for microbenchmarks. He applies microbenchmark-driven patches when the effect is large and real: a 33% file-locking regression from accounting led him to say "those benchmarks do matter" (2024), and he applied a signal-path fix because "if you fix the details on all the microbenchmarks you find, eventually you probably do well on real loads too" (2020). He runs microbenchmarks himself (his `stat()`-in-a-loop and `make -j` on a built tree) to find hot spots, then checks them against real loads. The rule is about *justifying complexity*, not about which tool finds the problem. He also changes his mind when shown a real load: in 2025 he first called a many-threads-reading-one-page case "a completely unrealistic microbenchmark", then accepted it once "apparently there are real loads" (`CAHk-=wgy=oOSu+A3cMfVhBK66zdFsstDV3cgVO-=RF4cJ2bZ+A@mail.gmail.com`).

**Outside the kernel.** This applies directly. In a service, a library or firmware, ask for an end-to-end measurement (latency percentiles under production-shaped traffic, a real build, a real request mix) before accepting a cache layer, a lock-free queue, an object pool or a custom serializer. A micro-benchmark of one function is evidence of where time goes, not evidence that the change is worth its complexity.

**Evidence.**

- "I'm not interested in micro-benchmarks, either. I can show infinite TLB walk improvement in a microbenchmark."  
  `alpine.LFD.2.00.1004051326380.21411@i5.linux-foundation.org`, 2010-04-05, <https://lore.kernel.org/all/alpine.LFD.2.00.1004051326380.21411%40i5.linux-foundation.org/>
- "In order for me to be interested in any complex hugetlb crap, I want real numbers from real applications. Not "it takes this many cycles to walk a page table", or "it could matter under these circumstances"."  
  `alpine.LFD.2.00.1004051326380.21411@i5.linux-foundation.org`, 2010-04-05, <https://lore.kernel.org/all/alpine.LFD.2.00.1004051326380.21411%40i5.linux-foundation.org/>
- "Sorry, but I don't believe in "may be" as an excuse for complexity."  
  `CA+55aFwhX-6DzxKMPk=NTmSGt1GNHE6XTHZcss+Q=hC-epC7cQ@mail.gmail.com`, 2013-11-18, <https://lore.kernel.org/all/CA%2B55aFwhX-6DzxKMPk%3DNTmSGt1GNHE6XTHZcss%2BQ%3DhC-epC7cQ%40mail.gmail.com/>
- "Right now, the real numbers I can point to is in the size of the patch, and the extra code complexity. Yes, I see the microbenchmark numbers, but those are pretty much irrelevant to real loads."  
  `CA+55aFwhX-6DzxKMPk=NTmSGt1GNHE6XTHZcss+Q=hC-epC7cQ@mail.gmail.com`, 2013-11-18, <https://lore.kernel.org/all/CA%2B55aFwhX-6DzxKMPk%3DNTmSGt1GNHE6XTHZcss%2BQ%3DhC-epC7cQ%40mail.gmail.com/>
- "A lot of the wonderful benchmark numbers are based on loads that carefully don't touch the data on either the sender or receiver side, and that get perfect behavior from a performance standpoint as a result, but don't actually do anything remotely realistic in the process."  
  `CAHk-=wjh91hcEix55tH7ydTLHbcg3hZ6SaqgeyVscbYz57crfQ@mail.gmail.com`, 2022-08-02, <https://lore.kernel.org/all/CAHk-%3Dwjh91hcEix55tH7ydTLHbcg3hZ6SaqgeyVscbYz57crfQ%40mail.gmail.com/>
- "Don't optimize based off profiles of micro-benchmarks on made up platforms. That's for seeing where the limits are."  
  `CAHk-=wgVPHPPjZPoV8E_q59L7i8zFjHo_5hHo_+qECYuy7FF6g@mail.gmail.com`, 2024-02-25, <https://lore.kernel.org/all/CAHk-%3DwgVPHPPjZPoV8E_q59L7i8zFjHo_5hHo_%2BqECYuy7FF6g%40mail.gmail.com/>
- "That said, those benchmarks do matter. It's very easy to say "not relevant in the big picture" and then the end result is that everything is a bit of a pig."  
  `CAHk-=wg_CoTOfkREgaQQA6oJ5nM9ZKYrTn=E1r-JnvmQcgWpSg@mail.gmail.com`, 2024-01-17, <https://lore.kernel.org/all/CAHk-%3Dwg_CoTOfkREgaQQA6oJ5nM9ZKYrTn%3DE1r-JnvmQcgWpSg%40mail.gmail.com/>
- "If you fix the details on all the microbenchmarks you find, eventually you probably do well on real loads too.."  
  `CAHk-=wisa2xZHaCV=kh3seU-1kFDTjyWW9Ak3w5HH8nDvv7Snw@mail.gmail.com`, 2020-02-25, <https://lore.kernel.org/all/CAHk-%3Dwisa2xZHaCV%3Dkh3seU-1kFDTjyWW9Ak3w5HH8nDvv7Snw%40mail.gmail.com/>
- "Seriously. I'm going to NAK these kinds of changes unless you can actually show real improvement on real loads. No more of this "in theory this will fix all our problems" crap."  
  `CA+55aFwxYK-BLH0crhySHaQvAYHOH-VGUi7WTd1aq-24+WTDYw@mail.gmail.com`, 2013-02-13, <https://lore.kernel.org/all/CA%2B55aFwxYK-BLH0crhySHaQvAYHOH-VGUi7WTd1aq-24%2BWTDYw%40mail.gmail.com/>

**How well supported.** About 45 messages read that make this argument, 2001 to 2026 (THP 2010, qrwlock 2013, spinlock out-of-line 2013, readahead 2015, LKP regressions 2018 to 2024, buffered-IO limits 2024, filemap 2026). Strongly supported; the position is stable across eras.

## 2. Benchmark under the conditions that matter: cold caches, aged systems, real data

**Principle.** A number only counts if it was measured the way the code will run. Kernel and system code usually runs with a cold I-cache, cold branch predictors and memory already full of other data. Hot-loop benchmarks hide code-size, branch-layout and cache-pollution costs, so they systematically favour bigger, more "clever" code.

**What triggers it in a review.**
- Timing a function by calling it a million times in a loop, then claiming a win for code that is larger or that adds a table.
- Measuring a memory feature right after boot, or measuring I/O on a RAM disk.
- A single run with no indication of variance; small differences claimed from noisy numbers.
- Unrolling, larger inlines or lookup tables justified only by hot-cache timings.

**His reasoning.** "Being smaller automatically means faster if you're cold-cache"; a byte of code can cost about a cycle once you count I-cache misses. Hot-cache benchmarks also predict branches perfectly, so they hide static mispredicts. For hugepages, the "right after boot" case is pointless because the hard part is finding contiguous memory on an aged system. Benchmarks that do something nobody does are "worse than worthless" because they push people toward bad decisions.

**How serious.** Usually a request for better numbers rather than a hard NAK, but bad methodology is enough for him to discount a result completely and, in the splice/page-flipping case, to warn people off the whole approach.

**Limits and exceptions.** He accepts that cold-cache effects are hard to measure and settles for "microbenchmarks don't show any noticeable _worse_ behaviour, and code size went down by 10%" (`Pine.LNX.4.64.0601041356200.3668@g5.osdl.org`, 2006). Where the change is obviously right (removing `rep scas`), he applies it without cold-cache numbers.

**Outside the kernel.** Applies directly. Benchmark with realistic heap sizes, concurrent noise and cold starts (serverless cold starts, first request after deploy, firmware wake from sleep). Distrust JMH-style or `criterion` loops for code that runs once per request among many other things. Report variance and run more than once.

**Evidence.**

- "trivially: code/data size. Being smaller automatically means faster if you're cold-cache."  
  `Pine.LNX.4.58.0507281146290.3307@g5.osdl.org`, 2005-07-28, <https://lore.kernel.org/all/Pine.LNX.4.58.0507281146290.3307%40g5.osdl.org/>
- "So hot-cache may look very different indeed - the "normal" case might be that you mispredict all the time because the static prediction is wrong, but then a hot-cache benchmark will predict perfectly."  
  `Pine.LNX.4.58.0507281146290.3307@g5.osdl.org`, 2005-07-28, <https://lore.kernel.org/all/Pine.LNX.4.58.0507281146290.3307%40g5.osdl.org/>
- "Icache issues can overcome any cycle gains, and do not show up well in benchmarks (benchmarks tend to have very hot icaches)."  
  `Pine.LNX.4.31.0104201037580.5523-100000@penguin.transmeta.com`, 2001-04-20, <https://lore.kernel.org/all/Pine.LNX.4.31.0104201037580.5523-100000%40penguin.transmeta.com/>
- "The "right after boot" case is totally pointless, since a huge part of hugetlb entries is the ability to allocate those physically contiguous and well-aligned regions."  
  `alpine.LFD.2.00.1004051326380.21411@i5.linux-foundation.org`, 2010-04-05, <https://lore.kernel.org/all/alpine.LFD.2.00.1004051326380.21411%40i5.linux-foundation.org/>
- "It's often better to try to find a real load where that particular sequence is important enough to be measurable at all, and then try the alternatives. Not perfect either, but if you can't find such a load, maybe you shouldn't be doing it in the first place.."  
  `Pine.LNX.4.64.0606211022300.5498@g5.osdl.org`, 2006-06-21, <https://lore.kernel.org/all/Pine.LNX.4.64.0606211022300.5498%40g5.osdl.org/>
- "So please don't ever benchmark things that don't make sense, and then use the numbers as any kind of reason to do anything. It's worse than worthless."  
  `alpine.LFD.2.00.1005201043321.23538@i5.linux-foundation.org`, 2010-05-20, <https://lore.kernel.org/all/alpine.LFD.2.00.1005201043321.23538%40i5.linux-foundation.org/>

**How well supported.** About 15 messages, 2001 to 2024 (inline rule 2001, find_first_bit 2005, code size 2006, vgetcpu 2006, THP 2010, splice 2010, clear_user 2022). Well supported, though spread across the early and middle eras.

## 3. Optimise for the common case: keep the fast path short and push everything else out of line

**Principle.** Find the case that actually happens most (usually: uncontended, cached, feature disabled, small input) and make that path short, straight-line and dense. Features, rare conditions and error handling go behind one well-predicted test into an out-of-line slow path. Someone who wants a feature to be fast must not slow down everyone who doesn't use it.

**What triggers it in a review.**
- New tests, flag checks or slow instructions added to a hot path for an optional feature (audit, tracing, security hooks, debug accounting).
- A function where the common case and the rare case are interleaved, with a big stack frame needed only by the rare case.
- Expensive general-purpose computation (`fls64`, 64-bit divides) done unconditionally when the common inputs fit a trivial case.

```c
/* what he asks for: test once, bail to the rare case out of line */
if (unlikely((stime | total | rtime) >> 32))
        return uncommon_case(stime, total, rtime);
return div_u64((u64)(u32)stime * rtime, total);   /* the 99% case */
```

**His reasoning.** On hot paths "the only thing that matters is cache misses and mispredicted branches", so an extra test or touched cacheline in the fast path is paid by every call. Rare cases are going to be slow anyway ("Go Slow" mode), so making them a bit slower costs nothing. Mixing rare-case code into the fast path also bloats the frame and the I-cache footprint of the common path (the `avc_audit` split, 2012).

**How serious.** He asks for a rework ("Please don't do it like this", 2008 audit) and often writes the restructured version himself. He calls the 2024 fsnotify design a "complete mis-design" over this.

**Limits and exceptions.** The reverse also holds: uncommon paths should be *simple*, not optimised. "make them correct. Screw performance. And tell people that they are slower" (2004, case-insensitive lookups). He accepts a slower rare case outright. He also asks whether the presumed common case really is common before optimising for it ("is the !IS_POSIXACL() actually a common situation worth optimizing for?", `CAHk-=wh-Bom_pGKK+-=6FAnJXNZapNnd334bVcEsK2FSFKthhg@mail.gmail.com`, 2024).

**Outside the kernel.** Applies directly: request handlers where auth, tracing, feature flags or metrics add work to every request; parsers where the ASCII or small-input path should be a tight loop with a fallback; firmware ISRs that should do the minimum and defer the rest. Check that the disabled-feature path costs one cheap test.

**Evidence.**

- "I realize that Fedora enables audit by default, and that you care about the speed of the audit path, but I care about the speed of the *non*audit path. And you just slowed it down unnecessarily."  
  `alpine.LFD.1.10.0807070927090.11076@woody.linux-foundation.org`, 2008-07-07, <https://lore.kernel.org/all/alpine.LFD.1.10.0807070927090.11076%40woody.linux-foundation.org/>
- "Please don't add more instructions to the fastpath."  
  `alpine.LFD.1.10.0807070927090.11076@woody.linux-foundation.org`, 2008-07-07, <https://lore.kernel.org/all/alpine.LFD.1.10.0807070927090.11076%40woody.linux-foundation.org/>
- "So let's re-think the whole thing entirely. First, let's throw away the uncommon case, and we'll come back to it later:"  
  `CA+55aFway4C89fTewKvED4RvFLaNdM-BVtkJ2YChsvracLKiyA@mail.gmail.com`, 2013-04-11, <https://lore.kernel.org/all/CA%2B55aFway4C89fTewKvED4RvFLaNdM-BVtkJ2YChsvracLKiyA%40mail.gmail.com/>
- "Finally, mark the tests properly likely/unlikely, so that the common fast-paths are dense in the instruction stream."  
  `8aab6a27332bbf2abfcb35224738394e784d940b`, 2013-09-08, <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=8aab6a27332bbf2abfcb35224738394e784d940b>
- "And even ignoring the "common case" issue, that's the one you want to OPTIMIZE for. That's the case that matters for performance, because clearly if there are content watches, you're going to go into "Go Slow" mode anyway and not do pre-fetching."  
  `CAHk-=wj8L=mtcRTi=NECHMGfZQgXOp_uix1YVh04fEmrKaMnXA@mail.gmail.com`, 2024-11-11, <https://lore.kernel.org/all/CAHk-%3Dwj8L%3DmtcRTi%3DNECHMGfZQgXOp_uix1YVh04fEmrKaMnXA%40mail.gmail.com/>
- "The inexact matches should be a case of "make them correct". Screw performance. And tell people that they are slower."  
  `Pine.LNX.4.58.0402181457470.18038@home.osdl.org`, 2004-02-18, <https://lore.kernel.org/all/Pine.LNX.4.58.0402181457470.18038%40home.osdl.org/>

**How well supported.** About 30 messages and commits, 2001 to 2025 (rwsem 2001, syscall 2002, audit 2008, AIM7 2008, cputime 2013, dput 2013, avc_audit 2012, fsnotify 2024, permission 2024 to 2025). Strongly supported and stable.

## 4. Count cache misses: keep the hot path's data footprint small and avoid pointer chases

**Principle.** On cached paths, cost is dominated by how many distinct cachelines you touch and how many dependent loads you chain. Put the bits the hot path needs into the object it already has (flags in the inode or dentry) instead of dereferencing through `ops`, `security` or `private` pointers. Avoid touching a cacheline just to check something you could have recorded as a bit.

**What triggers it in a review.**
- Hot code that does `obj->ops->fn` or `obj->sec->field` just to find out whether there's anything to do.
- A check that reads a list head or a separate structure only to learn a boolean.
- Hash tables or linked structures with poor locality on a lookup path, where an array or a batched list would do.

```c
/* VFS trick he cites: cache "no special permission op" as a flag in the inode,
   so the common case never loads inode->i_op at all */
if (unlikely(!(inode->i_opflags & IOP_FASTPERM))) { ... }
return generic_permission(idmap, inode, mask);
```

**His reasoning.** "Even cached loads aren't small enough to fit in L1", so a pointer chase costs real time even when nothing goes to memory. Every extra D$ line in the common path adds up over every path-component lookup. The flag tricks are "extreme", but they matter "exactly because it keeps the D$ footprint smaller".

**How serious.** He writes these patches himself (the 2011 `i_op` access removal, the 2013 `dput` reorganisation, moving the SELinux SID into the inode). In review he asks for the restructure. He grumbles at, but tolerates, subsystems (security) that keep pointer chasing he can't remove.

**Limits and exceptions.** This applies to *hot* paths shown by profiles; he doesn't ask for it elsewhere. He disliked his own SELinux-fields-in-inode patch as "not a cleanup" because it special-cases one security model (`CA+55aFw_ic=4OvH0Ys2CUjgotdbfdbuxUsx77RYEYPGrbqzbAA@mail.gmail.com`, 2013). Layout tricks have a maintainability cost he weighs.

**Outside the kernel.** Transfers to any hot loop: struct-of-arrays versus array-of-structs, avoiding `Box`/`Rc`/object-graph chasing in inner loops, caching a "nothing to do" bit on the object, keeping the per-request context compact. In GC'd languages the same reasoning applies to object indirections and boxing. For a typical web service where I/O dominates it matters much less, and a reviewer should say so.

**Evidence.**

- "So on a VFS level, to a very close approximation, the only thing that matters is cache misses and mispredicted branches."  
  `CAHk-=wh9hc8sSNYwurp5cm2ub52yHYGfXC8=BfhuR3XgFr0vEA@mail.gmail.com`, 2024-11-11, <https://lore.kernel.org/all/CAHk-%3Dwh9hc8sSNYwurp5cm2ub52yHYGfXC8%3DBfhuR3XgFr0vEA%40mail.gmail.com/>
- "Is this an extreme example? Yes. But the whole i_opflags kind of thing does end up mattering, exactly because it keeps the D$ footprint smaller."  
  `CAHk-=wh9hc8sSNYwurp5cm2ub52yHYGfXC8=BfhuR3XgFr0vEA@mail.gmail.com`, 2024-11-11, <https://lore.kernel.org/all/CAHk-%3Dwh9hc8sSNYwurp5cm2ub52yHYGfXC8%3DBfhuR3XgFr0vEA%40mail.gmail.com/>
- "They did show up very clearly in profiles, even when the load is mostly cached - just the pointer chasing is expensive, especially since even cached loads aren't small enough to fit in L1."  
  `alpine.LFD.2.02.1107221023170.29055@i5.linux-foundation.org`, 2011-07-22, <https://lore.kernel.org/all/alpine.LFD.2.02.1107221023170.29055%40i5.linux-foundation.org/>
- "This is exactly what we have d_flags for, so that we can avoid touching extra cache lines for the common case."  
  `8aab6a27332bbf2abfcb35224738394e784d940b`, 2013-09-08, <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=8aab6a27332bbf2abfcb35224738394e784d940b>

**How well supported.** About 20 messages and commits, 2003 to 2025 (dcache hash 2003, i_op removal 2011, dput 2013, i_security 2013, VFS 2024). Well supported, concentrated in his VFS work.

## 5. Size-critical structures: don't grow them, don't force alignment on embedded ones, place fields by access pattern

**Principle.** Structures that exist once per page, inode or dentry are size-critical: every byte is multiplied by millions and makes cache misses worse. Don't add fields casually. Don't put `____cacheline_aligned` on structures (or members) that get embedded in other structures; it forces padding and alignment the container can't honour. Lay fields out by who touches them: things read or written under a lock can share the lock's cacheline; things touched independently by other CPUs should not.

**What triggers it in a review.**
- A new field in a per-object structure "just for" one feature.
- `____cacheline_aligned_in_smp` on a member of a structure that is itself embedded or on the stack.
- Locks or counters in size-critical objects that grow in size.
- "Read-mostly" comments used to justify a layout without saying who reads it, and under which lock.

**His reasoning.** "struct page" is "one of our biggest memory users" and its cache miss "tends to be one of the biggest problems in managing memory". Forced alignment on embedded structs "forces not only a potentially huge amount of padding" but also alignment the container won't have. Layout rules are subtle: fields read only under a lock belong with the lock, while fields hammered without it should be away from it.

**How serious.** He calls growing `struct page` by a big fraction of a percent "absolutely unacceptable" (2012) and says misplaced alignment in bcachefs's VFS changes is "not acceptable" (2019). For layout regressions found by test bots he usually asks the people who see the regression to do the re-layout, with comments.

**Limits and exceptions.** He won't add alignment to fix a layout-sensitive regression in an embedded structure (inode, 2019), preferring to repack fields. Some regressions are "really random memory layout" effects that he declines to chase (`CAHk-=wi1KcOZo4JeRDgJCU0gB5v16q6GJsFtF365MSfM8hH3zA@mail.gmail.com`, 2021). He does accept bigger sizes where there's a reason, for example not over-packing PFN bits (2015).

**Outside the kernel.** Transfers to anything allocated in large numbers: ECS components, packet descriptors, database row headers, per-connection state, embedded RAM-constrained structs. Check `sizeof`, padding and field order. Be suspicious of `alignas(64)` or `#[repr(align(64))]` on types that are embedded or put in arrays. For a typical CRUD service this does not apply.

**Evidence.**

- "Our "struct page" is one of our biggest memory users, there's no way we should cavalierly make it even bigger."  
  `CA+55aFwmhM2a2HjB_MEjVDDL-AP4j-t202ozmHgT0azSptjnoA@mail.gmail.com`, 2012-05-29, <https://lore.kernel.org/all/CA%2B55aFwmhM2a2HjB_MEjVDDL-AP4j-t202ozmHgT0azSptjnoA%40mail.gmail.com/>
- "It's also a huge performance sink, the cache miss on struct page tends to be one of the biggest problems in managing memory."  
  `CA+55aFwmhM2a2HjB_MEjVDDL-AP4j-t202ozmHgT0azSptjnoA@mail.gmail.com`, 2012-05-29, <https://lore.kernel.org/all/CA%2B55aFwmhM2a2HjB_MEjVDDL-AP4j-t202ozmHgT0azSptjnoA%40mail.gmail.com/>
- "So I would suggest we *not* do cacheline alignment, because it will result in random padding."  
  `CAHk-=whn+F+vFgCR0a04atTQuBmXhq0oU1Y1f0YqMiUFHj28JQ@mail.gmail.com`, 2019-02-26, <https://lore.kernel.org/all/CAHk-%3Dwhn%2BF%2BvFgCR0a04atTQuBmXhq0oU1Y1f0YqMiUFHj28JQ%40mail.gmail.com/>
- "which is completely bogus, since that forces not only a potentially huge amount of padding, it also requires alignment that that struct simply fundamentally does not have, and _will_ not have."  
  `CAHk-=wi0iMHcO5nsYug06fV3-8s8fz7GDQWCuanefEGq6mHH1Q@mail.gmail.com`, 2019-06-10, <https://lore.kernel.org/all/CAHk-%3Dwi0iMHcO5nsYug06fV3-8s8fz7GDQWCuanefEGq6mHH1Q%40mail.gmail.com/>
- "Even if they are mostly read-only, if they are only read *under* the lock (because the lock still is what serializes them), then putting them in the same cacheline as the lock certainly won't hurt."  
  `CAHk-=wiyjnKiCZyou+fHYi7tNh1FC-BYy_kubusd+jrkDRsExA@mail.gmail.com`, 2022-05-12, <https://lore.kernel.org/all/CAHk-%3DwiyjnKiCZyou%2BfHYi7tNh1FC-BYy_kubusd%2BjrkDRsExA%40mail.gmail.com/>
- "We have them in size-conscious data structures like "struct dentry" and "struct page", and they really must not be bigger than an "int" in the non-debug case."  
  `CA+55aFyteA526MZHpzYTo1XoMx772FrRoqc_keODx1TfxDx6Fw@mail.gmail.com`, 2013-06-11, <https://lore.kernel.org/all/CA%2B55aFyteA526MZHpzYTo1XoMx772FrRoqc_keODx1TfxDx6Fw%40mail.gmail.com/>

**How well supported.** About 15 messages, 2002 to 2022 (struct page 2002 and 2012, spinlock size 2013, inode 2019, address_space 2019, zone padding 2022, mmap_sem 2021). Well supported.

## 6. Indirection on hot paths costs more than the call: it blocks optimisation. Put a generic cache in front of it

**Principle.** Indirect calls (function pointers, vtables, ops structures, callbacks) on hot paths are expensive. Since Spectre the call itself is costly, but the deeper cost is that calling into "lower-level non-generic code" stops inlining, locking optimisation and anything clever. The fix he uses repeatedly: keep the polymorphic interface, but put a generic cache or flag in front of it so the hot path rarely calls down at all.

**What triggers it in a review.**
- A trivial operation turned into one or two indirect calls (the `->poll_mask` conversion).
- A callback-per-item API where a plain loop would do.
- A generic dispatch layer (security hooks, filesystem ops, plugin interfaces) on every lookup with no caching of the common answer.
- Compiler output that turns a two-way `if` into an indirect call through a register.

**His reasoning.** "It's simply not possible to have a generic interface to 50+ different filesystems and expect that kind of generic interface to be high-performance", but a cache in front of it can be made to "go fast like a bat out of hell". That is how the dentry cache, page cache and cached ACLs work.

**How serious.** He reverted the `->poll()` conversion in 2018 partly for this ("a huge performance regression"). He objects to function pointers in performance-critical code like `vsnprintf` (2024).

**Limits and exceptions.** *Change over time.* In 2002 he expected predictable indirect calls to stay cheap because they are "very common, and to some degree getting _more_ so with the proliferation of OO languages". After 2018 (retpolines) he treats them as one of the three things that matter on hot paths. He still endorses callbacks where the alternative is worse: page-table walkers keep the "walk over range using this set of callbacks" interface because a loop would need "magic complex conditionals" (2019). He is in favour of OO-style interfaces in C (VFS is "a object model"), as long as the indirection is explicit (`alpine.LFD.0.999.0709230911360.16478@woody.linux-foundation.org`, 2007).

**Outside the kernel.** Transfers to any hot path: virtual dispatch in C++, trait objects (`dyn Trait`) in Rust inner loops, middleware chains, plugin hooks per request, ORMs calling through layers per row. The transferable move is caching the common answer (permission results, resolved handlers, "no hooks registered" flags) ahead of the generic layer. In code that is not hot, ignore this.

**Evidence.**

- "The indirect calls are expensive, but they are expensive not because an indirect call itself is particularly expensive (although that's true on some architectures too), but because the whole notion of "I'm calling down to the lower-level non-generic code" means that we can't do inlining, we can't optimize locking, we can't do anything clever."  
  `CA+55aFyAW5tGqZA8kx7kMrMp0Zm0H1ohXVM4thZPOcnZeoosSg@mail.gmail.com`, 2013-05-26, <https://lore.kernel.org/all/CA%2B55aFyAW5tGqZA8kx7kMrMp0Zm0H1ohXVM4thZPOcnZeoosSg%40mail.gmail.com/>
- "It's simply not possible to have a generic interface to 50+ different filesystems and expect that kind of generic interface to be high-performance - but when we've been able to abstract it out as a cache in front of the filesystem operations, it is suddenly quite reasonable to spend a lot of effort making that cache go fast like a bat out of hell."  
  `CA+55aFyAW5tGqZA8kx7kMrMp0Zm0H1ohXVM4thZPOcnZeoosSg@mail.gmail.com`, 2013-05-26, <https://lore.kernel.org/all/CA%2B55aFyAW5tGqZA8kx7kMrMp0Zm0H1ohXVM4thZPOcnZeoosSg%40mail.gmail.com/>
- "(Indirect calls have always had some overhead, and Spectre made it much worse, so arguably indirect calls have become the third thing that matters)."  
  `CAHk-=wh9hc8sSNYwurp5cm2ub52yHYGfXC8=BfhuR3XgFr0vEA@mail.gmail.com`, 2024-11-11, <https://lore.kernel.org/all/CAHk-%3Dwh9hc8sSNYwurp5cm2ub52yHYGfXC8%3DBfhuR3XgFr0vEA%40mail.gmail.com/>
- "Loops are certainly simpler than callbacks for most cases (and often faster because you don't have indirect calls which now are getting quite expensive)"  
  `CAHk-=wgUO5hWJmMT7r8aCzP7DOkg9ADkv6AzZ=SrKLOoKxzD_g@mail.gmail.com`, 2019-08-07, <https://lore.kernel.org/all/CAHk-%3DwgUO5hWJmMT7r8aCzP7DOkg9ADkv6AzZ%3DSrKLOoKxzD_g%40mail.gmail.com/>
- "They also caused a huge performance regression, because "->poll()" was no longer a trivial file operation that just called down to the underlying file operations, but instead did at least two indirect calls."  
  `a11e1d432b51f63ba698d044441284a661f01144`, 2018-06-28, <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=a11e1d432b51f63ba698d044441284a661f01144>
- "That's because indirect calls are actually very common, and to some degree getting _more_ so with the proliferation of OO languages"  
  `Pine.LNX.4.44.0212191519260.6279-100000@penguin.transmeta.com`, 2002-12-19, <https://lore.kernel.org/all/Pine.LNX.4.44.0212191519260.6279-100000%40penguin.transmeta.com/>

**How well supported.** About 20 messages and commits, 2002 to 2024 (sys_indirect 2007, check_acl 2009, VFS 2013, retpoline 2018, poll revert 2018, DMA 2018, walkers 2019, iov_iter 2020 and 2023, VFS 2024). Well supported, with a dated change of position.

## 7. Inline only the small fast path or what folds away; everything else goes out of line

**Principle.** `inline` is not a speed switch. Inline the tiny fast case, and functions whose constant arguments let most of the body fold away. Keep fallbacks, slow paths and anything sizeable out of line. Code that isn't performance critical has no business being a big inline in a header. If it is critical, show profiles.

**What triggers it in a review.**
- Large `static inline` helpers in widely included headers, or inline wrappers that contain a real call anyway.
- A "performance" series that is 90% inline functions with special cases for small sizes and no profile.
- Inlining an entire function when only its first test is hot.
- Inlined slow paths pulling large stack frames into hot callers.

**His reasoning.** "the *big* wins from doing inlines are if it allows the call-site to do more optimizations ... or if the lack of any function call at all allows the caller to do better register allocation around it." If the inline still contains a call, neither happens. I-cache costs "can overcome any cycle gains, and do not show up well in benchmarks". The 2001 rule of thumb: no inlines where the inline code is more than twice the out-of-line code.

**How serious.** Mostly grumbling and asks to rework ("I pulled this, but honestly, this part was *GARBAGE*", 2018, an unimportant inline in a core header). Firm on the 2024 `find_atomic` series: profiles or no special cases.

**Limits and exceptions.** He wants `__always_inline` where the compiler must not out-of-line (asm-heavy helpers, user-access regions, constant-folded bit helpers), because gcc "will randomly not inline things" (2016). *Change over time:* in 2009 he argued that kernel `inline` should keep meaning "always inline" and that gcc's own inlining heuristics were broken, especially "single call-site static function" inlining that bloats stack frames (2008). He wants both less inlining *and* reliable inlining where asked.

**Outside the kernel.** Transfers to C, C++ and Rust (`#[inline(always)]` abuse, header-only bloat), and partly to JIT languages (method size limits for inlining). Ask: is this function hot? Does inlining remove work, or just copy a call? Is the binary or WASM size budget relevant (firmware, front-end bundles)?

**Evidence.**

- "We should avoid any inlines where the inline code is >2* the out-of-line code."  
  `Pine.LNX.4.31.0104201037580.5523-100000@penguin.transmeta.com`, 2001-04-20, <https://lore.kernel.org/all/Pine.LNX.4.31.0104201037580.5523-100000%40penguin.transmeta.com/>
- "I want to keep the _fast_ case in-line."  
  `Pine.LNX.4.31.0104201037580.5523-100000@penguin.transmeta.com`, 2001-04-20, <https://lore.kernel.org/all/Pine.LNX.4.31.0104201037580.5523-100000%40penguin.transmeta.com/>
- "the *big* wins from doing inlines are if it allows the call-site to do more optimizations (eg conditionals or calculations that just go away if inlined with constant arguments, for example), or if the lack of any function call at all allows the caller to do better register allocation around it."  
  `alpine.LFD.1.10.0806221532560.2926@woody.linux-foundation.org`, 2008-06-22, <https://lore.kernel.org/all/alpine.LFD.1.10.0806221532560.2926%40woody.linux-foundation.org/>
- "because either performance really matters, in which case you need to show profiles, or performance doesn't matter, in which case it damn well shouldn't have special cases for small bitsets that double the size of the code."  
  `CAHk-=wjv-DkukaKb7f04WezyPjRERp=xfxv34j5fA8cDQ_JudA@mail.gmail.com`, 2024-06-20, <https://lore.kernel.org/all/CAHk-%3Dwjv-DkukaKb7f04WezyPjRERp%3Dxfxv34j5fA8cDQ_JudA%40mail.gmail.com/>
- "So I think you'd actually be better off with *just* the IOP_USERNS patch, and only inlining *that* fast-path case, and keep the other cases out-of"  
  `CAHk-=wgt5Lw7q_VAHgEC+HT4d5iJos6_shnyOnNBQeT0qrJSXw@mail.gmail.com`, 2025-04-16, <https://lore.kernel.org/all/CAHk-%3Dwgt5Lw7q_VAHgEC%2BHT4d5iJos6_shnyOnNBQeT0qrJSXw%40mail.gmail.com/>
- "Size matters, but size matters mainly from an I$ standpoint, not from some absolute 'big is bad" issue."  
  `CA+55aFywCXk083w78cQGbRKh-ERLtE8v9PZhqxaHcyHJxSNsFQ@mail.gmail.com`, 2015-05-15, <https://lore.kernel.org/all/CA%2B55aFywCXk083w78cQGbRKh-ERLtE8v9PZhqxaHcyHJxSNsFQ%40mail.gmail.com/>

**How well supported.** About 25 messages, 2001 to 2025 (rwsem 2001, inline semantics 2008 and 2009, git 2008, stack frames 2008, usercopy 2016, powerpc 2018, find_atomic 2024, mnt_idmapping 2025). Well supported.

## 8. For hot core code, read the generated code; for everything else, write it plainly

**Principle.** When a function shows up high in profiles, look at what the compiler produced: stack frame setup, register spills, calling conventions, unexpected indirect calls, unrolling. Fix the source so the compiler "doesn't even have the option to screw it up". Do this in *core* code that everyone uses. In ordinary driver or application code, he wants clear, maintainable code and no micro-optimisation.

**What triggers it in a review.**
- A change to a hot core primitive with no look at the code generation.
- Callers working around a slow core helper with their own special-case versions (the `seq_put_decimal_ull_width()` story).
- Macros or annotations that make the `.s` output unreadable (his 2025 NAK of a `WARN` implementation).
- Compiler behaviour that blows up function size "for no gain".

**His reasoning.** "when core code works badly, the end result is badness": people avoid the slow primitive and write buggy special cases, "so bad performance results in actual BUGGY CODE". Performance needs all three levels: good source and data structures, a compiler that cleans up abstraction-induced "stupid" code, and sane hardware.

**How serious.** He does this work himself (`stat` cleanups 2012, `vsnprintf` 2024). He NAKs changes that make assembly output unreadable (2025) and files compiler bugs with reduced test cases (clang unrolling 2021).

**Limits and exceptions.** He explicitly says where it doesn't apply: "In random non-core code, I want people to write it clearly and maintainably." About a clang code-size problem he says "this function *really* doesn't matter from a performance standpoint on its own"; the worry was the compiler pattern, not that function.

**Outside the kernel.** Translates as: optimise the shared primitive (the logger, the serializer, the allocator, the router, the ORM's hot query path) so that application code doesn't grow ad-hoc fast paths. Look at compiler output (Godbolt, `cargo asm`, JIT disassembly, bytecode) for those primitives only. Reject micro-optimisations in leaf business logic.

**Evidence.**

- "So my vsnprintf branch was literally written with me looking at the resulting assembler too, because when core code works badly, the end result is badness."  
  `CAHk-=whe12v6dDjhYcOcfHEorwZ90+cbzD1sKLRzNyB8CWsaPw@mail.gmail.com`, 2025-01-07, <https://lore.kernel.org/all/CAHk-%3Dwhe12v6dDjhYcOcfHEorwZ90%2BcbzD1sKLRzNyB8CWsaPw%40mail.gmail.com/>
- "In random non-core code, I want people to write it clearly and maintainably. I very much do not want random drivers doing micro-optimizations etc."  
  `CAHk-=whe12v6dDjhYcOcfHEorwZ90+cbzD1sKLRzNyB8CWsaPw@mail.gmail.com`, 2025-01-07, <https://lore.kernel.org/all/CAHk-%3Dwhe12v6dDjhYcOcfHEorwZ90%2BcbzD1sKLRzNyB8CWsaPw%40mail.gmail.com/>
- "so bad performance results in actual BUGGY CODE."  
  `CAHk-=whe12v6dDjhYcOcfHEorwZ90+cbzD1sKLRzNyB8CWsaPw@mail.gmail.com`, 2025-01-07, <https://lore.kernel.org/all/CAHk-%3Dwhe12v6dDjhYcOcfHEorwZ90%2BcbzD1sKLRzNyB8CWsaPw%40mail.gmail.com/>
- "This is another result of me looking at code generation of functions that show up high on certain kernel profiles, and just going "Oh, let's just clean that up"."  
  `8c12fec90c54cfabdd57b2726a1defbc07c19a55`, 2012-05-21, <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=8c12fec90c54cfabdd57b2726a1defbc07c19a55>
- "spend the time at a source code level: make it reasonably easy for the compiler to generate good code, and use the right algorithms at a higher level (and order structures etc so that they have good cache behaviour)."  
  `alpine.LFD.0.999.0708241025430.25853@woody.linux-foundation.org`, 2007-08-24, <https://lore.kernel.org/all/alpine.LFD.0.999.0708241025430.25853%40woody.linux-foundation.org/>
- "but the worry is just that the kernel really doesn't want a compiler that blows up functions by this kind of big factor for no gain."  
  `CAHk-=wjVuxnqQXSP53zBtTN-o8k4tcvFtVi=AkYt+KAuc5KNOg@mail.gmail.com`, 2021-08-28, <https://lore.kernel.org/all/CAHk-%3DwjVuxnqQXSP53zBtTN-o8k4tcvFtVi%3DAkYt%2BKAuc5KNOg%40mail.gmail.com/>

**How well supported.** About 20 messages and commits, 2005 to 2025 (stat cleanups 2012, acl_permission_check 2011, CSE 2007, clang 2021 to 2022, vsnprintf 2024 to 2025, WARN 2025). Well supported for core code; the core-versus-random split is stated clearly only from 2024 on, though his practice matches it earlier.

## 9. Design locking so the common case is uncontended: fix contention, keep locks near data, prefer plain locks and RCU over rwlocks

**Principle.** Contention is a design bug, not something to tune a lock for. The uncontended case is by far the common one, so locks must be cheap when uncontended and should sit next to the data they protect. If a lock is hot, split the data, take one lock in the common case and a top-level lock only for the rare multi-object case, or switch readers to RCU or seqcounts. Plain spinlocks or mutexes beat rwlocks almost always. Sometimes the right move is to delete the lock instead of optimising it. Lock-ordering rules must be stated where two locks of the same kind are taken.

**What triggers it in a review.**
- A fancy lock (queued rwlock, percpu rwsem, transactional memory, adaptive anything) added to make a contended global lock faster.
- One spinlock covering many independent objects (sysv semaphores, 2013).
- An `rwlock_t` for short non-sleeping sections.
- Taking two locks of the same type (two pages, two inodes) with no stated order.
- A lock whose only user could use an existing lock.

```c
/* his preferred shape for "usually one object, sometimes many" */
lock(&obj->lock);                 /* common case: just this */
/* rare case: take the global "all" lock first, then the per-object
   locks one by one, tracking which you already hold */
```

**His reasoning.** "contention pretty much happens in one situation, and one situation only: in a combination of (a) bad locking and (b) benchmarks." With fine-grained locks "_near_ the data", lock tricks that share the lock cacheline don't help because you bounce the data anyway. rwlocks "tend to be more expensive than spinlocks" and their parallelism shows up mainly "as 'more cacheline bounces'". Fixing contention gets you speed *and* fairness.

**How serious.** Firm. He refuses to optimise rarely used locks ("I'd rather get rid of it entirely", 2015), objects to rwlock conversions, NAKs out-of-line spinlock changes without real-load numbers, and asks for documented lock-ordering rules before accepting multi-lock code.

**Limits and exceptions.** He accepts rwlocks or rwsems in specific places (`tasklist_lock`, `mmap_sem`) and was willing to consider making `siglock` an rwlock (2022). He accepts queued rwlocks to fix writer starvation, since unfairness is its own bug (2013). He accepts RCU-based lockless lookup when the numbers are large (2011). He also stresses that unlock order doesn't matter, only lock order (2008, `alpine.LFD.2.00.0810080836410.3208@nehalem.linux-foundation.org`).

**Outside the kernel.** Applies directly to multi-threaded services, connection pools, caches, actor systems and RTOS firmware. Look for global mutexes around maps (shard them, or use per-key locks), `RwLock` used for tiny critical sections (often slower than `Mutex`), reader-heavy configuration that should be published by atomic pointer swap (an RCU analogue), and multi-resource locking with no documented order (deadlock risk).

**Evidence.**

- "And contention pretty much happens in one situation, and one situation only: in a combination of (a) bad locking and (b) benchmarks."  
  `CAHk-=whjFwzEq0u04=n=t7-kNJdX0HkAOjAMjmLXDDycJ+j9yQ@mail.gmail.com`, 2023-01-16, <https://lore.kernel.org/all/CAHk-%3DwhjFwzEq0u04%3Dn%3Dt7-kNJdX0HkAOjAMjmLXDDycJ%2Bj9yQ%40mail.gmail.com/>
- "And for the kernel, where we don't have bad locking, and where we actually use fine-grained locks that are _near_ the data that we are locking"  
  `CAHk-=whjFwzEq0u04=n=t7-kNJdX0HkAOjAMjmLXDDycJ+j9yQ@mail.gmail.com`, 2023-01-16, <https://lore.kernel.org/all/CAHk-%3DwhjFwzEq0u04%3Dn%3Dt7-kNJdX0HkAOjAMjmLXDDycJ%2Bj9yQ%40mail.gmail.com/>
- "particularly the uncontended case - which is actually the common one by far, despite some benchmarks"  
  `CAHk-=whjFwzEq0u04=n=t7-kNJdX0HkAOjAMjmLXDDycJ+j9yQ@mail.gmail.com`, 2023-01-16, <https://lore.kernel.org/all/CAHk-%3DwhjFwzEq0u04%3Dn%3Dt7-kNJdX0HkAOjAMjmLXDDycJ%2Bj9yQ%40mail.gmail.com/>
- "Usually rwlocks are a bad idea. They tend to be more expensive than spinlocks, and the extra parallelism is almost never noticeable (except as "more cacheline bounces") for something that is appropriate for a non-sleeping lock."  
  `CA+55aFy8ym1KSFv753wGrYn8qG5eK6YOy_nOCpYiqPjoLJwysg@mail.gmail.com`, 2012-02-08, <https://lore.kernel.org/all/CA%2B55aFy8ym1KSFv753wGrYn8qG5eK6YOy_nOCpYiqPjoLJwysg%40mail.gmail.com/>
- "If you can't make things work with either RCU or seqlocks, just use a regular semaphore."  
  `Pine.LNX.4.64.0611021458240.25218@g5.osdl.org`, 2006-11-02, <https://lore.kernel.org/all/Pine.LNX.4.64.0611021458240.25218%40g5.osdl.org/>
- "The optimal strategy if you have many items, and the *common* case is that you need just one lock, is actually to only take that single lock for the common case. No top-level lock at all."  
  `CA+55aFyivGLzW3hYKR7y_ATff49EOiBq4Tnyrv+WZRm4ks81vg@mail.gmail.com`, 2013-03-06, <https://lore.kernel.org/all/CA%2B55aFyivGLzW3hYKR7y_ATff49EOiBq4Tnyrv%2BWZRm4ks81vg%40mail.gmail.com/>
- "No, you try to fix the contention instead! That way, you fix many things. You probably speed things up, _and_ you make it fairer."  
  `alpine.LFD.0.98.0706201018290.3593@woody.linux-foundation.org`, 2007-06-20, <https://lore.kernel.org/all/alpine.LFD.0.98.0706201018290.3593%40woody.linux-foundation.org/>
- "So I'm not convinced that the right thing to do is to try to optimize that lock at ALL. I'd rather get rid of it entirely."  
  `CA+55aFwxjAWTm9XZg0ZE6kB70S8iKV6b8RQL8Bi6fapaPbwpRQ@mail.gmail.com`, 2015-05-26, <https://lore.kernel.org/all/CA%2B55aFwxjAWTm9XZg0ZE6kB70S8iKV6b8RQL8Bi6fapaPbwpRQ%40mail.gmail.com/>
- "Is there some ordering guarantee that says that 'pagecache_page' and 'page' will always be in a certain relationship so that you cannot get A->B and B->A lock ordering? Please document that ordering rule if so."  
  `alpine.LFD.2.00.1009101011140.9670@i5.linux-foundation.org`, 2010-09-10, <https://lore.kernel.org/all/alpine.LFD.2.00.1009101011140.9670%40i5.linux-foundation.org/>

**How well supported.** About 40 messages, 2001 to 2026 (rwsem 2001, rwlock 2006, BKL 2008, rwlock 2009 and 2012, sysv sem 2013, qrwlock 2013, percpu-rwsem 2015, TM 2023, d_walk 2026). Strongly supported.

## 10. Atomics and locked instructions are expensive even without contention

**Principle.** A locked instruction serialises the pipeline and costs tens of cycles even on one CPU with a hot cache. An uncontended spinlock costs about the same as one atomic op, so replacing a lock with two atomics is a loss. Adding a single atomic to a hot path is measurable. Counters on hot paths should be per-CPU or per-thread and folded later.

**What triggers it in a review.**
- Converting counters to `atomic_t` "for scalability", which slows the single-threaded case.
- A pair of atomic increments where one reference or a batched update would do.
- `cmpxchg` loops that read first (shared-then-exclusive cacheline transitions).
- Reference counting on every operation in a hot loop.

**His reasoning.** "A totally uncontended spinlock is actually cheaper than a pair of atomic ops", which costs "roughly 10-35 on modern x86" cycles. "Locked ops show up not just in microbenchmarks ... they show up in 'real' benchmarks too": one or two locked instructions in the page-fault path were visible in lmbench.

**How serious.** He rejects atomic-counter conversions as "pointless" when they lose the uncontended win (2005), and rewrites hot paths to drop atomics himself (signal accounting, 2020).

**Limits and exceptions.** Under real contention, an atomic `xadd` beats a spinlock because it bounces once per success rather than once per attempt (2010). Lockref's cmpxchg was accepted although it is "a tiny bit" slower single-threaded, because it removes contention on shared dentries (2013).

**Outside the kernel.** Applies directly: `Arc` clone and drop in hot loops, `AtomicUsize` statistics on every request, `std::shared_ptr` copies, Java `AtomicLong` counters (use `LongAdder`). Per-thread or sharded counters and batching are the transferable fixes. On microcontrollers without cache coherency the costs are different (interrupt masking), but "don't add serialisation to the hot path" still holds.

**Evidence.**

- "HOWEVER, the fact that it makes the mm counters be atomic just makes it pointless. It may help scalability, but it loses the attribute that I considered a big win above - it no longer helps the non-contended case"  
  `Pine.LNX.4.58.0508171529530.3553@g5.osdl.org`, 2005-08-17, <https://lore.kernel.org/all/Pine.LNX.4.58.0508171529530.3553%40g5.osdl.org/>
- "Locked ops show up not just in microbenchmarks looping over the instruction, they show up in "real" benchmarks too."  
  `alpine.LFD.1.10.0808140901390.3324@nehalem.linux-foundation.org`, 2008-08-14, <https://lore.kernel.org/all/alpine.LFD.1.10.0808140901390.3324%40nehalem.linux-foundation.org/>
- "A totally uncontended spinlock is actually cheaper than a pair of atomic ops. So if it's a hot path it probably should be moved elsewhere if possible."  
  `CA+55aFz6vpv01OAGcq9n8Q4bVgihqSiwz2qwNjBAHeFFvUD5Hg@mail.gmail.com`, 2011-12-15, <https://lore.kernel.org/all/CA%2B55aFz6vpv01OAGcq9n8Q4bVgihqSiwz2qwNjBAHeFFvUD5Hg%40mail.gmail.com/>

**How well supported.** About 15 messages and commits, 2004 to 2026 (UP atomics 2004, mm counters 2005, LOCK_PREFIX 2008, xadd 2010, audit 2011, lockref 2013, signals 2020, folio refcount 2026). Well supported.

## 11. Default to a lock; lockless code needs a hot-path justification, paired barriers and comments

**Principle.** Unless a path is truly timing-critical, use a lock: mutexes are "high-performance and non-confusing", and lockless code is almost always either buggy or "incredibly subtle". When lockless code is justified, both sides of every ordering must be explicit and paired, documented in comments saying what each barrier pairs with, and built from a few standard patterns (release/acquire, RCU, seqcount) rather than ad-hoc barriers. Lockless code belongs in core infrastructure reviewed by people who know it, not in random drivers.

**What triggers it in a review.**
- A barrier (`smp_wmb`, `mb`, `READ_ONCE`) with no comment naming its pair.
- Barriers used to handle multiple concurrent readers or writers ("Barriers simply do not protect against two concurrent readers, or two concurrent writers").
- Open-coded wait queues, flags or hand-rolled ring buffers in place of a mutex or completion.
- `READ_ONCE`/`WRITE_ONCE` sprinkled to silence a race detector.
- Weakening documented memory-ordering rules.

**His reasoning.** "You can never do ordering on just one side." People "always invariably get the memory ordering wrong", both "doesn't work" and "slow". He says he gets it wrong himself and prefers "leaning on a few standard patterns". Weak rules confuse people, who then "'fix' code that doesn't want fixing" (2016).

**How serious.** He asks for documentation before applying ("Please document the barrier that this mb() pairs with ... and I'll happily take it", 2013). He tells people to delete barriers and use a lock (circular buffers, 2019). He wants ordering rules "as tight as at all humanly possible" (2016).

**Limits and exceptions.** He wrote and merged much lockless code where it pays: RCU path walk ("way more clever and subtle ... But it's rather impressive and I really wanted to merge it, because some of the performance numbers are pretty stunning", 2011), lockref, seqcount-protected lookups. His own 2008 anon_vma fix admits "lockless is bad", but taking the lock "is just not an option" on that hot path. *Change over time:* he used to prefer `rmb`/`wmb` pairs and in 2024 said acquire/release has become the preferred form (`CAHk-=wivmMgGiSnUm35WVm9=yNM1=jrHG4fgWo09XWwWZzvTMw@mail.gmail.com`).

**Outside the kernel.** Applies directly to `std::atomic` and `Ordering::Relaxed` in Rust and C++, Java `volatile`, Go `sync/atomic`, and lock-free queues in firmware between ISR and main loop. A reviewer should ask: why not a mutex or channel? What does each atomic pair with? Is there a comment? Has it been tested on a weakly ordered CPU (ARM)? Prefer library primitives (channels, `ArcSwap`, `crossbeam`) to hand-rolled ones.

**Evidence.**

- "End result: use a lock. Seriously. Anything else is going to be buggy, or going to be incredibly subtle."  
  `CAHk-=wj85tOp8WjcUp6gwstp4Cg2WT=p209S=fOzpWAgqqQPKg@mail.gmail.com`, 2019-09-18, <https://lore.kernel.org/all/CAHk-%3Dwj85tOp8WjcUp6gwstp4Cg2WT%3Dp209S%3DfOzpWAgqqQPKg%40mail.gmail.com/>
- "Anyway, lockless is bad. It would certainly be a *lot* simpler to just take the page_table_lock around the whole thing, except I think we really *really* don't want to do that. That thing is solidly in a couple of *very* timing-critical routines."  
  `alpine.LFD.2.00.0810171549310.3438@nehalem.linux-foundation.org`, 2008-10-17, <https://lore.kernel.org/all/alpine.LFD.2.00.0810171549310.3438%40nehalem.linux-foundation.org/>
- "That, btw, is an important part of memory ordering. You can never do ordering on just one side. A "smp_wmb()" on its own is always nonsensical."  
  `alpine.LFD.2.00.0810171235310.3438@nehalem.linux-foundation.org`, 2008-10-17, <https://lore.kernel.org/all/alpine.LFD.2.00.0810171235310.3438%40nehalem.linux-foundation.org/>
- "They don't have lockdep checking, but more importantly, people always invariably get the memory ordering wrong. And by "wrong" I mean both "doesn't work" (because of insufficient memory ordering) and "slow" (due to excessive memory ordering)."  
  `CA+55aFyd7d+C39ipC5XuZg1gJjJ+HFSgcPQU7Xb26Fsh6Z1_0A@mail.gmail.com`, 2016-11-21, <https://lore.kernel.org/all/CA%2B55aFyd7d%2BC39ipC5XuZg1gJjJ%2BHFSgcPQU7Xb26Fsh6Z1_0A%40mail.gmail.com/>
- "mutexes are good for exclusion. mutexes are both high-performance and non-confusing."  
  `CA+55aFyd7d+C39ipC5XuZg1gJjJ+HFSgcPQU7Xb26Fsh6Z1_0A@mail.gmail.com`, 2016-11-21, <https://lore.kernel.org/all/CA%2B55aFyd7d%2BC39ipC5XuZg1gJjJ%2BHFSgcPQU7Xb26Fsh6Z1_0A%40mail.gmail.com/>
- "Christ, I'm supposed to know it fairly well, and I still get it wrong myself regularly and have to really think about it (and honestly just prefer leaning on a few standard patterns rather than having to think about it too much)."  
  `CAHk-=wgxB7LbAfAjx9_-N=4YDd+afMC8n1ydNh1v059bULNAGQ@mail.gmail.com`, 2024-03-18, <https://lore.kernel.org/all/CAHk-%3DwgxB7LbAfAjx9_-N%3D4YDd%2BafMC8n1ydNh1v059bULNAGQ%40mail.gmail.com/>
- "Please document the barrier that this mb() pairs with, and then give an explanation for the fix in the commit message, and I'll happily take it."  
  `CA+55aFwP3Tvmfh23KDDXhB3k=RS8pNhqasw5vuBUHw4TxrakOQ@mail.gmail.com`, 2013-01-01, <https://lore.kernel.org/all/CA%2B55aFwP3Tvmfh23KDDXhB3k%3DRS8pNhqasw5vuBUHw4TxrakOQ%40mail.gmail.com/>
- "It's scary because this is some very core code, and the new RCU lookup model is way more clever and subtle than the old dentry_lock spinlock. But it's rather impressive and I really wanted to merge it, because some of the performance numbers are pretty stunning."  
  `AANLkTi=eNucM5d=+zq5euz3dZirJEhPaH9f9ZXuHymEM@mail.gmail.com`, 2011-01-08, <https://lore.kernel.org/all/AANLkTi%3DeNucM5d%3D%2Bzq5euz3dZirJEhPaH9f9ZXuHymEM%40mail.gmail.com/>

**How well supported.** About 35 messages, 2006 to 2025 (anon_vma 2008, completions 2008, poll 2013, ticketlock 2013, LKMM 2016, wait queues 2016, circular buffers 2019, KCSAN 2019 and 2021, C++ committee 2024, seqlock helpers 2025). Strongly supported.

## 12. "It works in testing" proves nothing for races; reason about the interleaving

**Principle.** Concurrency bugs that need rare timing don't show up in testing, so passing tests is no evidence of correctness for racy code. A reviewer has to reason about the possible interleavings. Code that is "practically impossible to hit" is still wrong if nothing prevents it, and those are the worst bugs because they surface as unreproducible field failures. Debug checks that only fire on the racy case need to fire on the possible case.

**What triggers it in a review.**
- Checks like `if (file_count(file) > 1)` or "is this the last user" done outside the mechanism that guarantees it.
- A faster path whose safety depends on the other side being "slow and heavy".
- Arguments of the form "we ran it for a week and never saw it".
- Debug assertions that test a racy condition, so they never trigger.

**His reasoning.** "It is a very dangerous pattern, because it likely works in practice during testing, and looks like it might work. But it is completely and unfixably wrong." Blue-moon bugs on specific hardware are "the worst kind of bugs". About his own work (2025): it "all looks beautiful in profiles etc - ask me how I know. But it's still wrong."

**How serious.** He pulls with an explicit "I expect this to be either reverted, or explained why it really is correct" (2018), rejects patterns outright (configfs 2020), and changes debug checks so they fire on the possible case (`dput` might_sleep, 2013).

**Limits and exceptions.** He accepts racy statistics and approximations where nothing depends on them, and objects to annotations whose only purpose is silencing KCSAN (2019, 2021). He doesn't treat every data race as a bug.

**Outside the kernel.** Applies directly: check-then-act on shared state, "last reference" logic outside the refcount, TOCTOU on files, async code relying on timing. Ask for the invariant and what enforces it, not for test runs. Tools (TSan, loom, `-race`) help, but he would not accept "the race detector is quiet" as a proof either.

**Evidence.**

- "It is a very dangerous pattern, because it likely works in practice during testing, and looks like it might work. But it is completely and unfixably wrong."  
  `CAHk-=wg9dzJOkvysjgdHv5eFJU76EFAwCxNenRxTtq6VWof98Q@mail.gmail.com`, 2020-08-05, <https://lore.kernel.org/all/CAHk-%3Dwg9dzJOkvysjgdHv5eFJU76EFAwCxNenRxTtq6VWof98Q%40mail.gmail.com/>
- "Because right now it just looks to be like a race condition that generates faster - but incorrect - code."  
  `CAHk-=wg4QEioEY=ps0ntD-CU_pDD4R3nkg-Z-sT_W=XWJ7-faQ@mail.gmail.com`, 2018-12-28, <https://lore.kernel.org/all/CAHk-%3Dwg4QEioEY%3Dps0ntD-CU_pDD4R3nkg-Z-sT_W%3DXWJ7-faQ%40mail.gmail.com/>
- "The "this happens in a blue moon on just very specific hardware" bugs are the worst kind of bugs."  
  `CAHk-=wg4QEioEY=ps0ntD-CU_pDD4R3nkg-Z-sT_W=XWJ7-faQ@mail.gmail.com`, 2018-12-28, <https://lore.kernel.org/all/CAHk-%3Dwg4QEioEY%3Dps0ntD-CU_pDD4R3nkg-Z-sT_W%3DXWJ7-faQ%40mail.gmail.com/>
- "But because it's a very rare race, the debugging code would never trigger it in practice."  
  `0d98439ea3c6ffb2af931f6de4480e744634e2c5`, 2013-09-08, <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=0d98439ea3c6ffb2af931f6de4480e744634e2c5>
- "In fact, it works so fine that everything boots and it all looks beautiful in profiles etc - ask me how I know. But it's still wrong."  
  `CAHk-=wh62OxWsL+msmks7=VdBJHz7HvRYoPDckkAEAwsgrmjew@mail.gmail.com`, 2025-10-21, <https://lore.kernel.org/all/CAHk-%3Dwh62OxWsL%2Bmsmks7%3DVdBJHz7HvRYoPDckkAEAwsgrmjew%40mail.gmail.com/>

**How well supported.** About 15 messages and commits, 2003 to 2025 (dput 2013, blk-mq 2018, configfs 2020, workqueue 2022, filemap 2025). Moderately well supported; the theme also overlaps with correctness reviews outside performance.

## 13. Fast but wrong is garbage, yet performance is a feature: don't dismiss it with specious correctness, and revert regressions

**Principle.** Two sides of one rule. A faster result that is incorrect is worthless ("Speed doesn't matter for garbage"). But performance is a real feature, and a reviewer must not wave away a performance cost by appealing to a "correctness" nobody needs, or to security in the abstract. A measured performance regression on a real load is a regression like any other: it gets reverted if not fixed.

**What triggers it in a review.**
- "Optimisations" that rely on undefined behaviour or skip a needed check.
- A change that slows a common operation to fix a theoretical corner case nobody has hit.
- Mitigations or hardening with large costs and no evidence of a real attack.
- A known performance regression waved through because "it fixes something else" or "it's already merged".

**His reasoning.** "sometimes 'pi = 3.14' is (a) infinitely faster than the 'correct' answer and (b) the difference between the 'correct' and the 'wrong' answer is meaningless." "Performance is a feature too": a known 40% AIM7 drop would never have been accepted, and having merged it is no reason to keep it. On security he says that "performance matters. A *LOT*" when real users report slowdowns.

**How serious.** Reverts (BKL semaphore 2008, THP placement 2018, poll 2018), and public pushback on security patches with big costs (Spectre-era, 2018).

**Limits and exceptions.** Where correctness is real (data loss, races, semantics users rely on), correctness wins: see principle 12 and the uncommon-path rule in principle 3. He accepts security costs when the hole is real and nothing cheaper works. He also notes that regressions nobody notices on any real workload can be treated "as if it doesn't exist" (`CAHk-=wi7DB2SJ-wngVvsJ7Ak2cM556Q8437sOXo4EJt2BWPdEg@mail.gmail.com`, 2021).

**Outside the kernel.** Applies directly: treat p99 latency or throughput regressions as release blockers. Push back on defensive copies, validation or encryption layers added on hot paths without a threat model. Equally, reject fast paths that skip invariants.

**Evidence.**

- "It doesn't make correct code run faster. It just makes incorrect code result in incorrect results."  
  `CA+55aFy-imLQ9WeA880qR_DqKTpCiH2-3ou6_NScBGOKGE=-fQ@mail.gmail.com`, 2018-03-06, <https://lore.kernel.org/all/CA%2B55aFy-imLQ9WeA880qR_DqKTpCiH2-3ou6_NScBGOKGE%3D-fQ%40mail.gmail.com/>
- "Speed doesn't matter for garbage."  
  `CA+55aFy-imLQ9WeA880qR_DqKTpCiH2-3ou6_NScBGOKGE=-fQ@mail.gmail.com`, 2018-03-06, <https://lore.kernel.org/all/CA%2B55aFy-imLQ9WeA880qR_DqKTpCiH2-3ou6_NScBGOKGE%3D-fQ%40mail.gmail.com/>
- "The thing is, some specious value of "correctness" is often irrelevant because it doesn't matter. While performance almost _always_ matters. And I absolutely _detest_ the fact that people so often dismiss performance concerns so readily."  
  `alpine.LFD.1.10.0808081639540.3462@nehalem.linux-foundation.org`, 2008-08-08, <https://lore.kernel.org/all/alpine.LFD.1.10.0808081639540.3462%40nehalem.linux-foundation.org/>
- "Put another way: if we had introduced the BKL-as-semaphore with a known 40% performance drop in AIM7, I would simply never ever have accepted the patch in the first place, regardless of _any_ excuses. Performance is a feature too."  
  `alpine.LFD.1.10.0805070800120.32269@woody.linux-foundation.org`, 2008-05-07, <https://lore.kernel.org/all/alpine.LFD.1.10.0805070800120.32269%40woody.linux-foundation.org/>
- "I'm going to revert the commit since people apparently seem to be ignoring this fundamental issue."  
  `CAHk-=whi8Ju-cTDL4cYtwuLA7BYgGJYyy6HVMoknZaLHnRc83g@mail.gmail.com`, 2018-12-05, <https://lore.kernel.org/all/CAHk-%3Dwhi8Ju-cTDL4cYtwuLA7BYgGJYyy6HVMoknZaLHnRc83g%40mail.gmail.com/>
- "So this whole "security is so important that performance doesn't matter" mindset is pure and utter garbage."  
  `CA+55aFzqb-p_Ng2nsXvFsibtNC2rH5fwrefwnwA3TTFVtzM3FA@mail.gmail.com`, 2018-01-07, <https://lore.kernel.org/all/CA%2B55aFzqb-p_Ng2nsXvFsibtNC2rH5fwrefwnwA3TTFVtzM3FA%40mail.gmail.com/>

**How well supported.** About 20 messages, 2004 to 2025 (BKL 2008, git symlinks 2008, Spectre 2018, UB 2018, THP revert 2018, random 2020). Well supported; the git message is from the git list and shows the rule is not kernel-only.

## 14. Complexity for speed must be paid for with numbers; prefer the obvious solution

**Principle.** Extra complexity in the name of performance needs a measured, real payoff, and the bar rises with the subtlety. Without numbers, take the simple, obvious version ("I'd rather be intelligent than clever"): optimise what shows up in profiles, and don't build heuristics around a cost nobody measured. With strong real numbers, he accepts complexity he dislikes.

**What triggers it in a review.**
- Elaborate caching, invalidation, deferred work or heuristics to avoid a cost that hasn't been profiled.
- Infrastructure in a shared file serving one caller.
- New flags or modes "in case it matters".
- Subtle invalidation logic where a crude but obvious rule (time-based caching) would work.

**His reasoning.** The clever approach adds "tons of complexity" that is hard to debug because the rare case is rare; the intelligent approach waits for a profile. "Numbers talk, handwaving 'this might be an issue' walks." Complexity has measurable costs (patch size, bugs, review time); a speculative speedup doesn't.

**How serious.** He refuses or defers until numbers arrive (2000, 2013, 2016, 2024), and sometimes writes the crude-but-obvious alternative himself (meminfo cache by time, 2015).

**Limits and exceptions.** Strong numbers beat his own taste: "I'll take 'real numbers' over my personal dislikes any day" (2009, nontemporal copies, which he otherwise opposes). The RCU path walk and lockref were large complexity increases he championed because of measured wins. The 2007 git talk calls git "very performance centric" and says that sometimes "you have to use more complicated algorithm" (`https://www.youtube.com/watch?v=4XpnKHJAok8`, auto-caption transcript, so not quoted).

**Outside the kernel.** Applies directly: cache layers, memoisation, pooled objects, speculative prefetching or bespoke data structures in services and libraries. Ask for the profile that motivated it and the measured gain; otherwise ask for the simple version.

**Evidence.**

- "So I didn't want to apply the nocache patches in the first place, but the performance numbers were pretty clear. I'll take "real numbers" over my personal dislikes any day."  
  `alpine.LFD.2.00.0902250753030.3111@localhost.localdomain`, 2009-02-25, <https://lore.kernel.org/all/alpine.LFD.2.00.0902250753030.3111%40localhost.localdomain/>
- "The "intelligent" approach is just to say that if get_block() shows up on the performance profiles, then it should be optimized. I'd rather be intelligent than clever."  
  `Pine.LNX.4.10.10012311035020.4239-100000@penguin.transmeta.com`, 2000-12-31, <https://lore.kernel.org/all/Pine.LNX.4.10.10012311035020.4239-100000%40penguin.transmeta.com/>
- "The point is, it's rare, and if there are no numbers to say that it's an issue, we shouldn't create the complication. Numbers talk, handwaving "this might be an issue" walks."  
  `CA+55aFyzf8r2q-HLfADcz74H-My_GY-z15yLrwH-KUqd486Q0A@mail.gmail.com`, 2016-11-03, <https://lore.kernel.org/all/CA%2B55aFyzf8r2q-HLfADcz74H-My_GY-z15yLrwH-KUqd486Q0A%40mail.gmail.com/>
- "In contrast, my "just base it on time" sure as hell isn't subtle. It's not great, but at least it's obvious and the crazy logic is localized.."  
  `CA+55aFyTLkNP+5Bwnc=Z8BnygBAALdzTAYxfXXoenkp33iipyA@mail.gmail.com`, 2015-08-13, <https://lore.kernel.org/all/CA%2B55aFyTLkNP%2B5Bwnc%3DZ8BnygBAALdzTAYxfXXoenkp33iipyA%40mail.gmail.com/>
- "Also, this kind of extra complexity does require numbers to argue for it."  
  `CAHk-=wj5rEZFvaLgs-ZtsCX9++mFNYKox21SBfF8vrSQG4WbPA@mail.gmail.com`, 2024-03-13, <https://lore.kernel.org/all/CAHk-%3Dwj5rEZFvaLgs-ZtsCX9%2B%2BmFNYKox21SBfF8vrSQG4WbPA%40mail.gmail.com/>

**How well supported.** About 25 messages, 2000 to 2024 (deferred writes 2000, nocache 2009, THP 2010, qrwlock 2013, meminfo 2015, PageWaiters 2016, smp_call 2024). Strongly supported.

## 15. Memory allocation: handle failure by returning an error, never panic; say explicitly when failure is fine; keep stack frames small

**Principle.** Allocation failure is an error to be returned (`-ENOMEM`), not a panic, `BUG_ON` or hidden abort. Callers that can tolerate failure must say so explicitly (`__GFP_NOWARN`, `__GFP_NORETRY`), and large allocations must handle failure. For "usually small, sometimes large" buffers: try a cheap allocation first, then fall back. Keep allocation side work (accounting, hooks) out of the hot path. On the stack: small fixed buffers for the common case are good and much faster than heap allocation, but big stack frames, especially in deep call chains or from inlining, are bugs.

**What triggers it in a review.**
- `BUG_ON(!ptr)` or `panic!("Out of memory!")` after an allocation.
- Hidden allocations in a language runtime or helper with no error path.
- Large arrays, `cpumask_t` or structs with many cases on the stack, or functions with disjoint `case` arms each declaring big locals.
- A 4 KB stack buffer in a function that also calls deep slow paths.
- Per-allocation accounting or hooks added to every allocation.

```c
char small[256];                 /* fine: bounded, common case */
char *buf = len <= sizeof(small) ? small : kmalloc(len, GFP_KERNEL);
if (!buf)
        return -ENOMEM;          /* not BUG_ON() */
```

**His reasoning.** Failures must be "caught and handled synchronously and results in an ENOMEM error return"; panics that trigger "only under very special situations that are hard to trigger" are "about the worst possible case" (Rust, 2021). Stack space is small and shared by the whole call chain; gcc doesn't merge stack slots well, so inlining or many disjoint locals inflate frames. On the stack, the small common case is "about infinitely faster" than `kmalloc()`.

**How serious.** He refuses `BUG_ON` for allocation failure ("I refuse to see more of the shit-for-brains kind of 'I can't be bothered to handle error cases' BUG_ON() stuff", 2018). He commits stack fixes himself when builds break on frame-size limits (2021), and he limited `NR_CPUS` in 2008 over stack usage.

**Limits and exceptions.** *Kernel-specific policy:* small kernel allocations "should basically never fail" (the OOM killer reclaims instead), so he called "everybody should check allocation failure" "a computer science myth" for that case (2015). That is a statement about kernel allocator policy, not permission to skip error paths: the same message requires large allocations to handle failure, and he still wants ENOMEM rather than panic from Rust code. `__GFP_NOFAIL` is acceptable only for small allocations; boot-time allocations can be assumed to succeed.

**Outside the kernel.** Partly transfers. In application code, most languages abort on OOM, and that is usually right; the reviewer's points are not to add `unwrap()` or `panic` in library code that might run in constrained contexts, to use fallible allocation in firmware, `no_std` and embedded code, to use small-buffer optimisation (`SmallVec`, SSO strings) for common small sizes, and to watch stack usage on embedded targets and threads with small stacks. Keep per-request allocations out of hot loops.

**Evidence.**

- "Kernel allocators that know that they do large allocations (ie bigger than a few pages) need to be able to handle the failure, but not the general case."  
  `CA+55aFw=OLSdh-5Ut2vjy=4Yf1fTXqpzoDHdF7XnT5gDHs6sYA@mail.gmail.com`, 2015-10-02, <https://lore.kernel.org/all/CA%2B55aFw%3DOLSdh-5Ut2vjy%3D4Yf1fTXqpzoDHdF7XnT5gDHs6sYA%40mail.gmail.com/>
- "Small kernel allocations should basically never fail, because we end up needing memory for random things, and if a kmalloc() fails it's because some application is using too much memory, and the application should be killed."  
  `CA+55aFw=OLSdh-5Ut2vjy=4Yf1fTXqpzoDHdF7XnT5gDHs6sYA@mail.gmail.com`, 2015-10-02, <https://lore.kernel.org/all/CA%2B55aFw%3DOLSdh-5Ut2vjy%3D4Yf1fTXqpzoDHdF7XnT5gDHs6sYA%40mail.gmail.com/>
- "An allocation failure in some random driver must never ever be something that the compiler just turns into a panic. It must be something that is caught and handled synchronously and results in an ENOMEM error return."  
  `CAHk-=wiVY56LzwV_G075NEFwsdf-p7GOTy_cB7-UU9b=49rB1g@mail.gmail.com`, 2021-04-14, <https://lore.kernel.org/all/CAHk-%3DwiVY56LzwV_G075NEFwsdf-p7GOTy_cB7-UU9b%3D49rB1g%40mail.gmail.com/>
- "No. I *really* want people to write out that "I am ok with the allocation failing". It's not an "inconvenience". It's a sign that you are competent and that you know it will fail, and that you can handle it."  
  `CA+55aFw4R7B8pAJ4TNVefdtCVAnZKY28i6_+5jQhoop60-NuQQ@mail.gmail.com`, 2016-11-29, <https://lore.kernel.org/all/CA%2B55aFw4R7B8pAJ4TNVefdtCVAnZKY28i6_%2B5jQhoop60-NuQQ%40mail.gmail.com/>
- "Either we know the allocation cannot fail - which is perfectly fine at bootup, and is a common pattern - or it can fail and we need to handle it. In neither case is the BUG_ON() appropriate."  
  `CA+55aFwAtfiMa22-OFGf1dNR8CNzSKjjLLj5UL-HqgapV7Tf1A@mail.gmail.com`, 2018-05-23, <https://lore.kernel.org/all/CA%2B55aFwAtfiMa22-OFGf1dNR8CNzSKjjLLj5UL-HqgapV7Tf1A%40mail.gmail.com/>
- "Generally if it's *usually* a small allocation, the best pattern tends to be to first try to kmalloc (of get_free_pages()) using __GFP_NORETRY | __GFP_NOWARN, and then fall back on vmalloc()."  
  `CA+55aFw8ERWE13OJ7ejx=g=C5K1BtwZXA92wO-iSmLHyt1fDpw@mail.gmail.com`, 2016-10-20, <https://lore.kernel.org/all/CA%2B55aFw8ERWE13OJ7ejx%3Dg%3DC5K1BtwZXA92wO-iSmLHyt1fDpw%40mail.gmail.com/>
- "but that's an uncommon path and would be marked unlikely and not be in the hot path at all."  
  `CAHk-=whYOOdM7jWy5jdrAm8LxcgCMFyk2bt8fYYvZzM4U-zAQA@mail.gmail.com`, 2024-01-22, <https://lore.kernel.org/all/CAHk-%3DwhYOOdM7jWy5jdrAm8LxcgCMFyk2bt8fYYvZzM4U-zAQA%40mail.gmail.com/>

**How well supported.** About 30 messages and commits, 2002 to 2025 (stack 2002, NR_CPUS 2008, fs stack 2008, OOM 2015, GFP flags 2016, BUG_ON 2018, Rust 2021, frame-size 2021, NOFAIL 2024, memcg 2024, filemap 2025). Well supported; the kernel-specific "small allocations don't fail" policy needs care when transferring.

## 16. Scalability work must not slow the normal machine; single-thread performance still matters

**Principle.** Improvements for huge NUMA or many-core machines are welcome only if they don't cost the common machine (one socket, a few cores, mostly single-threaded work) anything measurable. The best scalability work also speeds up the unthreaded case. A change that helps "very few NUMA machines" while hurting normal ones gets reverted.

**What triggers it in a review.**
- Per-node or per-CPU data structures or extra indirection added for big-machine scaling, with no single-socket numbers.
- Atomic counters replacing plain ones "for scalability" (see principle 10).
- Lock-algorithm changes justified by contention only on very large systems.
- Configuration limits raised (`NR_CPUS`) without checking stack or size costs for everyone.

**His reasoning.** "That zone crap may have helped some very few NUMA machines, but it *hurt* normal machines." Making things "worse for just about everybody, in order to fix a problem that almost nobody can actually see" is "hubris". "Single-thread performance matters a hell of a lot." He celebrated the RCU path walk because the win was in "the _unthreaded_ case. Not some odd high-end scalability thing".

**How serious.** He refused to reintroduce the zone code ("HELL NO!", 2016), NAKed spinlock changes (2013), and limited `NR_CPUS` to 512 in 2008 over stack costs.

**Limits and exceptions.** He accepts a "tiny bit" of single-thread cost if it is "hopefully unmeasurable" and removes real contention (lockref, 2013). He takes big-machine reports seriously when they're real and persistent ("on big multi-socket machines people have reported it as a problem forever", `tasklist_lock`, 2020). He also argues that server scalability work has improved desktops "_immensely_" and opposes splitting kernels by audience (`alpine.LFD.0.999.0707281050590.3442@woody.linux-foundation.org`, 2007).

**Outside the kernel.** Applies directly: sharding, actor pools or distributed caches added to a service that runs on one box; thread pools that slow the single-request path; frameworks tuned for hyperscale that cost small deployments. Ask for numbers on the typical deployment, not only the largest.

**Evidence.**

- "That zone crap may have helped some very few NUMA machines, but it *hurt* normal machines."  
  `CA+55aFyzf8r2q-HLfADcz74H-My_GY-z15yLrwH-KUqd486Q0A@mail.gmail.com`, 2016-11-03, <https://lore.kernel.org/all/CA%2B55aFyzf8r2q-HLfADcz74H-My_GY-z15yLrwH-KUqd486Q0A%40mail.gmail.com/>
- "So you're potentially making things worse for just about everybody, in order to fix a problem that almost nobody can actually see."  
  `CA+55aFwxYK-BLH0crhySHaQvAYHOH-VGUi7WTd1aq-24+WTDYw@mail.gmail.com`, 2013-02-13, <https://lore.kernel.org/all/CA%2B55aFwxYK-BLH0crhySHaQvAYHOH-VGUi7WTd1aq-24%2BWTDYw%40mail.gmail.com/>
- "Single-thread performance matters a hell of a lot, and any company that bets that it doesn't, is a failure."  
  `Pine.LNX.4.64.0511231416490.13959@g5.osdl.org`, 2005-11-23, <https://lore.kernel.org/all/Pine.LNX.4.64.0511231416490.13959%40g5.osdl.org/>
- "And that's the _unthreaded_ case. Not some odd high-end scalability thing"  
  `AANLkTi=eNucM5d=+zq5euz3dZirJEhPaH9f9ZXuHymEM@mail.gmail.com`, 2011-01-08, <https://lore.kernel.org/all/AANLkTi%3DeNucM5d%3D%2Bzq5euz3dZirJEhPaH9f9ZXuHymEM%40mail.gmail.com/>
- "So I actually expect the x86 code to slow down a tiny bit for the single-threaded case, although that should be hopefully unmeasurable."  
  `CA+55aFzVNe==TM+PeK4zqvGQm7K+KLgO1hBYSOzFqwPSVts03Q@mail.gmail.com`, 2013-08-30, <https://lore.kernel.org/all/CA%2B55aFzVNe%3D%3DTM%2BPeK4zqvGQm7K%2BKLgO1hBYSOzFqwPSVts03Q%40mail.gmail.com/>
- "But because it's one of those completely global locks, on big multi-socket machines people have reported it as a problem forever."  
  `CAHk-=wiOS4Fi2tsXQrvLOiW69g4HiJYsqL6RPeTd14b4+2-Ykg@mail.gmail.com`, 2020-04-02, <https://lore.kernel.org/all/CAHk-%3DwiOS4Fi2tsXQrvLOiW69g4HiJYsqL6RPeTd14b4%2B2-Ykg%40mail.gmail.com/>

**How well supported.** About 15 messages, 2002 to 2020 (SMP 2002, single-thread 2005, desktop/server 2007, NR_CPUS 2008, RCU walk 2011, spinlocks 2013, lockref 2013, zones 2016, tasklist 2020). Well supported.

## 17. Build efficiency into data structures; leave cold code simple; don't optimise what isn't hot

**Principle.** Real performance comes from data structure and layout choices made up front: what is cheap "by design" and what is expensive. Micro-optimising code that isn't hot is a cost with no benefit: it adds special cases and complexity. Either a path is performance-critical and you show profiles, or it isn't and it should be the simplest correct code. Early-exit shortcuts that complicate semantics without a measured need are premature.

**What triggers it in a review.**
- Special cases for small sizes, unsafe accessors (`__put_user`) or inlines in cold code (boot, setup, ioctl, error paths, core dumps).
- Micro-optimised helpers for functions called "once in a blue moon".
- Data structure changes that make the format or invariants worse for "dubious gain".
- Shortcuts (stop-early, skip-the-check) that create subtle ordering or semantics rules.

**His reasoning.** "Bad programmers worry about the code. Good programmers worry about data structures and their relationships." In git, path limiting "is cheap by design (it's how the data structures are laid out)". For cold code: "It's not performance-critical code, and if it ever is, it needs to be rewritten anyway." Rarely called functions run with cold caches and no branch history, so hot-loop tuning doesn't even apply to them.

**How serious.** Usually a request to simplify or remove ("Just replace the __put_user() with a put_user() and be done with it", 2019). Strong objections when data-structure soundness is at stake (git pack formats, 2006).

**Limits and exceptions.** "Premature optimization" barely appears as a phrase in the corpus (one 2026 message). His usual argument is about evidence and hotness, not the Knuth quote. He doesn't defend slow designs: he expects designed-in efficiency (git's object model, the page cache's "much better designed" fixed-size entries, `Pine.LNX.4.21.0105041015520.521-100000@penguin.transmeta.com`, 2001).

**Outside the kernel.** Applies directly: choose the schema, index, data layout and API shape for the expected access patterns; keep CLI parsing, configuration loading and admin endpoints simple; reject "optimised" versions of code that runs once per process.

**Evidence.**

- "Bad programmers worry about the code. Good programmers worry about data structures and their relationships."  
  `Pine.LNX.4.64.0607270936200.4168@g5.osdl.org`, 2006-07-27, <https://lore.kernel.org/all/Pine.LNX.4.64.0607270936200.4168%40g5.osdl.org/>
- "seeing differences in the paths is cheap by design (it's how the data structures are laid out), but seeing differences in actual diffs means that we have to fully generate each diff for each revision!"  
  `alpine.LFD.0.98.0705060919010.25245@woody.linux-foundation.org`, 2007-05-06, <https://lore.kernel.org/all/alpine.LFD.0.98.0705060919010.25245%40woody.linux-foundation.org/>
- "The wait-queue traversal itself was never the problem, and stopping early was a premature optimization that causes these kinds of problems."  
  `CAHk-=wj_eqNh+gNhCQh3exrL5Pmo5hbZBcL0W-4Ah_Nw0Kegzw@mail.gmail.com`, 2026-11-23, <https://lore.kernel.org/all/CAHk-%3Dwj_eqNh%2BgNhCQh3exrL5Pmo5hbZBcL0W-4Ah_Nw0Kegzw%40mail.gmail.com/>
- "It's not performance-critical code, and if it ever is, it needs to be rewritten anyway."  
  `CAHk-=wgSzPwzX0cHgTZ9SQrd8XWQcMnLkBCo_-710pLTEBFGYQ@mail.gmail.com`, 2019-10-07, <https://lore.kernel.org/all/CAHk-%3DwgSzPwzX0cHgTZ9SQrd8XWQcMnLkBCo_-710pLTEBFGYQ%40mail.gmail.com/>
- "Because honestly, calling int_sqrt() once in a blue moon with caches cold and no branch prediction information tends to have very different performance characteristics from calling it"  
  `CA+55aFyBxxzNHH_z2BDNP5kmupSMa07wKK+6j=aURHN-tbMSQg@mail.gmail.com`, 2017-07-20, <https://lore.kernel.org/all/CA%2B55aFyBxxzNHH_z2BDNP5kmupSMa07wKK%2B6j%3DaURHN-tbMSQg%40mail.gmail.com/>

**How well supported.** About 25 messages, 2001 to 2026 (page cache 2001, git 2005 to 2007, data structures 2006, int_sqrt 2017, filldir 2019, ia64 2022, find_atomic 2024, vmware 2026, wait queues 2026). Well supported.

## 18. Trust measured hardware behaviour over manuals and theory; software rarely outsmarts the CPU

**Principle.** Architecture manuals, specs and theoretical models don't reliably describe how CPUs behave. Hints that try to manage the cache or pipeline from software (software prefetch, nontemporal stores, transactional memory, explicit cache control) usually lose on real hardware and across microarchitectures. Measure across several CPUs, and remove such hints when profiles show they hurt.

**What triggers it in a review.**
- `prefetch()` in generic iterators or list walks.
- Nontemporal or cache-bypassing copies in general-purpose code.
- Code justified by "the manual says" or "the spec guarantees" without testing on real parts.
- Optimisations tested on one microarchitecture and claimed as general.

**His reasoning.** "So sadly the architecture manuals do not reflect reality." Software prefetch "very seldom actually work[s]". Removing the hlist prefetch "actually IMPROVES PERFORMANCE" because `prefetch(NULL)` stalls and unneeded prefetches pollute the D$. "software almost never knows enough about the CPU cache to make an intelligent choice." Transactional memory "looks good in theory, but is just garbage in reality".

**How serious.** He removed prefetching from all generic list iterators himself (2011), and pushes back on prefetch in other subsystems unless tested across "a lot of different (micro-)architectures" (2016).

**Limits and exceptions.** Prefetch can help "MMX/media kind of code" with known access patterns (`Pine.LNX.4.64.0703071911330.10832@woody.linux-foundation.org`, 2007) and streaming RAID rebuilds (2016). He applied nontemporal copies when numbers showed a win (2009). *Change over time:* he was "quite excited about transactional memory" around 2013 and by 2023 called it garbage.

**Outside the kernel.** Transfers to compiler intrinsics (`_mm_prefetch`, `__builtin_expect` everywhere), JVM or GC tuning flags copied from blogs, hand-written SIMD tested on one CPU, and firmware relying on datasheet timing without measurement. Ask for measurements on the deployment hardware (including ARM servers and phones, not only the developer's x86 laptop).

**Evidence.**

- "So sadly the architecture manuals do not reflect reality."  
  `CAHk-=whxLURD=qsF3ijmQYxGRPSyjS8_zoxZz-AsD-7tmRBM0w@mail.gmail.com`, 2020-07-04, <https://lore.kernel.org/all/CAHk-%3DwhxLURD%3DqsF3ijmQYxGRPSyjS8_zoxZz-AsD-7tmRBM0w%40mail.gmail.com/>
- "That said, software prefetch instructions very seldom actually work."  
  `CAHk-=whxLURD=qsF3ijmQYxGRPSyjS8_zoxZz-AsD-7tmRBM0w@mail.gmail.com`, 2020-07-04, <https://lore.kernel.org/all/CAHk-%3DwhxLURD%3DqsF3ijmQYxGRPSyjS8_zoxZz-AsD-7tmRBM0w%40mail.gmail.com/>
- "Just don't expect the iterator to do it, since normally the downsides are bigger than the upsides."  
  `e66eed651fd18a961f11cda62f3b5286c8cc4f9f`, 2011-05-19, <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=e66eed651fd18a961f11cda62f3b5286c8cc4f9f>
- "Removing the prefetch actually IMPROVES PERFORMANCE."  
  `BANLkTim5MaJBYSuTnXfmOjgPNVOyZSgQuQ@mail.gmail.com`, 2011-05-19, <https://lore.kernel.org/all/BANLkTim5MaJBYSuTnXfmOjgPNVOyZSgQuQ%40mail.gmail.com/>
- "In general, I think that software should not mess with nontemporal stores. The thing is, software almost never knows enough about the CPU cache to make an intelligent choice."  
  `alpine.LFD.2.00.0902250753030.3111@localhost.localdomain`, 2009-02-25, <https://lore.kernel.org/all/alpine.LFD.2.00.0902250753030.3111%40localhost.localdomain/>
- "I was quite excited about transactional memory, but have (obviously) come to the conclusion that it was one of those "looks good in theory, but is just garbage in reality"."  
  `CAHk-=whjFwzEq0u04=n=t7-kNJdX0HkAOjAMjmLXDDycJ+j9yQ@mail.gmail.com`, 2023-01-16, <https://lore.kernel.org/all/CAHk-%3DwhjFwzEq0u04%3Dn%3Dt7-kNJdX0HkAOjAMjmLXDDycJ%2Bj9yQ%40mail.gmail.com/>
- "So I'm not categorically against prefetching, but it needs to be tested across a lot of different (micro-)architectures."  
  `CA+55aFzZ9-1dC9L_Q1xxKuKWKavP0eeB0YQjK0gzoBtKbDzSOw@mail.gmail.com`, 2016-10-07, <https://lore.kernel.org/all/CA%2B55aFzZ9-1dC9L_Q1xxKuKWKavP0eeB0YQjK0gzoBtKbDzSOw%40mail.gmail.com/>

**How well supported.** About 15 messages and commits, 2005 to 2023 (prefetch 2007 and 2011, nocache 2009, MD 2016, manuals 2020, TM 2023). Well supported.


## Changes of position over time

| Topic | Earlier | Later (current) | Evidence |
|---|---|---|---|
| Cost of indirect calls | 2002: predictable indirect calls expected to stay cheap, "getting _more_" common with OO languages | 2018 onward: Spectre or retpoline made them expensive; "the third thing that matters" on hot paths (2024). He converts syscall dispatch to a `switch` (2024 commit `1e3ad78334a6`) | `Pine.LNX.4.44.0212191519260.6279-100000@penguin.transmeta.com`; `CAHk-=wh9hc8sSNYwurp5cm2ub52yHYGfXC8=BfhuR3XgFr0vEA@mail.gmail.com` |
| Memory barriers | `rmb`/`wmb` pairs were the norm | 2024: acquire/release is now the preferred form; rmb/wmb is "the legacy way" | `CAHk-=wivmMgGiSnUm35WVm9=yNM1=jrHG4fgWo09XWwWZzvTMw@mail.gmail.com` |
| Transactional memory | About 2013: "quite excited", tried TSX for lockref | 2023: "garbage in reality" | `CAHk-=whjFwzEq0u04=n=t7-kNJdX0HkAOjAMjmLXDDycJ+j9yQ@mail.gmail.com`; `CA+55aFwzY_1tD5vmaDgwAGLXNSGw4XS8vEp9vOpN6NPm5+Mxow@mail.gmail.com` (2013) |
| Software prefetch | Generic list iterators prefetched | 2011: removed from all generic iterators; 2020: "very seldom actually work" | `e66eed651fd1`; `CAHk-=whxLURD=qsF3ijmQYxGRPSyjS8_zoxZz-AsD-7tmRBM0w@mail.gmail.com` |
| Microbenchmarks | 2010 to 2013: mostly dismissive ("irrelevant to real loads") | 2020 to 2024: still won't justify complexity with them, but says "those benchmarks do matter" when a regression is large, and applies fixes found by them | `CAHk-=wg_CoTOfkREgaQQA6oJ5nM9ZKYrTn=E1r-JnvmQcgWpSg@mail.gmail.com`; `CAHk-=wisa2xZHaCV=kh3seU-1kFDTjyWW9Ak3w5HH8nDvv7Snw@mail.gmail.com` |
| Meaning of `inline` | 2009: kernel `inline` should mean always inline; gcc's heuristics are broken | Later he uses `__always_inline` explicitly where it matters and argues against inlines in non-critical code (2018 to 2025). The two are consistent: fewer inlines, but reliable ones | `alpine.LFD.2.00.0901091731130.6528@localhost.localdomain`; `CAHk-=wjv-DkukaKb7f04WezyPjRERp=xfxv34j5fA8cDQ_JudA@mail.gmail.com` |
| Tone | Through 2018: profanity common in performance arguments ("HELL NO", "bullshit") | After late 2018 the substance is unchanged (still NAKs, still reverts) but personal insults are rarer; capitals and "garbage" remain (2024 "wake up and smell the coffee") | Compare 2013-02-13 and 2016-11-03 with 2024-02-25 and 2025-01-07 |

The positions themselves are remarkably stable from 2001 to 2026: real-load numbers, common-case fast paths, cache footprint, plain locks over clever ones. The changes above are about hardware facts (Spectre, ARM's acquire/release, TSX failing), not about principles.

## Not in corpus

- His 2020 Realworldtech post on user-space spinlocks and `sched_yield()` ("do not use spinlocks in user space unless you actually know what you're doing"): no Realworldtech posts are in the corpus (no URL matches `realworldtech`). Not quoted.
- His 2020 Realworldtech "I hope AVX512 dies a painful death": not found (only unrelated AVX-512 mentions in LKML).
- Knuth's "premature optimization is the root of all evil" in Linus's own words as a principle: not found. Only one passing use of "premature optimization" (2026).
- "Bad programmers worry about the code. Good programmers worry about data structures" **is** in the corpus (2006 git list) and is quoted above.
- The coding-style "inline disease" section is in `kernel-docs`, but its authorship is not clearly his, so I didn't quote it. Its content (no inline over about 3 lines unless constants fold) matches his mail.

## What I looked for and did not find (or found thinly)

- **Allocation in hot paths as a standalone rule.** I found little beyond "keep accounting hooks out of the hot path" (2024) and stack buffers for the common small case (2008). The principle is inferred from those plus the SLAB_ACCOUNT regression thread; evidence is thin.
- **Who may write lockless code.** No explicit "only maintainers X may write barriers" statement. The nearest are "In random non-core code ... I very much do not want random drivers doing micro-optimizations" (2025), "mortals are not supposed to really look at" the dcache lookup (2012 Slashdot, `https://meta.slashdot.org/story/12/10/11/0030249/linus-torvalds-answers-your-questions`), and repeated "use a lock". The core-versus-driver split is my inference.
- **Seqcounts specifically.** Several 2025 messages refine seqlock helper APIs (register use, clarity), and 2006 gives their constraints (atomic readers, writers must not break unsynchronised readers). I found no standalone rule beyond "RCU or seqlocks for read-mostly, else a regular lock".
- **Early era (1991 to 1999).** Usenet posts on performance are mostly user-facing tuning (swap counters, interrupt latency, context-switch asm). Nothing in my sample states review principles. The rules above are essentially 2000 onward.
- **Explicit statements on async I/O or event-loop performance** for user space (useful for transfer). Found only kernel-side io_uring and AIO discussion, and nothing generalisable beyond principle 1.
- **Lock ordering** beyond "document the rule" and "unlock order doesn't matter". I found no general method; lockdep is treated as the tool.

## Method note

I searched with about 60 FTS queries covering the brief's topics, using both annoyed vocabulary ("bullshit", "garbage", "NAK", "HELL NO", "disgusting code generation") and positive vocabulary ("pretty stunning", "I love this fix", "really like how this looks"), filtered to his own non-quoted lines. I skimmed match windows from roughly 450 distinct documents and read about 40 in full (the quoted ones whose context mattered, plus the 2023 transactional memory, 2013 spinlock NAK, 2013 VFS security cache, 2015 OOM, 2021 Rust, 2006 rwlock or RCU, 2008 git correctness, 2025 vsnprintf and 2001 rwsem messages). "How well supported" counts are counts of documents whose matched passages made the argument, not documents read end to end.
