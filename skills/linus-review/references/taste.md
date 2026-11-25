# Taste: functions, data structures and patches

Load this when: the diff adds or restructures functions, helpers, layers, names, comments, conditionals or
data types, or calls itself a cleanup or refactor.

## Quick scan

1. Is the code deeply nested or dense, or were lines split just to fit a width limit?
2. Do names describe the concept, match their siblings, and avoid letter jumbles?
3. Does each new helper or layer clarify something, without hiding a lock or a cost?
4. Do comments say why, rather than narrate the lines below them?
5. Is there a special case that a better representation would make the normal case?
6. Is something clever where the obvious version would do?
7. Is anything built for a future user, or kept alive by a *what if*?
8. Is code shared between different concepts, or copied between identical ones?
9. Does this cleanup improve something you can point to, or is it churn?
10. Are feature, platform or version conditionals scattered through function bodies?
11. Would a different data layout remove the special cases, side caches or ambiguity?

## 1. Shallow nesting, plain expressions
**Severity:** rework      **Basis:** his words; non-C examples inferred
**Rule:** Deep indentation means the function needs splitting. Judge complexity by what each statement and
expression does, not by line count or column width.
**Look for:**
- More than three or four indentation levels, especially new error handling nested in old branches.
- One big `switch`/`match` function whose arms could be named functions.
- Nested ternaries, assignments inside conditions, `&&`/`||` chains over several lines; several `if`
  statements or a small named function read better.
- Expressions broken across lines only to satisfy a line-length limit.
**Why:** Dense statements hide the logic, and deep nesting is unreadable even when it fits on screen.
He calls lines-of-code a bogus metric.
**Unless:** A long but flat function is acceptable. An occasional long line beats a split one; he rejects
80 columns as a hard rule. A patch that adds lines but is conceptually simpler is good. Numeric
function-length limits (screenfuls, number of locals) come from the multi-author kernel style document,
not his mail; do not cite them as his.
**He said:** "But _splitting_ lines isn't the answer. Making code simpler is, but somehow the 80-column warning never causes that to happen - instead people just split." (2009-04-08, `alpine.LFD.2.00.0904081341090.4583@localhost.localdomain`)

## 2. Names: the concept, written out, consistent
**Severity:** rework (reject when a rename makes a good name worse)      **Basis:** his words
**Rule:** Name things for what they mean to the caller, not how they work. Exported names carry their
context; locals do not repeat it. Consistency with existing names beats a locally better name.
**Look for:**
- Mechanism names (`safe`, `fast`, `v2`) instead of the condition or result.
- Abbreviations near-identical to siblings (`rdllink` beside `rdllist`); cute names; Hungarian prefixes.
- A rename for the sake of *using the generic function* that makes a clear name vaguer.
- Aliases hiding that something is a pointer (`typedef struct foo *foo_t;`).
**Why:** The call site should read without looking up the definition. A function too trivial to be given
a written-out name should not exist.
**Unless:** Short locals are fine where the context is obvious. A type alias is fine when the type really
varies by build or is deliberately opaque. He has merged renames he disliked at a maintainer's request.
**He said:** "Naming - like comments - shouldn't be about what some implementation is, but about the concept." (2020-05-01, `CAHk-=wh1SPyuGkTkQESsacwKTpjWd=_-KwoCK5o=SuC3yMdf7A@mail.gmail.com`)
"much worse than a bad name is to use a name that is not consistent." (2010-05-08, `alpine.LFD.2.00.1005081455450.3711@i5.linux-foundation.org`)

## 3. Helpers and layers must help, and must not hide
**Severity:** rework (often grumble; reject for hidden synchronisation)      **Basis:** his words; framework and ORM examples inferred
**Rule:** A helper, wrapper or layer earns its place by naming a concept, encoding a rule, removing real
duplication or splitting a complex expression. A thin rename, or a layer that hides locking, ordering or
cost from the call site, makes code harder to read.
**Look for:**
- Pure forwarders (`getFoo(x)` for `x.foo`), adopted by search-and-replace across many files.
- Near-identical helper families whose differences nobody can state.
- A specialised one-caller helper placed in a shared module that everyone must learn.
- Layer stacks with one implementation each, where nobody can tell if a call is cheap.
- Locks taken inside helpers with no hint in the name; annotations on data (`volatile`, decorators,
  properties that run queries) standing in for rules that belong to particular accesses.
**Why:** Wrappers bring churn, rules to learn and bad names. Access rules belong to the code, not the
data; a hidden lock cannot be found by searching for it.
**Unless:** A local helper used once or twice is good when it makes each part readable on its own or
replaces a comment. A wrapper whose name states the rule (a named lock-and-read function) is welcome: the
objection is to hiding, not naming. Abstraction is worth it where real variation is expected.
**He said:** "Dammit, if we add wrapper and "helper" functions, they should *help*, not confuse." (2015-02-21, `CA+55aFwZ9X2XYzwkTvxANOMN8T9aynUCLCr5wKdahfdOX5fXig@mail.gmail.com`)
"It's not the *data* that has access rules, it's the *code* that has rules of access." (2012-02-01, `CA+55aFw=z2SKFGoSE5e_0ZmKcAAjK5q0DBM4PaxBH2D9tuikzA@mail.gmail.com`)

## 4. Comments explain why, not how
**Severity:** rework      **Basis:** his words
**Rule:** Make code readable without comments first. A comment gives the reason, or the what at a higher
level, aimed at the reader most likely to get it wrong.
**Look for:**
- Line-by-line narration, end-of-line comments, box comments, docstrings restating the signature.
- A comment explaining a messy block that a named helper would make obvious.
- An unusual choice (skipped lock, ignored error, deliberate race) with no comment saying why it is safe.
- A warning addressed to callers who already do the right thing; comments the diff makes stale.
**Why:** Comments about code details go stale and are likely bogus. Without the why, nobody remembers
why a mess exists.
**Unless:** For subtle code he often asks for a big comment as well as a helper. End-of-line comments are
fine in assembly.
**He said:** "This comment is useless - because it's aimed at the wrong people." (2020-08-10, `CAHk-=whUVHA-=4mwGaUA42teESc2mX1nwZjbbOMQsvPaoYxh3w@mail.gmail.com`)

## 5. Make the special case the normal case
**Severity:** rework (reject when it patches over a bug)      **Basis:** his words
**Rule:** When code branches for the first element, the empty case, the disabled case or a sentinel, look
for a representation that needs no branch.
**Look for:**
- Head-versus-middle branches:
  ```c
  if (prev) prev->next = entry->next; else head = entry->next;   /* two cases */
  for (pp = &head; *pp != entry; pp = &(*pp)->next) ; *pp = entry->next;   /* one */
  ```
- Dummy head nodes added only to dodge that branch.
- Enabled flags tested at every use, where a valid empty structure would do (an empty list, not `None`).
- Overloaded sentinels; hard-coded lists of exception values; a fix adding a magic case for one caller.
**Why:** Special cases scatter magic details through the code, hide bugs and accumulate.
**Unless:** One explicit special case beats new generic infrastructure built to avoid it. A necessary one
should be confined to the place it matters, with a big comment. Hardware and external-format quirks may
need one.
**He said:** "Special case code is bad. It's certainly a lot more important to me to have a straightforward approach that doesn't have any strange cases, and where debugging "just works", instead of having a lot of magic small details scattered all over the place." (2002-12-22, `Pine.LNX.4.44.0212211858240.8783-100000@home.transmeta.com`)

## 6. Simple to think about beats clever
**Severity:** rework (reject for ad-hoc concurrency schemes)      **Basis:** his words
**Rule:** Prefer the version that is easy to reason about. Cleverness must buy something measured in a path
that matters, be isolated and be explained.
**Look for:**
- Hand-rolled synchronisation; invariants encoded in combinations of flags and null fields.
- Bit or metaprogramming tricks in code that is not hot, or that only work for unguaranteed inputs.
- A series piling more machinery onto an already-buggy clever design.
**Why:** Subtle schemes are where bugs live; obvious rules can be checked.
**Unless:** He likes measured, small, commented cleverness in real hot paths, and a cleaner rewrite that
is measurably slower loses. Ask for numbers.
**He said:** "Any time people do ad-hoc locking with "clever" schemes, it's almost invariably buggy." (2009-10-14, `alpine.LFD.2.01.0910131744590.3404@localhost.localdomain`)
"So at some point I just decided that "optimal" was less important than "simple to think about"." (2012-02-19, `CA+55aFxJvGRjF63Dv=W7pc3tPcFom1-cGJcoFjGG1CeXkwtMVw@mail.gmail.com`)

## 7. Build for the need in front of you
**Severity:** rework (reject for public interfaces with no real user)      **Basis:** his words; app-framework transfer inferred
**Rule:** Solve the concrete problem with the straightforward change. Frameworks, plug-in points,
expose-anything interfaces and future-proofing need a real current user, not an example.
**Look for:**
- A small need answered with a registry, strategy hierarchy, config system or generic container.
- Loosely typed bags of fields (`dict[str, Any]`, `Record<string, unknown>`) because the author has not
  decided what to expose.
- Options or endpoints whose only user is a demo or a test.
- Code kept or added for callers that may never come; unexplained disabled blocks.
**Why:** Overdesign multiplies concepts without users; interfaces with one or two minor users become
long-term maintenance burdens.
**Unless:** Over-engineering inside the author's own module bothers him far less than in shared library
code. Small, safe infrastructure merged just ahead of its users is fine. Disabled code kept as commentary
on a rejected approach is acceptable with a comment.
**He said:** "It's a huge sign of over-design and "I don't know what the hell I want to expose, so I'll make this generic thing that can expose anything, and then I start adding random fields"." (2020-08-17, `CAHk-=wig0ZqWxgWtD9F1xZzE7jEmgLmXRWABhss0+er3ZRtb9g@mail.gmail.com`)
"let's not use "what if" as an argument to keep unused code around." (2018-05-05, `CA+55aFzX9CeRr3HZtVN5XKK2Ema5TjXo4FCgD8ukWz6Waz=pZw@mail.gmail.com`)

## 8. Share the same concept, separate different ones
**Severity:** rework      **Basis:** his words
**Rule:** Merge copies of one concept. Do not force different things through one common routine;
simple duplication beats a complex sharing interface.
**Look for:**
- One function with mode parameters and different rules or early exits per mode.
- A common layer joining two features, so a change for one risks the other.
- Conversely: near-identical copies differing in one token, or every caller writing the same wrapper.
**Why:** Sharing ties separate things together, and the shared code takes an odd shape to serve conflicting
needs.
**Unless:** One interface with many real users wants a common layer. Ask whether the parts are the same
concept, not whether the lines look alike.
**He said:** "it's a lot better to have the same (simple) code duplicated five times than it is to make a (much more complex) interface to have things shared." (2005-01-27, `Pine.LNX.4.58.0501271312440.2362@ppc970.osdl.org`)

## 9. A cleanup must improve something
**Severity:** rework (reject repeated churn or cleanups that break things)      **Basis:** his words
**Rule:** A cleanup or refactor must make code demonstrably simpler or clearer, with no unadmitted
behaviour change. Mechanical churn and edits that only silence a tool are not cleanups.
**Look for:**
- Large diffstat, no conceptual gain: mass renames, a wrapper adopted in 150 places, file shuffles.
- A refactor that reads worse, or changes semantics while claiming not to.
- Code contorted to satisfy a linter, type checker or compiler warning.
**Why:** Change for its own sake has pain and no gain, and cleanups have repeatedly brought subtle bugs.
**Unless:** Real cleanups are welcome; *looks cleaner* matters for maintenance. A large mechanical change is
fine when trivially verifiable and it enables real work. Credit patches that remove special cases, make a
component independent of the rest, or make the compiler reject unconverted callers.
**He said:** "I don't mind cleanups, but this is "churn". Change for its own sake. If it doesn't lead to any _improvement_, it's pointless." (2008-04-24, `alpine.LFD.1.10.0804231914270.2779@woody.linux-foundation.org`)

## 10. Keep conditionals out of function bodies
**Severity:** rework      **Basis:** his words about C `#ifdef`; transfer to flags and platform checks inferred
**Rule:** Feature, platform and version conditionals inside function bodies mean one problem was treated
as two. Put the variation behind an interface (a helper with a no-op variant, a per-platform module).
**Look for:**
- `#ifdef`, `#[cfg]`, `if sys.platform`, `if (config.featureX)` scattered through logic.
- A fix that only respells the condition as another macro without abstracting it.
- The same runtime enabled-check repeated at many call sites.
**Why:** Conditionals destroy the linearity of the code; pushing them out forces better interfaces.
**Unless:** A one-off condition right where it is needed, with a comment saying why, is fine. A condition
in normal control flow beats a preprocessor block, but a named helper is better still.
**He said:** "I hate code that has #ifdef's. It's a major design mistake, and shows that the person who coded it didn't think of it as _one_ problem, but as two." (2001-08-08, `https://yarchive.net/comp/linux/ifdefs.html#1`)

## 11. Data structures before code
**Severity:** rework      **Basis:** his words
**Rule:** Review the data layout and its invariants before the code. An ambiguous structure produces
special cases no code polish fixes. A value the program needs belongs in the real structure, not a side cache.
**Look for:**
- A schema or type that can represent one thing two ways, or state kept in sync in two places.
- A new cache or side table because the main structure lacks a field.
- An API forcing callers to allocate separately instead of embedding state in their own structures.
**Why:** Bugs often come from a structure losing a property, such as being unambiguous.
**Unless:** He accepted adding data to a core format once it had become core; weigh format-change costs.
**He said:** "Bad programmers worry about the code. Good programmers worry about data structures and their relationships." (2006-07-27, `Pine.LNX.4.64.0607270936200.4168@g5.osdl.org`)

## Position changes

- One-use helpers: 2022 said exported ones should go; 2025 called local ones good for readability. Apply
  2025 to local helpers, 2022 to shared ones.
- `#ifdef`: refused outright in 2001; since about 2010 he usually asks for a named helper, or merges and complains.
