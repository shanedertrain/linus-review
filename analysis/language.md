# Theme: language — Linus Torvalds on languages, type systems and compilers

Scope: C as he wants it written, macros, undefined behaviour, warnings, hidden control flow (C++), Rust, scripts and
tooling, generated code, standards. About 215 documents read in full or in large part (lore mail 1993–2026, commits,
yarchive, talks, interviews, Slashdot, blog). Every quote below is in `language.quotes.jsonl` and passed
`scripts/verify_quotes.py`.

Convention: **"Outside the kernel"** paragraphs are *my* generalisation unless they cite him. Where he himself drew the
line between kernel and user space, it is said explicitly.

The unifying idea, in my words: **source code is for humans, and it must mean what it plainly says.** The compiler
must not invent meaning (UB exploitation, type-based aliasing), the language must not hide meaning (exceptions,
implicit allocation, hidden assignments in macros, typedef'd pointers), and tools must not force code to say less than
it means (bad warnings, casts to silence them). Most principles below are applications of that.

---

## 1. The compiler must do what the code plainly says; turn off UB-exploiting optimisation

**Principle.** Treat "undefined behaviour" as "implementation-defined and boring", not as licence. Code generation
should follow the code as written; optimisations are fine only when they can be shown to make no difference on real
hardware. Where a toolchain offers flags that remove UB-based optimisation, use them.

**What triggers it.**
- A null check after a dereference that the compiler may delete; signed-overflow checks written as `if (a + b < a)`.
- Arguments of the form "the standard says this is undefined, so the compiler may…" used to justify a miscompile or
  to reject a bug report.
- A build that drops `-fno-strict-overflow`, `-fno-delete-null-pointer-checks`, `-fno-strict-aliasing`.

```c
struct foo *p = get();
int x = p->field;   /* compiler infers p != NULL ... */
if (!p) return;     /* ... and deletes this check. Benign bug -> exploit. */
```

**His reasoning.** Every nontrivial project has dodgy code, and it was tested with compilers that did not go out of
their way to produce "legal but idiotic" code (2007). UB-based optimisation buys a few ALU ops in some loops at the
price of subtle security bugs (2025). "Implementation-defined" at least forces *some* well-defined behaviour;
"undefined" lets code far away change the generated code (2022). An optimisation is legitimate if it is based on what
the hardware does, not on what the standard permits (2018).

**How serious.** Kernel-wide policy: the flags are in the top-level Makefile and he refuses compiler changes that
would require removing them. He blames the compiler, not the code, in such bug reports.

**Limits.** He is not against optimisation: proving "I can do it better and it makes no difference" from the code as
written is fine (2019). He accepts "slightly worse code generation" as the price (2025). He does not claim the code
was correct; the point is that a bug should stay a bug and not become an exploit.

**Outside the kernel.** Transfers directly to C/C++ services and firmware (use `-fwrapv`/`-fno-strict-overflow`,
sanitizers in test). For Rust: review `unsafe` blocks for code that relies on the compiler *not* exploiting UB
(see §6). For Python/TypeScript the analogue (mine) is relying on unspecified engine behaviour (dict ordering pre-3.7,
`Array.prototype.sort` stability in old engines): write code whose meaning does not depend on it.

**Evidence.**
- "Optimizations based on undefined behavior are wrong. If you have to resort to those kinds of optimizations, your compiler is bad."  
  `CAHk-=wjqtMfRySaBoShSivAL3SYbYDTEUz-hbc4xXSNUrpSaGg@mail.gmail.com`, 2024-02-09, <https://lore.kernel.org/all/CAHk-%3DwjqtMfRySaBoShSivAL3SYbYDTEUz-hbc4xXSNUrpSaGg%40mail.gmail.com/>
- "Removing the NULL pointer check turned a benign bug into a trivially exploitable one"  
  `CA+55aFyZA5t-+OyzSDDPGjDoaKsh=Erz8zuoEdDo7hOCBU6ZfQ@mail.gmail.com`, 2018-04-04, <https://lore.kernel.org/all/CA%2B55aFyZA5t-%2BOyzSDDPGjDoaKsh%3DErz8zuoEdDo7hOCBU6ZfQ%40mail.gmail.com/>
- "It's ok to do optimizations that are based on "hardware does the exact same thing", but not on "the standard says this is undefined so we can remove it"."  
  `CA+55aFyZA5t-+OyzSDDPGjDoaKsh=Erz8zuoEdDo7hOCBU6ZfQ@mail.gmail.com`, 2018-04-04, <https://lore.kernel.org/all/CA%2B55aFyZA5t-%2BOyzSDDPGjDoaKsh%3DErz8zuoEdDo7hOCBU6ZfQ%40mail.gmail.com/>
- "For the kernel, we basically do not accept "that's undefined behavior, I might generate odd code"."  
  `CAHk-=wjGd0Ce2xadkiErPWxVBT2mhyeZ4TKyih2sJwyE3ohdHw@mail.gmail.com`, 2019-11-12, <https://lore.kernel.org/all/CAHk-%3DwjGd0Ce2xadkiErPWxVBT2mhyeZ4TKyih2sJwyE3ohdHw%40mail.gmail.com/>
- "Overflow isn't undefined in the kernel. Aliasing isn't undefined in the kernel."  
  `CAHk-=wgq1DvgNVoodk7JKc6BuU1m9UnoN+k=TLtxCAL7xTP=Dg@mail.gmail.com`, 2025-02-22, <https://lore.kernel.org/all/CAHk-%3Dwgq1DvgNVoodk7JKc6BuU1m9UnoN%2Bk%3DTLtxCAL7xTP%3DDg%40mail.gmail.com/>
- "The end result: any nontrivial project always has dodgy code. Because people simply don't write perfect code."  
  `Pine.LNX.4.64.0701040937460.3661@woody.osdl.org`, 2007-01-04, <https://lore.kernel.org/all/Pine.LNX.4.64.0701040937460.3661%40woody.osdl.org/>

**Support.** ~18 messages, 2003–2026 (consistent throughout; strongest 2016–2025).

---

## 2. Type-based ("strict") aliasing is wrong; aliasing must follow what the code actually does

**Principle.** A compiler or language must not assume two pointers don't alias because their types differ. Aliasing
decisions should come from provenance or explicit annotation, never from the declared types.

**What triggers it.** Type-punning through unions or casts that "works" only with `-fno-strict-aliasing`; code
review comments asking to rewrite perfectly clear punning through `memcpy` to satisfy the standard; any proposal to
build the kernel (or a C codebase) without `-fno-strict-aliasing`; in Rust, `unsafe` code where the compiler is
allowed to assume `&mut` uniqueness that the programmer did not mean.

**His reasoning.** Type-based aliasing "ignores actual real aliasing even if it exists" and makes decisions "on
entirely made-up grounds" (2024). What gcc does may be legal but is bad quality of implementation (2007). He prefers
the Rust model on this point (2024). The key distinction (2025): the *programmer* doing something unsafe is
acceptable; the *compiler* doing something unsafe silently is not.

**How serious.** Hard policy since at least 1999 (yarchive "norestrict" proposal) through 2026 ("need to just die").

**Limits.** He accepts explicit, programmer-stated non-aliasing (`restrict`-like) because it is visible in the code.
He accepts some code-generation cost.

**Outside the kernel.** C/C++: build with `-fno-strict-aliasing` or review punning carefully. Rust: unsafe code
should not create references whose aliasing guarantees the author did not intend; prefer raw pointers in such code.
The general rule (mine): optimisation assumptions must be things the author wrote, not things the tool inferred from
incidental declarations.

**Evidence.**
- "Strict aliasing is a *horrible* mistake."  
  `CAHk-=wgQy+FRKjO_BvZgZN56w6-+jDO8p-Mt=X=zM70CG=CVBQ@mail.gmail.com`, 2024-03-27, <https://lore.kernel.org/all/CAHk-%3DwgQy%2BFRKjO_BvZgZN56w6-%2BjDO8p-Mt%3DX%3DzM70CG%3DCVBQ%40mail.gmail.com/>
- "The fact that Rust doesn't do the C strict aliasing is a good thing. Really."  
  `CAHk-=wgQy+FRKjO_BvZgZN56w6-+jDO8p-Mt=X=zM70CG=CVBQ@mail.gmail.com`, 2024-03-27, <https://lore.kernel.org/all/CAHk-%3DwgQy%2BFRKjO_BvZgZN56w6-%2BjDO8p-Mt%3DX%3DzM70CG%3DCVBQ%40mail.gmail.com/>
- "So what gcc does may be technically legal, but it's still a horribly bad thing to do."  
  `Pine.LNX.4.64.0703242123310.6730@woody.linux-foundation.org`, 2007-03-25, <https://lore.kernel.org/all/Pine.LNX.4.64.0703242123310.6730%40woody.linux-foundation.org/>
- "Just accept that things alias, and that you might sometimes get slightly worse code generation. Nobody cares."  
  `CAHk-=wgMnSOnaddFzfAFwjT-dGO9yeSkv6Lt21LgWmCKYCM7cg@mail.gmail.com`, 2025-02-25, <https://lore.kernel.org/all/CAHk-%3DwgMnSOnaddFzfAFwjT-dGO9yeSkv6Lt21LgWmCKYCM7cg%40mail.gmail.com/>
- "The strict aliasing rules are garbage and need to just die."  
  `CAHk-=wg37rxdKbvLDR2OuzYOD_15Fycko4e1Yg=2Gj3TU=muPA@mail.gmail.com`, 2026-02-11, <https://lore.kernel.org/all/CAHk-%3Dwg37rxdKbvLDR2OuzYOD_15Fycko4e1Yg%3D2Gj3TU%3DmuPA%40mail.gmail.com/>
- "In one case, the *programmer* is doing something unsafe. And in the other, the *compiler* is doing something unsafe."  
  `CAHk-=whGY2uYcXog8kmuAAAPJy4R84Jy9rEfXfoHBe-evmuYDQ@mail.gmail.com`, 2025-02-25, <https://lore.kernel.org/all/CAHk-%3DwhGY2uYcXog8kmuAAAPJy4R84Jy9rEfXfoHBe-evmuYDQ%40mail.gmail.com/>

**Support.** ~10 messages, 1999–2026.

---

## 3. Wrap-around is defined and useful; target dangerous overflow specifically; trapping is not "safe"

**Principle.** Do not treat all arithmetic overflow as a bug. Unsigned wrap is well defined and deliberately used
(hashes, sequence numbers, ring indices). Find the specific dangerous cases (sizes for allocation, implicit
conversion to unsigned, pointer arithmetic) and check them at an explicit point with an explicit error path. Crashing
on overflow is not a safety mechanism.

**What triggers it.**
- Tree-wide patches that annotate or rewrite every wrapping expression to please a sanitizer.
- New types or attributes that make arithmetic trap, defined far from where the arithmetic happens.
- Overflow checks with no way to handle the failure.

```c
/* He wants this shape: explicit check, explicit exit */
if (check_add_overflow(a, b, &sum))
        return -EOVERFLOW;
/* not: a type declared elsewhere that silently turns "a + b" into a BUG() */
```

**His reasoning.** Tools that warn about good code (hash functions) are horrible: false positives make real
warnings worthless (2024). Unsigned wrap is neither a "sanitizer" issue nor UB (2024). A trap type is "completely
invisible in the context of the code" because the type may be declared somewhere else (2026). "A dead machine is
not a safe machine"; the only safe trapping is one with a clear, simple way to *handle* it (2026). He proposed an
`add_overflow(a, b, label)` shape: an exception with an explicit exit label.

**How serious.** NAK of mindless conversion patches (2024-01); NAK of trap types (2026-03). Repeated long arguments
with the hardening people.

**Limits.** He accepts and wants checked arithmetic where a size goes to an allocator or a user-controlled value
indexes memory, and he accepted helpers like `check_add_overflow`, `struct_size`, `array_size`. He agrees implicit
conversion to unsigned is a real bug class worth targeting.

**Outside the kernel.** Transfers well. Rust: `wrapping_*` vs `checked_*` vs default-panic-in-debug is exactly this
argument; a reviewer should ask whether a `checked_` result is *handled* (returns `Err`), not `unwrap()`ed. Python
has no overflow but the same logic applies to blanket validators: (mine) a check without a handling path just moves
the crash. In services, "panic on bad input" is a denial of service, not safety.

**Evidence.**
- "False positive warnings make real warnings worthless."  
  `CAHk-=wgoE5EkH+sQwi4KhRhCZizUxwZAnC=+9RbZcw7g6016LQ@mail.gmail.com`, 2024-05-08, <https://lore.kernel.org/all/CAHk-%3DwgoE5EkH%2BsQwi4KhRhCZizUxwZAnC%3D%2B9RbZcw7g6016LQ%40mail.gmail.com/>
- "Think of it as wrong in _specific_ cases, and see if you can target those cases."  
  `CAHk-=wgoE5EkH+sQwi4KhRhCZizUxwZAnC=+9RbZcw7g6016LQ@mail.gmail.com`, 2024-05-08, <https://lore.kernel.org/all/CAHk-%3DwgoE5EkH%2BsQwi4KhRhCZizUxwZAnC%3D%2B9RbZcw7g6016LQ%40mail.gmail.com/>
- "stop calling the unsigned wrap-around a "sanitizer" and talking about "undefined behavior" in the same sentence, since it's neither."  
  `CAHk-=wgMPVv-mDxA2qcywpLCRLojtaKmP13h7bVo4m=XN202xA@mail.gmail.com`, 2024-01-23, <https://lore.kernel.org/all/CAHk-%3DwgMPVv-mDxA2qcywpLCRLojtaKmP13h7bVo4m%3DXN202xA%40mail.gmail.com/>
- "Stop thinking that trapping is "safe"."  
  `CAHk-=wg=q7ptcMyUAqPGDbX_DKHivJVppc8bP0zpQqzOky_avA@mail.gmail.com`, 2026-03-31, <https://lore.kernel.org/all/CAHk-%3Dwg%3Dq7ptcMyUAqPGDbX_DKHivJVppc8bP0zpQqzOky_avA%40mail.gmail.com/>
- "A dead machine is not a safe machine."  
  `CAHk-=wg=q7ptcMyUAqPGDbX_DKHivJVppc8bP0zpQqzOky_avA@mail.gmail.com`, 2026-03-31, <https://lore.kernel.org/all/CAHk-%3Dwg%3Dq7ptcMyUAqPGDbX_DKHivJVppc8bP0zpQqzOky_avA%40mail.gmail.com/>
- "is completely invisible in the context of the code, because the type may be somewhere very different"  
  `CAHk-=whjwHjmB0_2yXsOjDa7Mi_yFSx3AMd3vGk5r70WocvZZg@mail.gmail.com`, 2026-03-31, <https://lore.kernel.org/all/CAHk-%3DwhjwHjmB0_2yXsOjDa7Mi_yFSx3AMd3vGk5r70WocvZZg%40mail.gmail.com/>

**Support.** ~9 messages, 2015–2026.

---

## 4. Interactions must be locally visible: no hidden allocation, control flow, lifetimes or conversions

**Principle.** A reader should be able to tell what a line does — whether it allocates, can fail, can jump away,
runs code on scope exit, or converts types — from the line and its immediate context. Language features that hide
these (the C++ set: exceptions, implicit constructors/destructors, operator overloading, implicit conversions, deep
library abstraction like STL/Boost) are rejected for that reason, not because they are C++.

**What triggers it.**
- A call or operator that may allocate without that being visible (`a + b` on a big-number or string type, a
  constructor that opens a file).
- Implicit conversions between user types; overloaded operators with side effects.
- An abstraction layer that every caller now depends on, so a performance mistake in it cannot be fixed without a
  rewrite.
- Casts that a stricter type system forces you to add, which then hide the real problem.

**His reasoning.** "Interactions should be *locally* visible" (2007). Memory allocation is among the biggest
performance issues, so it has to be explicit (2007). Languages that hide allocation are a bad choice for a kernel
(2004). Abstracted object models lock you in: two years later you find the abstraction was inefficient and cannot fix
it (2007). C++ offers no new safety and forces more casts (2021). He states the objection in terms of mental baggage,
not syntax: "You can write bad code in any language" (2007).

**How serious.** C++ in the kernel is a closed question (2004, 2006, 2007, 2021). In review, hidden allocation or
hidden control flow in a new helper is a reason to ask for a rework.

**Limits.** He likes explicit abstraction: templates and an integrated preprocessor are the good parts of C++ (2007);
he wants an explicit opt-in garbage collector rather than none (2007); sparse's `__user` annotation, an explicit
type-system extension, "is a VERY GOOD THING" (2007). In a 2024 talk he says Subsurface is now almost entirely C++ "but it's not a language I like": he
tolerates it in user space when others maintain it. Scope-based cleanup became acceptable once it was explicit (§14).

**Outside the kernel.** This is the most transferable principle in the theme. Applied by me to:
- Python: properties and `__getattr__` that do I/O; `__del__`; decorators that swallow exceptions; implicit network
  calls inside ORM attribute access.
- TypeScript: getters with side effects; implicit `async` work hidden in constructors; deep framework abstractions
  callers cannot see through.
- Rust: `Deref` abuse, `Drop` impls with surprising side effects, operator overloads that allocate, `?` conversions
  through `From` that silently change error types.
Operator overloading is not attacked by name in the corpus (see "not found"); it falls under his argument about
implicit behaviour and explicit syntax.

**Evidence.**
- "But I'm also a huge believer in *explicit*syntax*. People should see what is going on, and the abstraction should be explicit."  
  `alpine.LFD.0.999.0709230911360.16478@woody.linux-foundation.org`, 2007-09-23, <https://lore.kernel.org/all/alpine.LFD.0.999.0709230911360.16478%40woody.linux-foundation.org/>
- "If you need to understand the "big picture" in order to understand what a line of code does, that's usually a bad idea."  
  `alpine.LFD.0.999.0709230911360.16478@woody.linux-foundation.org`, 2007-09-23, <https://lore.kernel.org/all/alpine.LFD.0.999.0709230911360.16478%40woody.linux-foundation.org/>
- "Memory allocation issues are often some of the *biggest* performance issues, and that means that they have to be explicit."  
  `alpine.LFD.0.999.0709230911360.16478@woody.linux-foundation.org`, 2007-09-23, <https://lore.kernel.org/all/alpine.LFD.0.999.0709230911360.16478%40woody.linux-foundation.org/>
- "any compiler or language that likes to hide things like memory allocations behind your back just isn't a good choice for a kernel."  
  `Pine.LNX.4.58.0401192241080.2311@home.osdl.org`, 2004-01-20, <https://lore.kernel.org/all/Pine.LNX.4.58.0401192241080.2311%40home.osdl.org/>
- "inefficient abstracted programming models where two years down the road you notice that some abstraction wasn't very efficient, but now all your code depends on all the nice object models around it, and you cannot fix it without rewriting your app."  
  `alpine.LFD.0.999.0709061839510.5626@evo.linux-foundation.org`, 2007-09-06, <https://lore.kernel.org/all/alpine.LFD.0.999.0709061839510.5626%40evo.linux-foundation.org/>
- "It forces you to use _more_ casts, which then just make for more problems when it turns out the casts were incorrect and hid the real problem."  
  `CAHk-=wjYGDtLafGB6wabjZCyPUiTJSda0c8h5+_8BeFNdCdrNg@mail.gmail.com`, 2021-07-07, <https://lore.kernel.org/all/CAHk-%3DwjYGDtLafGB6wabjZCyPUiTJSda0c8h5%2B_8BeFNdCdrNg%40mail.gmail.com/>

**Support.** ~14 messages, 2004–2026.

---

## 5. Exceptions: explicit, synchronous exits are fine; asynchronous or nested ones are not; goto is fine

**Principle.** Error handling should leave the normal path readable and make the exit point explicit. Labels,
`goto out`, `asm goto` style "exception tables" and `Result` returns are good. Mechanisms where any call can throw
and unwinding is implicit (C++ exceptions, setjmp/longjmp) are not.

**What triggers it.** Deep nesting to avoid `goto`; mandatory try/catch spread through code; errors propagated by
unwinding through code that holds locks; macro-hidden early returns.

```c
        if (unsafe_get_user(x, ptr, Efault))   /* explicit exit label */
        ...
Efault:
        user_access_end();
        return -EFAULT;
```

**His reasoning.** Exception handling *done right* means the normal flow stays normal and errors are dealt with
separately; error handling exits, it does not nest (2026). Asynchronous exceptions are horrific for performance
(setjmp) (2025). C++ exception handling is fundamentally broken, especially for kernels (2004). Gotos are often more
readable than indentation (2003).

**How serious.** Design-level; he rejects macros that hide returns or contain code in their arguments (2025).

**Limits.** "goto is fine, as long as you have legible syntax and don't use it to generate spaghetti code" (2025).
He welcomed an overflow multiply with an error label as a "hand-coded try/catch" (2015).

**Outside the kernel.** Rust's `?` with `Result` fits his model (explicit at each call site). In Python/TypeScript
(mine): exceptions are idiomatic and can't be avoided, so apply the underlying test — is it visible where control can
leave, and is cleanup tied to that exit (`with`, `try/finally`)? Flag broad `except:`/`catch {}` that hide errors,
and exceptions used for normal control flow.

**Evidence.**
- "Asynchronous exceptions are horrific and tend to cause huge performance problems (think setjmp())."  
  `CAHk-=wibAE=yDhWdY7jQ7xvCtbmW5Tjtt_zMJcEzey3xfL=ViA@mail.gmail.com`, 2025-08-18, <https://lore.kernel.org/all/CAHk-%3DwibAE%3DyDhWdY7jQ7xvCtbmW5Tjtt_zMJcEzey3xfL%3DViA%40mail.gmail.com/>
- "And "goto" is fine, as long as you have legible syntax and don't use it to generate spaghetti code."  
  `CAHk-=wibAE=yDhWdY7jQ7xvCtbmW5Tjtt_zMJcEzey3xfL=ViA@mail.gmail.com`, 2025-08-18, <https://lore.kernel.org/all/CAHk-%3DwibAE%3DyDhWdY7jQ7xvCtbmW5Tjtt_zMJcEzey3xfL%3DViA%40mail.gmail.com/>
- "IOW, exception handling means that you can continue to use the normal flow of code for the normal case, and you deal with errors separately."  
  `CAHk-=wgKB5f3MM40FGGUWUm_9eyESe2PAqCa6uZ=YTi0CdPwDg@mail.gmail.com`, 2026-03-31, <https://lore.kernel.org/all/CAHk-%3DwgKB5f3MM40FGGUWUm_9eyESe2PAqCa6uZ%3DYTi0CdPwDg%40mail.gmail.com/>
- "Error handling does not nest: it exits."  
  `CAHk-=wgKB5f3MM40FGGUWUm_9eyESe2PAqCa6uZ=YTi0CdPwDg@mail.gmail.com`, 2026-03-31, <https://lore.kernel.org/all/CAHk-%3DwgKB5f3MM40FGGUWUm_9eyESe2PAqCa6uZ%3DYTi0CdPwDg%40mail.gmail.com/>
- "the whole C++ exception handling thing is fundamentally broken. It's _especially_ broken for kernels."  
  `Pine.LNX.4.58.0401192241080.2311@home.osdl.org`, 2004-01-20, <https://lore.kernel.org/all/Pine.LNX.4.58.0401192241080.2311%40home.osdl.org/>
- "I think goto's are fine, and they are often more readable than large amounts of indentation."  
  `Pine.LNX.4.44.0301121134340.14031-100000@home.transmeta.com`, 2003-01-12, <https://lore.kernel.org/all/Pine.LNX.4.44.0301121134340.14031-100000%40home.transmeta.com/>

**Support.** ~8 messages, 2003–2026.

---

## 6. Rust (a): kernel rules beat language rules — no panics, fallible allocation, no context-dependent behaviour

**Principle.** A language brought into an existing system must follow the system's rules, not its own defaults.
For Rust in the kernel that means: no implicit panics on allocation failure or other runtime errors, allocation
returns `Result`, no behaviour that silently changes with context (atomic vs sleeping), and the kernel memory model
(LKMM) rather than the C++/Rust one.

**What triggers it.** `unwrap()`/`expect()` on fallible kernel ops; infallible `Box::new`/`Vec::push` that panic on
OOM; APIs that pick a different allocation strategy depending on whether they are in atomic context; "safety" arguments
that amount to "panicking is safer than continuing".

**His reasoning.** Unsafe conditions must be caught at compile time or handled as a regular error (2021). An
allocation failure in a driver must never become a panic (2021). Not completing an operation is not better than
the wrong answer, only more debuggable; prefer WARN_ON_ONCE and continue (2022). Behaviour that changes with context
is "a total disaster" (2022). He likes static checking — "as much as possible should be done 100% statically" (2022)
— but runtime checks must not kill the machine.

**How serious.** Preconditions for merging Rust (2021–2022); stated to Rust developers in strong terms.

**Limits.** Static guarantees are welcome. He does not reject `Result`; he asked for it.

**Outside the kernel.** For any long-running service in any language (mine): a library must not panic/abort/`exit`
on recoverable errors; return errors and let the caller choose. Reviewers should flag `unwrap()` in Rust library
code, `process.exit` in TypeScript library code, `sys.exit` in Python libraries. The "host rules beat language rules"
point applies to any embedded runtime (plugin systems, FFI layers).

**Evidence.**
- "Unsafe code has to either be caught at compile time, or it has to be handled dynamically as just a regular error."  
  `CAHk-=wh_sNLoz84AUUzuqXEsYH35u=8HV3vK-jbRbJ_B-JjGrg@mail.gmail.com`, 2021-04-14, <https://lore.kernel.org/all/CAHk-%3Dwh_sNLoz84AUUzuqXEsYH35u%3D8HV3vK-jbRbJ_B-JjGrg%40mail.gmail.com/>
- "An allocation failure in some random driver must never ever be something that the compiler just turns into a panic."  
  `CAHk-=wiVY56LzwV_G075NEFwsdf-p7GOTy_cB7-UU9b=49rB1g@mail.gmail.com`, 2021-04-14, <https://lore.kernel.org/all/CAHk-%3DwiVY56LzwV_G075NEFwsdf-p7GOTy_cB7-UU9b%3D49rB1g%40mail.gmail.com/>
- "Not completing the operation at all, is *not* really any better than getting the wrong answer, it's only more debuggable."  
  `CAHk-=whm5Ujw-yroDPZWRsHK76XxZWF1E9806jNOicVTcQC6jw@mail.gmail.com`, 2022-09-19, <https://lore.kernel.org/all/CAHk-%3Dwhm5Ujw-yroDPZWRsHK76XxZWF1E9806jNOicVTcQC6jw%40mail.gmail.com/>
- "I really need you to understand that Rust in the kernel is dependent on *kernel* rules."  
  `CAHk-=whm5Ujw-yroDPZWRsHK76XxZWF1E9806jNOicVTcQC6jw@mail.gmail.com`, 2022-09-19, <https://lore.kernel.org/all/CAHk-%3Dwhm5Ujw-yroDPZWRsHK76XxZWF1E9806jNOicVTcQC6jw%40mail.gmail.com/>
- "But having *behavior changes* depending on context is a total disaster."  
  `CAHk-=wgaBaVaK2K=N05fwWSSLM6YJx=yLmP4f7j6d6o=nCAtdw@mail.gmail.com`, 2022-09-19, <https://lore.kernel.org/all/CAHk-%3DwgaBaVaK2K%3DN05fwWSSLM6YJx%3DyLmP4f7j6d6o%3DnCAtdw%40mail.gmail.com/>
- "I think that compile-time static checking is wonderful, and as much as possible should be done 100% statically so that people cannot write incorrect programs."  
  `CAHk-=wityPWw4YkHeMNU4iGanyiC3UwDRhbOHYCJrhB2paCGwA@mail.gmail.com`, 2022-09-19, <https://lore.kernel.org/all/CAHk-%3DwityPWw4YkHeMNU4iGanyiC3UwDRhbOHYCJrhB2paCGwA%40mail.gmail.com/>

**Support.** ~10 messages, 2020–2022, reiterated 2025.

---

## 7. Rust (b): unsafe is the core, safe is a wrapper; the compiler must be humble in unsafe code

**Principle.** Build the powerful primitive on `unsafe`, then wrap it in safe, simple interfaces; don't design the
whole system around the safe subset. Inside `unsafe`, the compiler should assume as little as possible; semantics
should be defined by behaviour, not by types.

**What triggers it.** Contorted designs to stay in safe Rust where a small unsafe core would be simpler; unsafe
code that creates references the optimiser can exploit (aliasing, validity) beyond what the author meant; abstractions
for atomics or MMIO built from high-level types instead of primitive operations.

**His reasoning.** "the *unsafe* part is what makes Rust powerful"; basing the whole design on the safe part makes
a straitjacket (2024). In unsafe mode the compiler should assume it does not understand what is going on (2025).
Semantics defined in terms of behaviour, not syntax and types (2025).

**How serious.** Design guidance to Rust-for-Linux; not merge-blocking per se.

**Limits.** He still wants safe interfaces at the boundary; he is not inviting unsafe everywhere.

**Outside the kernel.** Directly applicable to Rust reviews: small audited unsafe core, safe API, `SAFETY:` comments,
raw pointers over references where aliasing is unclear. My extension to TypeScript: a small `any`/cast-heavy core
behind a well-typed interface is better than type gymnastics everywhere.

**Evidence.**
- "But the *unsafe* part is what makes Rust powerful."  
  `CAHk-=wjwxKD9CxYsf5x+K5fJbJa_JYZh1eKB4PT5cZJq1+foGw@mail.gmail.com`, 2024-03-26, <https://lore.kernel.org/all/CAHk-%3DwjwxKD9CxYsf5x%2BK5fJbJa_JYZh1eKB4PT5cZJq1%2BfoGw%40mail.gmail.com/>
- "You can - and should - wrap the powerful model with safer and simpler interfaces."  
  `CAHk-=wjwxKD9CxYsf5x+K5fJbJa_JYZh1eKB4PT5cZJq1+foGw@mail.gmail.com`, 2024-03-26, <https://lore.kernel.org/all/CAHk-%3DwjwxKD9CxYsf5x%2BK5fJbJa_JYZh1eKB4PT5cZJq1%2BfoGw%40mail.gmail.com/>
- "In unsafe mode, the compiler should always just basically assume "I don't understand what is going on, so I'm not going to _think_ I understand what is going on"."  
  `CAHk-=whGY2uYcXog8kmuAAAPJy4R84Jy9rEfXfoHBe-evmuYDQ@mail.gmail.com`, 2025-02-25, <https://lore.kernel.org/all/CAHk-%3DwhGY2uYcXog8kmuAAAPJy4R84Jy9rEfXfoHBe-evmuYDQ%40mail.gmail.com/>
- "100% convinced that the semantics of a language *should* be defined in terms of behavior, not in terms of syntax and types."  
  `CAHk-=wh=8sqvB-_TkwRnvL7jVA_xKbzsy9VH-GR93brSxTp60w@mail.gmail.com`, 2025-02-26, <https://lore.kernel.org/all/CAHk-%3Dwh%3D8sqvB-_TkwRnvL7jVA_xKbzsy9VH-GR93brSxTp60w%40mail.gmail.com/>

**Support.** ~6 messages, 2024–2025.

---

## 8. Rust (c): his position up to 2026 — augment, don't replace; maintainers cannot veto users

**Principle (for the reviewer).** Judge Rust (or any new language in a codebase) on the code, not on the language
fight. It fixes some bug classes, not logic errors. A maintainer of an interface does not get to forbid a new
language's users of it.

**What triggers it.** Reviews that reject a change because of its language; claims that a rewrite in a memory-safe
language removes the need to review logic; the inverse, gratuitous rewrites of working code.

**His reasoning and timeline.**
| Year | Position (from corpus) |
|---|---|
| 2020 | Rust support should be build-tested by default, not a niche config |
| 2021 | "augment our C code where it makes sense", not "replace C" (interview) |
| 2021–22 | Conditions: no panics, `Result`, kernel rules (§6) |
| 2024 | "not a language I love" but has not reached active dislike (talk); finds it hard to read |
| 2025-02 | Maintainers cannot control who uses their code; "how many problems has rust caused you in the last year?" |
| 2025-10 | Complains about rustfmt's `use` heuristics hurting merges (§19) |
| 2025-12 | 6.19-rc1: phase moving from infrastructure to "actual driver and subsystems development" |
| 2026-02 | Complains Rust builds serialise (tooling cost) |
| 2026-07 | Talk: Rust fixes easy bugs, not logic errors; C still "a much simpler tool" for him; enthusiastic about C verification tooling |

**How serious.** 2025-02 is a policy statement against blocking Rust users of C APIs.

**Limits.** He is pragmatic, not a convert. He will not mandate Rust and keeps C primary.

**Outside the kernel.** (Mine) A reviewer should neither praise nor penalise code for its language; review memory
safety *and* logic in safe languages. Rewrites need a reason.

**Evidence.**
- "So let me be very clear: if you as a maintainer feel that you control who or what can use your code, YOU ARE WRONG."  
  `CAHk-=wgLbz1Bm8QhmJ4dJGSmTuV5w_R0Gwvg5kHrYr4Ko9dUHQ@mail.gmail.com`, 2025-02-21, <https://lore.kernel.org/all/CAHk-%3DwgLbz1Bm8QhmJ4dJGSmTuV5w_R0Gwvg5kHrYr4Ko9dUHQ%40mail.gmail.com/>
- "rust is not a language I love but at the same time it doesn't have it hasn't reached the point where I actively dislike it either"  
  `https://www.youtube.com/watch?v=s4wlrxFf2lM`, 2024-10-17, <https://www.youtube.com/watch?v=s4wlrxFf2lM>
- "Rust fixes a few easy bugs that you can make in C, but it does not fix the logic errors, right? It does not think for you."  
  `https://www.youtube.com/watch?v=YKkEe-PxW10`, 2026-07-01, <https://www.youtube.com/watch?v=YKkEe-PxW10>
- "I still find C to be a much simpler tool."  
  `https://www.youtube.com/watch?v=YKkEe-PxW10`, 2026-07-01, <https://www.youtube.com/watch?v=YKkEe-PxW10>
- "The "mainly preparation and infrastructure" phase is starting to become "actual driver and subsystems development"."  
  `CAHk-=wgizos80st3bL3EoEoh0+07u9zRjsw45M+RS-js-bcwag@mail.gmail.com`, 2025-12-14, <https://lore.kernel.org/all/CAHk-%3Dwgizos80st3bL3EoEoh0%2B07u9zRjsw45M%2BRS-js-bcwag%40mail.gmail.com/>
- "So it's not "replace C", but more of "augment our C code where it makes sense"."  
  `https://www.tag1.com/blog/interview-linus-torvalds-linux-and-git/`, 2021-04-28, <https://www.tag1.com/blog/interview-linus-torvalds-linux-and-git/>

**Support.** ~16 documents (mail + 3 talks + 1 interview), 2020–2026.

---

## 9. A warning is good only if fixing it improves the code; fix problems, not warnings

**Principle.** Keep warnings whose fix makes code better (assignment in `if`, missing prototypes, `sizeof` of an
array parameter, shift overflow). Disable warnings whose silencing makes code worse (casts, removed checks, dummy
initialisers). Patches should fix real problems; "remove warning" is not a goal.

**What triggers it.**
- Casts added only to silence `-Wsign-compare`/`-Wpointer-sign`.
- A removed `x < 0` check on an unsigned (now) variable because of `-Wtype-limits`; it becomes a bug when the type
  later turns signed.
- `= 0` or `uninitialized_var()` added only to quiet maybe-uninitialized.
- `#pragma` to locally disable a warning.

```c
/* -Wtype-limits wants this "fixed": */
if (idx < 0 || idx >= max) return -EINVAL;
/* Removing "idx < 0" is wrong: idx's type may change, and both ends make intent clear. */
```

**His reasoning.** A bad warning "CAUSES PEOPLE TO WRITE WORSE CODE" (2007); it is "the literal reverse of a safety
net" (2025). Do not confuse a broken warning with a good one that also fires on your code (2025). Range checks with
both ends are always good (2025). False positives make real warnings worthless (2024). He praised the array-argument
`sizeof` warning — "this one is a keeper" (2015).

**How serious.** He moves or disables whole warnings (maybe-uninitialized to W=2 in 2020; -Wshadow, -Wpointer-sign,
-Wshift-negative-value off) and rejects warning-fix patches that add casts.

**Limits.** He does want warnings he might miss to be visible (2020), and he wants the build clean (§10). Good
warnings are kept even if noisy at first.

**Outside the kernel.** Transfers to linters: `eslint-disable`, `# type: ignore`, `# noqa`, `#[allow(...)]`, `as
any` and `!` non-null assertions are the modern casts. A reviewer should ask whether the lint fix made the code
better; if not, the lint rule may be the problem. (Mine: same for clippy pedantic lints.)

**Evidence.**
- "IT CAUSES PEOPLE TO WRITE WORSE CODE! Which was against the whole point of having the warning in the first place."  
  `Pine.LNX.4.64.0702131513050.3604@woody.linux-foundation.org`, 2007-02-13, <https://lore.kernel.org/all/Pine.LNX.4.64.0702131513050.3604%40woody.linux-foundation.org/>
- "The warning literally causes bugs. It's not a safety net - it's the literal reverse of a safety net that encourages bad code, or leaving out good checks."  
  `CAHk-=wgg2A_iHNwf_JDjYJF=XHnKVGOjGp50FzVWniA2Z010bw@mail.gmail.com`, 2025-02-21, <https://lore.kernel.org/all/CAHk-%3Dwgg2A_iHNwf_JDjYJF%3DXHnKVGOjGp50FzVWniA2Z010bw%40mail.gmail.com/>
- "So don't confuse a broken warning that might trigger for your code with a good warning that would also trigger for your code."  
  `CAHk-=wjQ94GipftbNo0PbfuUxFMXFyp2bWGJJPNUngyf17Ai8A@mail.gmail.com`, 2025-02-21, <https://lore.kernel.org/all/CAHk-%3DwjQ94GipftbNo0PbfuUxFMXFyp2bWGJJPNUngyf17Ai8A%40mail.gmail.com/>
- "Don't send patches to remove warnings. Send patches to FIX PROBLEMS."  
  `alpine.LFD.1.10.0805291123320.2958@woody.linux-foundation.org`, 2008-05-29, <https://lore.kernel.org/all/alpine.LFD.1.10.0805291123320.2958%40woody.linux-foundation.org/>
- "this one is a keeper"  
  `CA+55aFx=xh4+vCNOgwXyfeV-t=6anXimqBxH_i71RjYy+Gy9-w@mail.gmail.com`, 2015-09-03, <https://lore.kernel.org/all/CA%2B55aFx%3Dxh4%2BvCNOgwXyfeV-t%3D6anXimqBxH_i71RjYy%2BGy9-w%40mail.gmail.com/>
- "I simply refuse to be in the situation where I might miss an _important_ warning"  
  `CAHk-=wjah-fkfzMdmCNN8v7uriJsGeYjHh18wkXDZa2sxuAXzA@mail.gmail.com`, 2020-05-10, <https://lore.kernel.org/all/CAHk-%3Dwjah-fkfzMdmCNN8v7uriJsGeYjHh18wkXDZa2sxuAXzA%40mail.gmail.com/>

**Support.** ~20 messages, 2006–2025.

---

## 10. Clean builds and -Werror: from "not an error" (2008) to on by default (2021)

**Principle (current).** The build should be warning-free; warnings that cannot be fixed are disabled explicitly
rather than tolerated. Making them fatal is the only way they go away.

**What triggers it.** New warnings introduced by a patch; "we'll fix the warnings later"; turning -Werror off for a
subsystem.

**His reasoning.** 2008: warnings are not errors. 2020: -Werror works in controlled environments, not in the random
mess of compilers and configs. 2021: enabled `CONFIG_WERROR` by default — "We really should always have a clean
build" — because non-fatal warnings "stay around forever". 2022: NAK of disabling -Werror for W=1.

**How serious.** Since 2021, new warnings in his tree are build breaks he fixes or reverts.

**Limits.** -Werror applies to the default warning set, not to extra warnings (W=1/W=2); the escape is a config
option and disabling over-eager warnings.

**Outside the kernel.** CI with warnings-as-errors for the curated set; noisy lints off rather than ignored.

**Evidence.**
- "If anybody thinks that a compiler warning is the same thing as a compiler error, that person shouldn't be compiling."  
  `alpine.LFD.1.10.0805291129520.2958@woody.linux-foundation.org`, 2008-05-29, <https://lore.kernel.org/all/alpine.LFD.1.10.0805291129520.2958%40woody.linux-foundation.org/>
- "End result: using -Werror works wonderfully in controlled environments. Not so wonderfully in the general random mess."  
  `CAHk-=whsW9Dh7zCwbct59GOL0CudU+k4C3pa1P1xUxzzSbJoUA@mail.gmail.com`, 2020-08-19, <https://lore.kernel.org/all/CAHk-%3DwhsW9Dh7zCwbct59GOL0CudU%2Bk4C3pa1P1xUxzzSbJoUA%40mail.gmail.com/>
- "We really should always have a clean build, and will disable specific over-eager warnings as required, if we can't fix them."  
  `3fe617ccafd6f5bb33c2391d6f4eeb41c1fd0151`, 2021-09-05, <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=3fe617ccafd6f5bb33c2391d6f4eeb41c1fd0151>
- "Because the warnings don't go away on their own, and not making them fatal clearly just means that they'll stay around forever."  
  `CAHk-=wj7M1_BXG2MXLv4OhjzjV-opy=5fE7+vafW5fHOyDrg+w@mail.gmail.com`, 2021-09-13, <https://lore.kernel.org/all/CAHk-%3Dwj7M1_BXG2MXLv4OhjzjV-opy%3D5fE7%2BvafW5fHOyDrg%2Bw%40mail.gmail.com/>

**Support.** ~7 messages/commits, 2002–2022.

---

## 11. Signedness is not obvious from the declaration; make it explicit and check both ends

**Principle.** Assume the signedness of `char`, enums, bitfields and typedefs is not what a reader thinks. Use
explicitly unsigned types for bit patterns and bytes, unsigned bitfields, and range checks that test both ends. For
comparisons across types, make the comparison type explicit.

**What triggers it.** `char` used for bytes; `int x:1` bitfields; `min(a, b)` across signed and unsigned; `if (x <
0)` on a typedef whose signedness is configuration-dependent; on-disk formats using host types.

**His reasoning.** Bitfields, enums and `char` have implementation-defined signedness (2007); signed bitfields are
almost always a bug (2007); architecture differences are bad, and making the language stricter (e.g. kernel-wide
`-funsigned-char`, 2022) is good. In 2001 he made `min()` take a type so the user states the comparison type; in
2024 the macro was redesigned for safety and compile cost (§13).

**How serious.** Kernel-wide build flag change (2022); review comments; NAK of removing range-check ends.

**Limits.** He prefers sane defaults over annotations everywhere; he relaxed min()'s type argument once the macro
could check signedness itself.

**Outside the kernel.** Rust removes most of this (no implicit conversions), but `as` casts truncate and change sign
silently — flag them. TypeScript/JS: bitwise operators convert to signed 32-bit; `>>>` vs `>>`. Python: `ctypes`,
`struct` formats, numpy dtypes. (Generalisation mine.)

**Evidence.**
- "Bitfields simply have implementation-defined signedness. As do enums. As does "char"."  
  `Pine.LNX.4.64.0702081632200.8424@woody.linux-foundation.org`, 2007-02-09, <https://lore.kernel.org/all/Pine.LNX.4.64.0702081632200.8424%40woody.linux-foundation.org/>
- "I will actually argue that having signed bit-fields is almost always a bug"  
  `Pine.LNX.4.64.0702081528070.8424@woody.linux-foundation.org`, 2007-02-08, <https://lore.kernel.org/all/Pine.LNX.4.64.0702081528070.8424%40woody.linux-foundation.org/>
- "So having both sides of a range check is *always* a good idea"  
  `CAHk-=wjMVfu-aiQ8aNHcgsh6hYwbZCoX1B4ps2scibokO8EZ+A@mail.gmail.com`, 2025-12-18, <https://lore.kernel.org/all/CAHk-%3DwjMVfu-aiQ8aNHcgsh6hYwbZCoX1B4ps2scibokO8EZ%2BA%40mail.gmail.com/>
- "And I do think that having odd architecture differences is generally a bad idea, and making the language rules stricter to avoid differences is a good thing."  
  `CAHk-=whT+xyge9UjH+r6dt0FG-eUdrzu5hDMce_vC+n8uLam2A@mail.gmail.com`, 2022-10-19, <https://lore.kernel.org/all/CAHk-%3DwhT%2Bxyge9UjH%2Br6dt0FG-eUdrzu5hDMce_vC%2Bn8uLam2A%40mail.gmail.com/>
- "force the user to specify what type he _thinks_ the comparison should be done in."  
  `9mf8ft$7pt$1@penguin.transmeta.com`, 2001-08-28, <https://lore.kernel.org/all/9mf8ft%247pt%241%40penguin.transmeta.com/>

**Support.** ~12 messages, 2001–2025.

---

## 12. Typedefs only when the type genuinely varies or must be opaque; never hide a pointer

**Principle.** A type alias needs a reason: it varies by configuration/architecture, or it must be opaque and
accessed only through helpers. Saving typing is not a reason. Never hide that something is a pointer.

**What triggers it.** `typedef struct foo foo_t;`; `typedef struct foo *foo_p;`; new names for `int` with no
semantic content.

**His reasoning.** The only valid reason is configuration dependence (2006); "hiding the fact that it's a pointer is
a shooting offense" (2006). Type abstraction without reason is dislikeable (2002); exceptions like `pte_t` exist
because the type must be accessed through helpers. Typedefs can't be forward-declared, unlike `struct foo` (2006).
He prefers `u32` to `uint32_t` (2004) but "would I make it a huge issue? Not personally" (2007).

**How serious.** Low to moderate; style comments, occasional rejection.

**Limits.** `u8..u64`, `__le32` endian types, sparse `__bitwise` types and config-dependent types are accepted.

**Outside the kernel.** (Mine) Type aliases in TypeScript/Rust that add no meaning are noise; aliases that add
meaning (newtypes, branded types) are the good case — but the newtype must carry a check, not just a name. Hiding
`Rc<RefCell<..>>`/pointer-ness behind an alias is the analogue of the "shooting offense".

**Evidence.**
- "The _only_ valid reason to use typedefs ever is because it's a type that depends on some configuration option"  
  `Pine.LNX.4.64.0611282027431.3395@woody.osdl.org`, 2006-11-29, <https://lore.kernel.org/all/Pine.LNX.4.64.0611282027431.3395%40woody.osdl.org/>
- "hiding the fact that it's a pointer is a shooting offense"  
  `Pine.LNX.4.64.0611282027431.3395@woody.osdl.org`, 2006-11-29, <https://lore.kernel.org/all/Pine.LNX.4.64.0611282027431.3395%40woody.osdl.org/>
- "I dislike type abstraction if it has no real reason. And saving on typing is not a good reason"  
  `Pine.LNX.4.44.0206100954250.30535-100000@home.transmeta.com`, 2002-06-10, <https://lore.kernel.org/all/Pine.LNX.4.44.0206100954250.30535-100000%40home.transmeta.com/>
- "We don't hide types in the kernel for no good reason."  
  `CAHk-=wj+P=YeuY=tpY72nDMQgxGTzEMqjfq5P536G=qYEkQr1w@mail.gmail.com`, 2021-10-05, <https://lore.kernel.org/all/CAHk-%3Dwj%2BP%3DYeuY%3DtpY72nDMQgxGTzEMqjfq5P536G%3DqYEkQr1w%40mail.gmail.com/>
- "But would I make it a huge issue? Not personally."  
  `alpine.LFD.0.98.0706160840290.14121@woody.linux-foundation.org`, 2007-06-16, <https://lore.kernel.org/all/alpine.LFD.0.98.0706160840290.14121%40woody.linux-foundation.org/>

**Support.** ~9 messages, 2002–2021.

---

## 13. `volatile` (and similar markers) belong on accesses, not on data

**Principle.** Volatility is a property of a particular access in a particular context, not of an object. Marking
data structures `volatile` usually means the locking or ordering is wrong. Use explicit access helpers
(`READ_ONCE`/`WRITE_ONCE`) and real synchronisation.

**What triggers it.** `volatile` in struct declarations or globals; busy-wait loops on `volatile` flags; "fixing" a
race by adding `volatile`.

**His reasoning.** In 99.9% of cases `volatile` means the data is not locked correctly (2000); "volatile on data
structures" is always wrong, "volatile in code" may be right (2007); the context makes an access volatile (2024);
often it only shows the programmer was confused or lazy (2006).

**How serious.** Patches adding `volatile` get rejected and redirected to locking or access helpers.

**Limits.** MMIO accessors and `READ_ONCE` use volatile internally; volatile access casts in code are fine.

**Outside the kernel.** (Mine) Rust: prefer `Atomic*` with explicit ordering, `read_volatile` only for MMIO. Java/C#
`volatile` fields as a substitute for proper synchronisation are the same smell. In TypeScript/Python the analogue is
"sleep and re-check" polling in place of a proper wait.

**Evidence.**
- "in 99.9% of all cases, the existence of "volatile" is just a sign that somebody doesn't lock the data structure correctly"  
  `https://yarchive.net/comp/volatile.html#2`, 2000-02-09, <https://yarchive.net/comp/volatile.html#2>
- "So the difference between "volatile in code" and "volatile on data structures" is that the latter is *always* wrong"  
  `alpine.LFD.0.999.0708090751560.25146@woody.linux-foundation.org`, 2007-08-09, <https://lore.kernel.org/all/alpine.LFD.0.999.0708090751560.25146%40woody.linux-foundation.org/>
- "So it's not the *variable* (aka "object") that is 'volatile', it's the *context* that makes a particular access volatile."  
  `CAHk-=wjP1i014DGPKTsAC6TpByC3xeNHDjVA4E4gsnzUgJBYBQ@mail.gmail.com`, 2024-03-25, <https://lore.kernel.org/all/CAHk-%3DwjP1i014DGPKTsAC6TpByC3xeNHDjVA4E4gsnzUgJBYBQ%40mail.gmail.com/>
- "In many cases, the _only_ thing that "volatile" implies is that the original programmer was confused and/or lazy."  
  `Pine.LNX.4.64.0607140941170.5623@g5.osdl.org`, 2006-07-14, <https://lore.kernel.org/all/Pine.LNX.4.64.0607140941170.5623%40g5.osdl.org/>

**Support.** ~8 messages, 1993–2024.

---

## 14. Casts break the type system: never cast to silence; strong types need a deliberate escape

**Principle.** A cast says "I know better than the type system" and so must be rare and deliberate. If a cast is
needed, usually a type is wrong somewhere. Strong-typing extensions (sparse `__bitwise`, `__user`) are good, but they
must have an explicit, greppable escape (`__force`) for the few legitimate uses.

**What triggers it.** Casts on function pointers or buffers to make a call compile; `(void *)` round trips; casts
added in warning-fix patches; strict enum/newtype schemes with no escape hatch.

**His reasoning.** Casts in C are dangerous (2007); a cast hides the fact that "buf" has the wrong type (2003);
random casts to shut up the compiler make code worse (2025). `__force` is not forbidden, but must never be used by
mistake (2004). Integer types that "stay in the type" are good, but need a sane escape (2025).

**How serious.** Review comments; rejection of cast-adding patches.

**Limits.** Explicit, documented escapes are fine. He accepts that strict typing in C must be opt-in per type.

**Outside the kernel.** Very transferable: TypeScript `as`, `as unknown as T`, `any`, `!`; Python `cast()` and
`# type: ignore`; Rust `as`, `transmute`. (Mine) Ask "which type is wrong?" before accepting any of them.

**Evidence.**
- "casts in C are *dangerous*."  
  `Pine.LNX.4.64.0702131513050.3604@woody.linux-foundation.org`, 2007-02-13, <https://lore.kernel.org/all/Pine.LNX.4.64.0702131513050.3604%40woody.linux-foundation.org/>
- "The point behind __force is not so much that you should never use it, but that you should never use it by _mistake_."  
  `Pine.LNX.4.58.0409131142370.2378@ppc970.osdl.org`, 2004-09-13, <https://lore.kernel.org/all/Pine.LNX.4.58.0409131142370.2378%40ppc970.osdl.org/>
- "The problem here is that "buf" has the wrong type, and you're hiding it with a cast."  
  `Pine.LNX.4.44.0306071259050.2393-100000@home.transmeta.com`, 2003-06-07, <https://lore.kernel.org/all/Pine.LNX.4.44.0306071259050.2393-100000%40home.transmeta.com/>
- "it makes the code actively worse with adding random casts just to shut the compiler up."  
  `CAHk-=whe1UZUGKbtaaRV7CfS=sGtB2ouYAriryZ6bscE+5AFhA@mail.gmail.com`, 2025-02-08, <https://lore.kernel.org/all/CAHk-%3Dwhe1UZUGKbtaaRV7CfS%3DsGtB2ouYAriryZ6bscE%2B5AFhA%40mail.gmail.com/>
- "So the *concept* of an enum - or any other integer type - that "stays in the type" is good, but I think it's a major mistake to think they have to do so without any sane escape"  
  `CAHk-=wjMux0w49bTdSbC3DOoc9FRctDrRvaqFUS4KFTmkbtKWg@mail.gmail.com`, 2025-02-08, <https://lore.kernel.org/all/CAHk-%3DwjMux0w49bTdSbC3DOoc9FRctDrRvaqFUS4KFTmkbtKWg%40mail.gmail.com/>

**Support.** ~10 messages, 2003–2025.

---

## 15. Macros must behave like the function they look like; prefer inline functions

**Principle.** If a macro looks like a function call, it must act like one: evaluate each argument exactly once, not
assign to its arguments, not return from the caller, not take code as an argument. Use inline functions when
possible; use `__always_inline` only when correctness depends on inlining, with a comment. Watch the compile-time cost
of macro expansion.

**What triggers it.**
```c
#define alloc_obj(p) (p = kmalloc(sizeof(*p), GFP_KERNEL))  /* hidden assignment: NAKed 2025-03 */
#define MAX(a,b) ((a) > (b) ? (a) : (b))                   /* double evaluation */
#define for_each_thing(x, CODE) ...                          /* code in arguments */
```
Also: very deep nested macros (`min()`/`max()` expansions of megabytes in 2024), and type-converting "convenient"
extensions (plan9 struct embedding).

**His reasoning.** "When it looks like a function, it should act like a function" (2025). A hidden assignment is too
easy to miss; maintaining code is at least as important as writing it (2025). He despises code inside macro
arguments even more than hidden updates (2025). "No, the preprocessor is not the answer" (2019). Inline functions are
nicer but have a cost (2005) — sometimes a macro is better (e.g. needs the caller's type or `sizeof`).

**How serious.** NAK (kmalloc_obj v1, 2025-03; double evaluation, 2025-07). He personally rewrote minmax.h (2024).

**Limits and the arc.** kmalloc_obj was accepted when it *returned* a properly typed pointer (2025-11) and converted
tree-wide in 2026-02 ("The code really does look better"). Type-generic macros (`min`, `container_of`) are accepted
when they act like functions. C23 `auto` replaced `__auto_type` (2025).

**Outside the kernel.** (Mine) The rule generalises to any metaprogramming: Rust `macro_rules!`/proc macros that hide
`return` or `?`, Python decorators and metaclasses that change call semantics, TypeScript decorators. Test: can a
reader understand the call site without opening the macro?

**Evidence.**
- "When it looks like a function, it should act like a function, and not evaluate its arguments multiple times."  
  `CAHk-=wgiX0q0WCL+SFwVCYtG7JR3=2Rshse-5J3AO2Y4AgT7Jw@mail.gmail.com`, 2025-03-14, <https://lore.kernel.org/all/CAHk-%3DwgiX0q0WCL%2BSFwVCYtG7JR3%3D2Rshse-5J3AO2Y4AgT7Jw%40mail.gmail.com/>
- "It's much much too easy to miss that there's an assignment there, because the assignment is hidden inside that macro that visually looks like a function call."  
  `CAHk-=wiFjwOk9knz8i-zAqE=Kc73+3TgkMuj-C_mNB1U=k2W7A@mail.gmail.com`, 2025-03-15, <https://lore.kernel.org/all/CAHk-%3DwiFjwOk9knz8i-zAqE%3DKc73%2B3TgkMuj-C_mNB1U%3Dk2W7A%40mail.gmail.com/>
- "Maintaining code is AT LEAST as important as writing it, and arguably much more so."  
  `CAHk-=wiFjwOk9knz8i-zAqE=Kc73+3TgkMuj-C_mNB1U=k2W7A@mail.gmail.com`, 2025-03-15, <https://lore.kernel.org/all/CAHk-%3DwiFjwOk9knz8i-zAqE%3DKc73%2B3TgkMuj-C_mNB1U%3Dk2W7A%40mail.gmail.com/>
- "I despise code inside macro arguments even more than I dislike the hidden update."  
  `CAHk-=wibAE=yDhWdY7jQ7xvCtbmW5Tjtt_zMJcEzey3xfL=ViA@mail.gmail.com`, 2025-08-18, <https://lore.kernel.org/all/CAHk-%3DwibAE%3DyDhWdY7jQ7xvCtbmW5Tjtt_zMJcEzey3xfL%3DViA%40mail.gmail.com/>
- "No, the preprocessor is not the answer."  
  `CAHk-=wgFODvdFBHzgVf3JjoBz0z6LZhOm8xvMntsvOr66ASmZQ@mail.gmail.com`, 2019-10-02, <https://lore.kernel.org/all/CAHk-%3DwgFODvdFBHzgVf3JjoBz0z6LZhOm8xvMntsvOr66ASmZQ%40mail.gmail.com/>
- "Clearly inline functions are "nicer", but they do come with a cost."  
  `Pine.LNX.4.58.0501200926510.8178@ppc970.osdl.org`, 2005-01-20, <https://lore.kernel.org/all/Pine.LNX.4.58.0501200926510.8178%40ppc970.osdl.org/>

**Support.** ~14 messages and 2 commits, 2005–2026.

---

## 16. Scope-based cleanup (RAII) is acceptable when explicit and paired with the acquire

**Principle.** Automatic cleanup is welcome if the cleanup is declared at the same place, in the same visible syntax,
as the acquisition; anything non-trivial stays explicit. Do not convert existing code mindlessly, and avoid
conditional guard variants that make it unclear whether the resource is held.

**What triggers it.** `guard()`/`scoped_guard()` conversions that leave an old manual unlock in place;
`cond_guard`/`if_not_guard` patterns; cleanup attributes on variables initialised far from their declaration;
large mechanical conversion series.

**His reasoning.** Non-trivial things must be "done very explicitly, and very much visibly by hand" (2023). The
cleanup syntax must match the acquire and be in one place (2025). He rejects the idea that mindless conversions of
conditional locking are good (2024). The primary goal is code legible to humans (2025).

**How serious.** He relaxed `-Wdeclaration-after-statement` (2023) to allow it — a real language-rule change — but
pushes back on specific APIs and conversions.

**Limits.** This is a 2023+ position; earlier (2007) he objected to implicit destructors in C++. What changed:
cleanup is now opt-in per variable and visible at the declaration.

**Outside the kernel.** Python `with`, Rust guards/`Drop`, TypeScript `using` (explicit resource management):
fine when acquire and release are declared together. (Mine) Flag `Drop` impls that do I/O or can block, and
conversions that change lock scope silently.

**Evidence.**
- "anything non-trivial had better be done very explicitly, and very much visibly by hand."  
  `CAHk-=wgQ5m+SnWTYGHu0JgYXTk2dkGF+msX=ARfYoo3t1_fX9g@mail.gmail.com`, 2023-06-06, <https://lore.kernel.org/all/CAHk-%3DwgQ5m%2BSnWTYGHu0JgYXTk2dkGF%2BmsX%3DARfYoo3t1_fX9g%40mail.gmail.com/>
- "or that "mindless conversions" of conditional locking is actually a good thing."  
  `CAHk-=whn07tnDosPfn+UcAtWHBcLg=KqA16SHVv0GV4t8P1fHw@mail.gmail.com`, 2024-11-20, <https://lore.kernel.org/all/CAHk-%3Dwhn07tnDosPfn%2BUcAtWHBcLg%3DKqA16SHVv0GV4t8P1fHw%40mail.gmail.com/>
- "But the *primary* thing should be about making the code itself legible and maintainable to humans."  
  `CAHk-=wjD1r5dr_b7gpuPdTXGdXAtaM6wHBSJyzi-Zfw3-cqR6w@mail.gmail.com`, 2025-11-18, <https://lore.kernel.org/all/CAHk-%3DwjD1r5dr_b7gpuPdTXGdXAtaM6wHBSJyzi-Zfw3-cqR6w%40mail.gmail.com/>

**Support.** ~6 messages, 2023–2025.

---

## 17. Arrays as parameters are a lie; `sizeof` and pointer arithmetic need care

**Principle.** In C an array parameter is a pointer; don't write signatures that pretend otherwise unless the
compiler checks it (`[static N]`). `sizeof` on such a parameter gives the pointer size. Pointer arithmetic scales by
the element type. No variable-length arrays.

**What triggers it.** `void f(char buf[16]) { memset(buf, 0, sizeof(buf)); }`; `ptr + len` where `len` is in bytes
but `ptr` is a struct pointer; VLAs on the stack.

**His reasoning.** "array arguments in C don't actually exist"; misleading documentation is a mistake (2015). VLAs
are not good in the kernel (2012). In 2025 he accepted `[static N]` because the feature is
right even if the syntax is "disgusting and nonsensical".

**How serious.** He enabled the compiler warning that catches `sizeof` on array parameters; bugs found are fixed.

**Limits.** `[static N]` is fine because the compiler enforces it.

**Outside the kernel.** Limited. (Mine) The general lesson is that signatures must not claim guarantees the
language does not check — e.g. TypeScript tuple types on data from `JSON.parse`, Python type hints treated as
validation.

**Evidence.**
- "array arguments in C don't actually exist"  
  `CA+55aFx=xh4+vCNOgwXyfeV-t=6anXimqBxH_i71RjYy+Gy9-w@mail.gmail.com`, 2015-09-03, <https://lore.kernel.org/all/CA%2B55aFx%3Dxh4%2BvCNOgwXyfeV-t%3D6anXimqBxH_i71RjYy%2BGy9-w%40mail.gmail.com/>
- "Misleading documentation isn't documentation, it's a mistake."  
  `CA+55aFx=xh4+vCNOgwXyfeV-t=6anXimqBxH_i71RjYy+Gy9-w@mail.gmail.com`, 2015-09-03, <https://lore.kernel.org/all/CA%2B55aFx%3Dxh4%2BvCNOgwXyfeV-t%3D6anXimqBxH_i71RjYy%2BGy9-w%40mail.gmail.com/>
- "VLA's really aren't a very good thing in the kernel."  
  `CA+55aFzCuDCo1tJvgetOVhwnO_W+FaYBDZiuZTGYD+YA4iwp0Q@mail.gmail.com`, 2012-03-14, <https://lore.kernel.org/all/CA%2B55aFzCuDCo1tJvgetOVhwnO_W%2BFaYBDZiuZTGYD%2BYA4iwp0Q%40mail.gmail.com/>
- "So the syntax is disgusting and nonsensical, but the feature certainly isn't wrong."  
  `CAHk-=wj6J5L5Y+oHc-i9BrDONpSbtt=iEemcyUm3dYnZ3pXxxg@mail.gmail.com`, 2025-11-15, <https://lore.kernel.org/all/CAHk-%3Dwj6J5L5Y%2BoHc-i9BrDONpSbtt%3DiEemcyUm3dYnZ3pXxxg%40mail.gmail.com/>

**Support.** ~5 messages, 2012–2025.

---

## 18. `const` means "you can't write through this", not "immutable"; take const wherever possible

**Principle.** Use `const` on pointer parameters wherever the function doesn't write; it documents and catches
misuse. Do not mistake it for immutability or use it to argue about optimisation.

**What triggers it.** Functions taking `char *` for read-only input; arguments that const allows the compiler to
assume the value never changes.

**His reasoning.** const is a pointer type issue meant to make misuse visible at compile time; anything that can
take a const pointer should (2008); it literally means "you can't write through this field" (2024).

**How serious.** Low; review comments.

**Outside the kernel.** TypeScript `readonly`/`Readonly<T>`, Rust `&` vs `&mut`, Python `Sequence` vs `list` in
hints: (mine) prefer the read-only type in signatures, and remember `readonly` in TS is a view, not a freeze.

**Evidence.**
- ""const" is a pointer type issue, and is meant to make certain mis-uses more visible at compile time."  
  `alpine.LFD.1.00.0801161026550.2806@woody.linux-foundation.org`, 2008-01-16, <https://lore.kernel.org/all/alpine.LFD.1.00.0801161026550.2806%40woody.linux-foundation.org/>
- "Anything that *can* take a const pointer should always do so."  
  `alpine.LFD.1.00.0801161026550.2806@woody.linux-foundation.org`, 2008-01-16, <https://lore.kernel.org/all/alpine.LFD.1.00.0801161026550.2806%40woody.linux-foundation.org/>
- "It literally means "you can't write through this field"."  
  `CAHk-=whZefPXJaPSZR=3JzX9Bx2zRoCK9ASd=US5CFfU0HCTfw@mail.gmail.com`, 2024-02-10, <https://lore.kernel.org/all/CAHk-%3DwhZefPXJaPSZR%3D3JzX9Bx2zRoCK9ASd%3DUS5CFfU0HCTfw%40mail.gmail.com/>

**Support.** ~3 messages, 2008–2024 (thin).

---

## 19. Write code the compiler can see through, and check the generated code where it matters

**Principle.** For code you care about, look at what the compiler actually generates. Write source so the efficient
code is obvious, rather than relying on clever optimisations. Don't trust that automated tools do the right thing.
In ordinary user programs, use compiler intrinsics rather than hand-written assembly.

**What triggers it.** Performance claims with no profile or disassembly; micro-optimisations relying on the
compiler to do non-obvious conversions; new compiler features (named address spaces, builtins) adopted without
checking output; hand-written assembly in application code.

**His reasoning.** He looks at generated code and profiles (2016); verifying generated code is great for code you
care about, but don't depend on non-obvious conversions (2017); he admires code written so the compiler can make it
efficient, not "despite" the source (2012). Automation does not make compilers right (2024). For user programs,
intrinsics make more sense (2024).

**How serious.** He rejects patches whose code generation is bad (e.g. gcc's `__seg_fs` struct copy, 2023).

**Limits.** He explicitly distinguishes kernel needs (inline asm, exact control) from user programs (intrinsics).

**Outside the kernel.** (Mine) For Python/TypeScript the analogue is reading the profile, the SQL query plan, or the
bundle output — check what actually runs for hot paths. For Rust: `cargo asm`/Compiler Explorer for hot loops.

**Evidence.**
- "So I generally do not want people to depend on the compiler to do non-obvious conversions"  
  `CA+55aFyo0Md9G5xF40jLL8DwjBHCaxPn628xUEVG=yr3d6YBUg@mail.gmail.com`, 2017-11-17, <https://lore.kernel.org/all/CA%2B55aFyo0Md9G5xF40jLL8DwjBHCaxPn628xUEVG%3Dyr3d6YBUg%40mail.gmail.com/>
- "If you are comfy with assembler, it can actually be a great thing to occasionally just verify the actual generated code if it's some piece of code you care deeply about."  
  `CA+55aFyo0Md9G5xF40jLL8DwjBHCaxPn628xUEVG=yr3d6YBUg@mail.gmail.com`, 2017-11-17, <https://lore.kernel.org/all/CA%2B55aFyo0Md9G5xF40jLL8DwjBHCaxPn628xUEVG%3Dyr3d6YBUg%40mail.gmail.com/>
- "rather than hoping that the compiler is so smart that it can make efficient code *despite* the state of the original source code"  
  `https://meta.slashdot.org/story/12/10/11/0030249/linus-torvalds-answers-your-questions`, 2012-10-11, <https://meta.slashdot.org/story/12/10/11/0030249/linus-torvalds-answers-your-questions>
- "I care about performance a lot, and I actually look at generated code and do profiling etc."  
  `CA+55aFyauwKmUdxfrKcy5Q2kvdej5fWt6xL+amVyPFhzmHMcsg@mail.gmail.com`, 2016-02-28, <https://lore.kernel.org/all/CA%2B55aFyauwKmUdxfrKcy5Q2kvdej5fWt6xL%2BamVyPFhzmHMcsg%40mail.gmail.com/>
- "People who think that compilers do things right just because they are automated simply don't know what they are talking about."  
  `CAHk-=whY5A=S=bLwCFL=043DoR0TTgSDUmfPDx2rXhkk3KANPQ@mail.gmail.com`, 2024-03-23, <https://lore.kernel.org/all/CAHk-%3DwhY5A%3DS%3DbLwCFL%3D043DoR0TTgSDUmfPDx2rXhkk3KANPQ%40mail.gmail.com/>
- "But in some random user level program, where all you want is an efficient way to do "find first bit"? Then using a compiler intrinsic makes a lot more sense."  
  `CAHk-=whkQk=zq5XiMcaU3xj4v69+jyoP-y6Sywhq-TvxSSvfEA@mail.gmail.com`, 2024-03-23, <https://lore.kernel.org/all/CAHk-%3DwhkQk%3Dzq5XiMcaU3xj4v69%2BjyoP-y6Sywhq-TvxSSvfEA%40mail.gmail.com/>

**Support.** ~10 messages, 2005–2024.

---

## 20. The standard is not the authority; working code and real machines are; pin the language level

**Principle.** "The standard says" does not settle an engineering question. Real compilers, real hardware and code
that works decide. Where the standard permits nonsense, the standard is wrong. Use one explicit language version for
the whole project.

**What triggers it.** Review arguments that rest solely on the standard; "abstract machine" reasoning; mixed
`-std=` levels across a codebase; rejecting non-standard but widely implemented extensions on principle.

**His reasoning.** The abstract machine concept is broken (2024). Either compiler and standard get it right or "we
don't use it" (2014, on C11 atomics). UB is almost always a sign the standard is wrong (2016). gcc people chasing what
C99 allows rather than making things work (2003). The kernel depends on non-standard features and "sane
implementation" over "language-lawyering" (2025). No upside to mixed standard versions (2022, the move to gnu11).

**How serious.** Policy; and in arguments with compiler developers he dismisses standards-only reasoning.

**Limits.** He adopts new standard features when useful (`gnu11` in 2022, C23 `auto`, `[static N]`). Sane compiler
people who say "yup, bug" are fine (2014).

**Outside the kernel.** (Mine) Specs, RFCs and type checkers are tools; when they disagree with what deployed
clients do, decide by what works and document it. Pin language/runtime versions (`rust-version`, `engines`,
`requires-python`) project-wide.

**Evidence.**
- "The whole concept of "abstract machine" is broken."  
  `CAHk-=wh+Cs7g6U7_7f5OngNqiTK5768ceQyRE07U6VRuxHDNfA@mail.gmail.com`, 2024-03-17, <https://lore.kernel.org/all/CAHk-%3Dwh%2BCs7g6U7_7f5OngNqiTK5768ceQyRE07U6VRuxHDNfA%40mail.gmail.com/>
- "So I'm very very serious: either the compiler and the standard gets things right, or we don't use it."  
  `CA+55aFypfiTFwundih8QEA6ZwVGk=g5L4sabsN0932eih5knOQ@mail.gmail.com`, 2014-02-14, <https://lore.kernel.org/all/CA%2B55aFypfiTFwundih8QEA6ZwVGk%3Dg5L4sabsN0932eih5knOQ%40mail.gmail.com/>
- "And undefined behavior is pretty much *always* a sign of "the standard is wrong"."  
  `CA+55aFyHmykKc=YybJMo9ZUO352MY5noJVB4-K1Lkjmw4UHXfA@mail.gmail.com`, 2016-02-27, <https://lore.kernel.org/all/CA%2B55aFyHmykKc%3DYybJMo9ZUO352MY5noJVB4-K1Lkjmw4UHXfA%40mail.gmail.com/>
- "The gcc people are more interested in trying to find out what can be allowed by the c99 specs than about making things actually _work_."  
  `b3itcd$2bi$1@penguin.transmeta.com`, 2003-02-26, <https://lore.kernel.org/all/b3itcd%242bi%241%40penguin.transmeta.com/>
- "We very obviously use entirely non-standard features, and regularly depend on "sane implementation" as opposed to any documentation language-lawyering."  
  `CAHk-=wj6J5L5Y+oHc-i9BrDONpSbtt=iEemcyUm3dYnZ3pXxxg@mail.gmail.com`, 2025-11-15, <https://lore.kernel.org/all/CAHk-%3Dwj6J5L5Y%2BoHc-i9BrDONpSbtt%3DiEemcyUm3dYnZ3pXxxg%40mail.gmail.com/>
- "I see absolutely no upside to allowing different users using higher/lower versions of the standard. There are only downsides."  
  `CAHk-=whWbENRz-vLY6vpESDLj6kGUTKO3khGtVfipHqwewh2HQ@mail.gmail.com`, 2022-02-27, <https://lore.kernel.org/all/CAHk-%3DwhWbENRz-vLY6vpESDLj6kGUTKO3khGtVfipHqwewh2HQ%40mail.gmail.com/>

**Support.** ~12 messages, 2003–2025.

---

## 21. Build scripts and tools: explicit dependencies, real error handling, tools serve maintainers

**Principle.** Scripts are good for prototypes and glue but bad at error handling; build dependencies (Python,
Sphinx, pip packages) must be checked explicitly with clear errors. Automated formatters and tooling must not make
decisions that hurt maintainability (merge conflicts).

**What triggers it.** Shell pipelines without error checks; build steps that fail obscurely when a Python package
is missing; rustfmt/prettier configurations that churn import lists.

**His reasoning.** Error handling in scripting is hard, especially in pipelines (2006, git history). Package
dependencies should be tested for explicitly (2022). rustfmt's `use` handling is "automated tooling that is
literally making bad decisions for the maintainability" (2025); `use` lines should be like `#include` lines, one per
line, so merges are easy.

**How serious.** Grumbles and requests to change the tool's configuration; not merge-blocking.

**Limits.** Thin on Python and Go as languages (see below).

**Outside the kernel.** (Mine) `set -euo pipefail`; dependency checks with actionable errors; formatter settings that
minimise diff churn (one import per line).

**Evidence.**
- "But error handling in scripting is very hard or inconvenient, especially in pipelines."  
  `Pine.LNX.4.64.0610251912220.3962@g5.osdl.org`, 2006-10-26, <https://lore.kernel.org/all/Pine.LNX.4.64.0610251912220.3962%40g5.osdl.org/>
- "It would be lovely to have that package dependency - whatever it may be - tested for explicitly."  
  `CAHk-=wj+FNSnspKwVWAatD+DHz3Uy4eHxQryrfoZz6=4D=1X1w@mail.gmail.com`, 2022-12-16, <https://lore.kernel.org/all/CAHk-%3Dwj%2BFNSnspKwVWAatD%2BDHz3Uy4eHxQryrfoZz6%3D4D%3D1X1w%40mail.gmail.com/>
- "It's automated tooling that is literally making bad decisions for the maintainability."  
  `CAHk-=wgO7S_FZUSBbngG5vtejWOpzDfTTBkVvP3_yjJmFddbzA@mail.gmail.com`, 2025-10-02, <https://lore.kernel.org/all/CAHk-%3DwgO7S_FZUSBbngG5vtejWOpzDfTTBkVvP3_yjJmFddbzA%40mail.gmail.com/>
- "And quite frankly, I think your "use a big array" in go is a mistake."  
  `AANLkTim7YVg1BTEjyhYShgZNL3oKu+zFywC7+NgFvT3z@mail.gmail.com`, 2011-02-08, <https://lore.kernel.org/all/AANLkTim7YVg1BTEjyhYShgZNL3oKu%2BzFywC7%2BNgFvT3z%40mail.gmail.com/>

**Support.** ~6 messages, 2006–2025 (thin).

---

## Changes of position over time

| Topic | Earlier | Later / current | Evidence |
|---|---|---|---|
| `-Werror` | 2002 "not really wrong"; 2008 a warning is not an error | 2021 `CONFIG_WERROR` on by default; 2022 NAK of turning it off | §10 |
| Implicit cleanup | 2007: implicit destructors "incredible bogosity" | 2023+: explicit scope cleanup accepted, `-Wdeclaration-after-statement` relaxed | §4, §16 |
| Type safety vs readability in helpers | 2007: "type safety in this area is probably less important than the code just being readable" | 2025: typed-return `kmalloc_obj` accepted, tree-wide 2026 | §15 |
| `min()`/`max()` | 2001: explicit type argument required | 2024: rewritten for compile cost and signedness checks | §11, §15 |
| `char` signedness | Tolerated architecture differences | 2022: `-funsigned-char` kernel-wide | §11 |
| C standard | gnu89 for decades | 2022 gnu11; 2025 C23 `auto` | §20 |
| Array parameters | 2015: they don't exist, misleading | 2025: `[static N]` accepted | §17 |
| Rust | 2020 build-test it; 2021 conditions | 2025 maintainers cannot block; 2025-12 drivers; 2026 "simpler tool" is still C | §8 |
| Tone | Pre-2018 sharper ("shooting offense") | Same positions, calmer wording; still capital-letter emphasis | — |

Treat the later column as current.

## Not in corpus

- The well-known "C++ is a horrible language" message *is* in the corpus (2007-09-06 thread,
  `alpine.LFD.0.999.0709061839510.5626@evo.linux-foundation.org`); not quoted here beyond the abstraction passage
  because the colourful part carries less reasoning.
- No direct statements found on **TypeScript** or JavaScript as languages.
- No direct statements on **Python** as a language, only as a build/doc dependency.
- No **Zig** opinion found (searched lightly).
- **Go**: one 2011 message (array sizing); no general opinion.
- No explicit attack on **operator overloading** by name; covered only via implicit behaviour and explicit syntax.
- No developed opinion on `bool` found.

## What I looked for and did not find

- A general view of garbage collection beyond the 2007 "explicit, opt-in GC" remark.
- Early (1991–95) Usenet posts with language philosophy: only scattered remarks (e.g. 1993 "volatile ... usually
  worthless").
- Statements on generics/templates beyond 2007 approval of templates.
- Statements on dynamic typing.
- `coding-style.rst` sections on macros and inlines exist but were mostly written by others, so they are not quoted
  as his words.

## Checked vs inferred

- **Checked:** every quote (verifier clean), dates and URLs from `corpus.db`, the timeline entries.
- **Inferred (mine):** all "Outside the kernel" mappings to Rust/Python/TypeScript, unless a sentence cites him;
  severity labels where based on a few cases; "support" counts are approximate counts of messages I read that
  back each principle.
