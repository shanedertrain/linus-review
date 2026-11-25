# Language features, types and compilers

Load this when: the diff touches macros, decorators, casts, type aliases, lint suppressions, build flags, error or
overflow handling, scoped cleanup or `unsafe` Rust, or an argument rests on what the standard allows.

Basis note: his statements are about C, the kernel and kernel Rust. He has said nothing about Python or TypeScript, so
every example in those languages is our inference.

## Quick scan
1. Can a reader see at the call site where this line allocates, fails, exits, cleans up or converts?
2. Does this macro or decorator behave like the call it looks like?
3. Does silencing this warning make the code better or only quieter? Is the build clean?
4. Did a cast, alias or type assertion hide a wrong type?
5. When this check fails, is the failure handled at an explicit point, or does the program die?
6. Is scoped cleanup declared with the acquire?
7. Does the code or its defence rest on what the spec permits rather than what it says?
8. (C) Are UB-based optimisations and type-based aliasing turned off?
9. (C) Is the signedness of `char`, enums, bitfields, typedefs what the reader thinks?
10. (C) Is `volatile` on an access, or on a data declaration?
11. (Rust) Can this panic on a recoverable error? Is `unsafe` a small core behind a safe API?
12. (Rust) Is the code judged on what it does, not its language?

## 1. Allocation, control flow, lifetimes and conversions are visible where they happen
**Severity:** rework (reject for a new framework-wide mechanism)      **Basis:** his words about C++ in the kernel, transfer inferred
**Rule:** From a line and its immediate context, a reader must be able to tell whether it allocates, can fail, can
leave the function, runs code at scope exit, or converts a type. What he objects to is features that hide these, not
the language they come from.
**Look for:**
- Property access, operators or constructors that allocate or do I/O. Inferred: a Python `@property` making a
  network call, ORM attribute access running a query, a TypeScript getter with side effects, a Rust `Deref`/`Drop`
  doing real work.
- Implicit conversions between user types (in Rust, a `?` that converts errors through `From`).
**Why:** If you need the big picture to understand one line, that is a bad sign. Allocation is among the largest
performance costs, so it must be explicit.
**Unless:** The abstraction is explicit and opt-in (he liked templates, an opt-in GC, sparse's `__user`). He never
attacked operator overloading by name; it falls under this rule only when it hides cost or side effects.
**He said:** "But I'm also a huge believer in *explicit*syntax*. People should see what is going on, and the abstraction should be explicit." (2007-09-23, `alpine.LFD.0.999.0709230911360.16478@woody.linux-foundation.org`)

## 2. Macros and metaprogramming act like what they look like
**Severity:** reject (he NAKed both C cases below), then rework      **Basis:** his words about C macros, transfer to decorators and Rust macros inferred
**Rule:** Something that looks like a function call must behave like one. It evaluates each argument once, does not
assign to its arguments, does not return from the caller, and takes no code blocks as arguments. Use a real
(inline) function wherever one can do the job.
**Look for:**
- Double evaluation, as in `#define MAX(a,b) ((a) > (b) ? (a) : (b))` called with `i++`.
- A hidden assignment such as `#define alloc_obj(p) (p = kmalloc(...))`. He NAKed this in 2025 and accepted the
  version that returns a typed pointer.
- `return` or `goto` inside a macro, or code passed as a macro argument.
- Inferred: Rust macros that hide `?` or `return`, and Python or TypeScript decorators that swallow exceptions,
  retry, or change arguments silently.
**Why:** A hidden assignment is far too easy to miss. Code is maintained far longer than it takes to write.
**Unless:** The macro needs something a function cannot have (the caller's type, `sizeof`, a constant) and still
acts like a function, as `min` and `container_of` do.
**He said:** "When it looks like a function, it should act like a function, and not evaluate its arguments multiple times." (2025-03-14, `CAHk-=wgiX0q0WCL+SFwVCYtG7JR3=2Rshse-5J3AO2Y4AgT7Jw@mail.gmail.com`)

## 3. Keep a warning only if fixing it improves the code; keep the build clean
**Severity:** rework (for a patch that makes code worse to silence a warning, or adds new warnings)      **Basis:** his words about compiler warnings, transfer to linters inferred
**Rule:** Fix the problem a warning points at, not the warning. If the only way to silence a warning makes the code
worse (a cast, a removed check, a dummy initialiser), disable that warning project-wide. Everything else is fatal:
the default build has no warnings.
**Look for:**
- Casts that only quiet sign warnings; `= 0` that only quiets maybe-uninitialised (hiding a real unset path).
- A range check losing an end (`idx < 0 || idx >= max` cut to `idx >= max` because the type is unsigned today).
- Local suppressions: `#pragma`; inferred: `eslint-disable`, `# type: ignore`, `# noqa`, `#[allow]`.
- New warnings; warnings-as-errors switched off for one directory.
**Why:** A bad warning makes people write worse code, and false positives make real warnings worthless. Warnings
that are not fatal stay around forever.
**Unless:** A good warning that happens to fire on your code is still good (assignment in `if`, missing
prototypes, `sizeof` on an array parameter). Extra warning levels (W=1, W=2) are not fatal. His 2008 *a warning is
not an error* is outdated: since 2021 warnings are fatal by default.
**He said:** "The warning literally causes bugs. It's not a safety net - it's the literal reverse of a safety net that encourages bad code, or leaving out good checks." (2025-02-21, `CAHk-=wgg2A_iHNwf_JDjYJF=XHnKVGOjGp50FzVWniA2Z010bw@mail.gmail.com`)

## 4. Types say what the values are: no casts to silence, no aliases without a reason
**Severity:** rework (grumble for aliases that are only noise)      **Basis:** his words about C casts, typedefs and const, transfer inferred
**Rule:**
- A cast means the author knows better than the type system, so it must be rare and deliberate. Needing one usually
  means a type is wrong somewhere else.
- A type alias needs a reason: it varies by configuration or platform, or it must be opaque. It never hides that
  something is a pointer.
- A parameter the function only reads takes the read-only type.
**Look for:**
- Casts that make a call compile (inferred: TypeScript `as unknown as T`, `any`; Python `cast()`; Rust `transmute`).
- `typedef struct foo *foo_p;`; aliases with no meaning; a strong type with no greppable escape, or one used casually.
- `char *` where `const char *` would do (inferred: TypeScript `readonly`, Rust `&` over `&mut`).
**Why:** A cast hides a wrong type. Saving typing is not a reason for an alias. `const` means you cannot write
through this pointer, not that the value is immutable.
**Unless:** Sized and endian types (`u32`, `__le32`), opaque handles reached only through helpers, and marked
escapes such as `__force`, as long as they are never used by mistake. `u32` versus `uint32_t` is not worth a fight.
**He said:** "it makes the code actively worse with adding random casts just to shut the compiler up." (2025-02-08, `CAHk-=whe1UZUGKbtaaRV7CfS=sGtB2ouYAriryZ6bscE+5AFhA@mail.gmail.com`)

## 5. Errors exit at an explicit point; crashing is not safety; target dangerous overflow
**Severity:** rework; reject for a mechanism that makes errors fatal or invisible (he NAKed trapping overflow types in 2026 and blanket wrap-around conversions in 2024)      **Basis:** his words about kernel C and Rust, transfer inferred
**Rule:** Errors leave by an explicit exit (`goto out`, a returned error, `Result` with `?`), never by an unseen
jump (asynchronous exceptions, setjmp, a type declared elsewhere that traps). Unsigned wrap is legitimate (hashes,
sequence numbers); check overflow, with a handled failure, where it is dangerous: allocation sizes, user indices,
implicit signed-to-unsigned conversion.
**Look for:**
- Checks with no handling path. Inferred: `unwrap()` in Rust libraries, `assert` validating input, `sys.exit` or
  `process.exit` in a library, bare `except:` or empty `catch {}`, exceptions as normal control flow.
- Sweeping patches making all arithmetic checked or wrapping; or `n * size` reaching an allocator unchecked
  (`check_mul_overflow`; inferred Rust: `checked_mul(..)?`, not `.unwrap()`).
**Why:** Error handling exits; it does not nest. A trap is invisible at the place it fires, and the only safe trap is
one with a clear, simple way to handle it. Treat overflow as wrong in specific cases and target those cases.
**Unless:** `goto` with legible syntax and no spaghetti is fine. An explicit exception exit with a label is good (he
called one a hand-coded try/catch). Assertions of internal invariants are a different matter.
**He said:** "Error handling does not nest: it exits." (2026-03-31, `CAHk-=wgKB5f3MM40FGGUWUm_9eyESe2PAqCa6uZ=YTi0CdPwDg@mail.gmail.com`)
"A dead machine is not a safe machine." (2026-03-31, `CAHk-=wg=q7ptcMyUAqPGDbX_DKHivJVppc8bP0zpQqzOky_avA@mail.gmail.com`)

## 6. Scoped cleanup is declared together with the acquire
**Severity:** rework      **Basis:** his words about kernel `cleanup.h`, transfer inferred
**Rule:** Automatic cleanup (C `guard()`; inferred: Rust guards, Python `with`, TypeScript `using`) is fine when the
release is declared at the acquisition in a visibly matching form. When to convert code: see the robustness reference.
**Look for:** a cleanup variable declared apart from its initialisation; a conversion leaving the old manual unlock
in place; conditional guards that leave it unclear whether the lock is held.
**Why:** Anything non-trivial is done explicitly and visibly. What matters is code that humans can read.
**Unless:** Current since 2023; his 2007 objection to implicit C++ destructors does not cover explicit per-variable cleanup.
**He said:** "But the *primary* thing should be about making the code itself legible and maintainable to humans." (2025-11-18, `CAHk-=wjD1r5dr_b7gpuPdTXGdXAtaM6wHBSJyzi-Zfw3-cqR6w@mail.gmail.com`)

## 7. Code means what it says; *the standard allows it* is not an argument
**Severity:** rework      **Basis:** his words about C compilers, transfer inferred
**Rule:** Code must not depend on the compiler or runtime inferring something the author never stated, and *the
spec permits it* never settles an argument on its own. What real implementations do decides. The whole project
uses one pinned language version.
**Look for:** standard or abstract-machine reasoning defending surprising behaviour; reliance on unspecified
behaviour (inferred: unordered-container iteration order); language versions differing across a codebase.
**Why:** An optimisation based on undefined behaviour is wrong; an optimisation is legitimate when it rests on what
the hardware does. Mixing standard versions has no upside.
**Unless:** Non-standard extensions that implementations agree on are fine. New standard features are adopted when
they help (gnu11 in 2022, C23 `auto`).
**He said:** "Optimizations based on undefined behavior are wrong. If you have to resort to those kinds of optimizations, your compiler is bad." (2024-02-09, `CAHk-=wjqtMfRySaBoShSivAL3SYbYDTEUz-hbc4xXSNUrpSaGg@mail.gmail.com`)

## C-specific

## 8. Turn off optimisations based on undefined behaviour; no reliance on type-based aliasing
**Severity:** reject (for removing the flags)      **Basis:** his words
**Rule:** Build with `-fno-strict-aliasing`, `-fno-strict-overflow` (or `-fwrapv`) and
`-fno-delete-null-pointer-checks`. Things alias, and slightly worse code generation is an acceptable price.
**Look for:** those flags removed; a null check after a dereference; signed overflow checks like `a + b < a`.
**Why:** Every nontrivial project has dodgy code. Exploiting undefined behaviour turns benign bugs into exploits.
**Unless:** Non-aliasing that the programmer states explicitly (`restrict`) is fine, because it is visible.
**He said:** "Removing the NULL pointer check turned a benign bug into a trivially exploitable one" (2018-04-04, `CA+55aFyZA5t-+OyzSDDPGjDoaKsh=Erz8zuoEdDo7hOCBU6ZfQ@mail.gmail.com`)

## 9. Signedness is not obvious from the declaration
**Severity:** rework      **Basis:** his words, transfer inferred
**Rule:** Unsigned types for bytes, bit patterns and bitfields; range checks on both ends; explicit comparison type
across types; no host signedness or sizes in on-disk or wire formats.
**Look for:** `char` used for bytes; `int flag:1`; min or max across a signed and an unsigned value. Inferred: Rust
`as` casts that truncate or flip the sign; JavaScript bitwise operators producing signed 32-bit results.
**Why:** The signedness of `char`, enums and bitfields is implementation-defined, and differences between
architectures are bad. In 2022 the kernel moved to `-funsigned-char`.
**Unless:** Bitfields are fine for in-memory flags, not for hardware or on-disk layouts.
**He said:** "I will actually argue that having signed bit-fields is almost always a bug" (2007-02-08, `Pine.LNX.4.64.0702081528070.8424@woody.linux-foundation.org`)

## 10. `volatile` goes on accesses, not on data
**Severity:** rework      **Basis:** his words, transfer inferred
**Rule:** Volatility is a property of a particular access. A `volatile` field or global usually means the locking
or ordering is wrong. Use access helpers (`READ_ONCE`/`WRITE_ONCE`) and real synchronisation.
**Look for:** `volatile` on a struct field or global; a race patched by adding it. Inferred: Java/C# `volatile`
fields standing in for synchronisation; Rust `read_volatile` outside MMIO.
**Why:** It usually means the data is not properly locked.
**Unless:** MMIO accessors and access helpers use it internally.
**He said:** "it's the *context* that makes a particular access volatile." (2024-03-25, `CAHk-=wjP1i014DGPKTsAC6TpByC3xeNHDjVA4E4gsnzUgJBYBQ@mail.gmail.com`)

## Rust

## 11. The host's rules beat the language's defaults; `unsafe` is a small core behind a safe interface
**Severity:** reject (panics on allocation failure were a blocker for merging Rust); rework for the design points      **Basis:** his words about Rust in the kernel, transfer to other hosts inferred
**Rule:** Embedded code follows the host's rules: fallible allocation returning `Result`, errors not panics, no
behaviour that changes silently with context. Build primitives on `unsafe`, wrap them in safe simple interfaces, and
inside `unsafe` don't create references with aliasing guarantees the author did not mean.
**Look for:** `unwrap()`/`expect()` on fallible operations; infallible allocation in kernel or embedded code; APIs
switching strategy on hidden context; contorted safe-only designs; `&mut` from raw pointers that may alias.
**Why:** An operation left unfinished is not better than a wrong answer, only easier to debug, so warn and carry
on. Check as much as possible statically. The `unsafe` part is what makes Rust powerful, and in unsafe code the
compiler should assume it does not understand what is going on.
**Unless:** The safe boundary is still required; this is not a licence for `unsafe` everywhere. In a user-space
program, `expect()` or an assertion on an internal invariant is judged under entry 5's Unless line, not as
a panic on a fallible operation.
**He said:** "An allocation failure in some random driver must never ever be something that the compiler just turns into a panic." (2021-04-14, `CAHk-=wiVY56LzwV_G075NEFwsdf-p7GOTy_cB7-UU9b=49rB1g@mail.gmail.com`)

## 12. His current position (2026): Rust augments C; judge the code, not the language
**Severity:** reject (for a review that blocks code for its language)      **Basis:** his words
**Rule:** Don't reject or praise a change for its language. Memory safety removes some bug classes, not logic
errors, so review safe-language logic as hard as C. A maintainer cannot forbid other-language users of an interface.
**Look for:** review comments aimed at the language rather than the code; claims that a Rust rewrite needs less
review.
**Why:** Kernel Rust reached real drivers by late 2025. He neither loves nor dislikes Rust (2024) and still finds C
the simpler tool (2026).
**He said:** "Rust fixes a few easy bugs that you can make in C, but it does not fix the logic errors, right? It does not think for you." (2026-07-01, `https://www.youtube.com/watch?v=YKkEe-PxW10`)
"So let me be very clear: if you as a maintainer feel that you control who or what can use your code, YOU ARE WRONG." (2025-02-21, `CAHk-=wgLbz1Bm8QhmJ4dJGSmTuV5w_R0Gwvg5kHrYr4Ko9dUHQ@mail.gmail.com`)
