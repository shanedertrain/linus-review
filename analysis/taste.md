# Theme: taste

What Linus Torvalds treats as good and bad code at the level of a function, a data structure and a patch.

Method: about 70 FTS searches (praise words, annoyance words, and topic words: special case, data structure,
clever, subtle, overdesign, abstraction, wrapper, helper, #ifdef, indentation, naming, typedef, comment, churn,
cleanup, "removes more lines", future-proof, "what if", real users), read as keyword-in-context extracts of his own
(non-`>`) paragraphs, plus about 45 documents read in full. Roughly 400 distinct messages seen, 1992 to 2026-11.
Every quote below is in `analysis/taste.quotes.jsonl` and passes `scripts/verify_quotes.py` (113/113). The kernel
`coding-style.rst` was used only as a cross-check, and is cited once where his mail says he wrote the passage.

A note on the word itself. "Good taste" for him is a judgement about people as much as code (he uses it to decide
whom he pulls from without review), and his own definition is deliberately vague: seeing the problem so that the
special case disappears, and "really seeing the big patterns". The concrete, reviewable content of "taste" is the
set of principles below. Several of them are the same instinct seen from different sides: make one concept, make
it visible, and do not build what nobody needs.

---

## 1. Rewrite until the special case disappears

**Principle.** When code has a branch for "the first element", "the empty case", "the disabled case", or a
sentinel value that means something different, look for a representation in which that case is just the normal
case. Code that handles one case uniformly beats code that handles two cases correctly.

**What triggers it in a review.**
- `if (prev) prev->next = x; else head = x;` and every structural cousin: separate code for head vs middle, first
  iteration vs later, empty vs non-empty container.
- Dummy head elements added only so the insertion code avoids a branch (he calls this the *bad* fix).
- Global "is this subsystem enabled/initialised" flags tested everywhere, instead of keeping the data structure
  valid-and-empty when the feature is off.
- In-band sentinels with overloaded meaning (`buf.head == NULL` means "don't flush") and lists of exceptions
  ("special-case signals X, Y, Z", per-machine quirk tables).

```c
/* triggers the comment */
if (prev) prev->next = entry->next; else list_head = entry->next;
/* what he wants */
for (pp = &list_head; *pp != entry; pp = &(*pp)->next) ;
*pp = entry->next;
```

**His reasoning.** Special cases are where bugs hide and where debugging stops "just working"; they accumulate
("magic small details scattered all over the place") and "end up biting us". Seeing the uniform formulation is, for
him, the visible sign of understanding the problem (pointer-to-pointer is his standing example since at least 2012).

**How serious.** High. He reverted a regression fix rather than accept what he called a magic special case for brk (2004);
he rejects per-machine exception tables; in reviews he often writes the uniform version himself.

**Limits and exceptions.** He is not a purist. When the alternative to one explicit special case is new generic
infrastructure, he prefers the special case (2009 async suspend: "it may not be pretty, but it sure is simple").
A necessary special case should be confined to the one place it matters, with a big comment, rather than leaking
special handling into other code (2019). He also accepts ugly special cases at hardware or ABI boundaries he cannot
change. So the rule is "eliminate special cases where a better representation exists; otherwise isolate and label
them", not "never branch".

**Outside the kernel.** Transfers directly: null-object/empty-collection instead of `None` checks, sentinel-free
iteration, initialising state so "disabled" is a valid empty state, avoiding boolean "mode" flags that make one
function two. Applies in any language.

**Evidence.**
- "sometimes you can see a problem in a different way and rewrite it so that a special case goes away and becomes the normal case and that's good code" (`https://www.youtube.com/watch?v=o8NPllzkFhE`, 2016-05-03, TED talk, auto-caption transcript)
- "People who understand pointers just use a "pointer to the entry pointer", and initialize that with the address of the list_head. And then as they traverse the list, they can remove the entry without using any conditionals, by just doing a "*pp = entry->next"." (`https://meta.slashdot.org/story/12/10/11/0030249/linus-torvalds-answers-your-questions`, 2012-10-11)
- "I say "no good reason", because there *is* a reason for it: it allows code to avoid the special case of empty list and adding entries to before the first entry etc etc.  But that reason is a really *bad* reason, because it's valid only because people don't understand basic list manipulation and pointers to pointers." (`eb47b2a8d8764778697ac2fdb342c976cd487ca3`, 2014-03-10, https://github.com/subsurface/subsurface/commit/eb47b2a8d8764778697ac2fdb342c976cd487ca3)
- "Special case code is bad. It's certainly a lot more important to me to have a straightforward approach that doesn't have any strange cases, and where debugging "just works", instead of having a lot of magic small details scattered all over the place." (`Pine.LNX.4.44.0212211858240.8783-100000@home.transmeta.com`, 2002-12-22, https://lore.kernel.org/all/Pine.LNX.4.44.0212211858240.8783-100000%40home.transmeta.com/)
- "Random special cases in code are just evil, and end up biting us in the end." (`Pine.LNX.4.58.0402100814410.2128@home.osdl.org`, 2004-02-10, https://lore.kernel.org/all/Pine.LNX.4.58.0402100814410.2128%40home.osdl.org/)
- "The proper fix in that case (in my opinion, and the one that thus got committed ;^) was simply to make sure that the data structures were simply always consistent (and empty), even if the code itself was disabled. That just automatically meant that it didn't need any global flags to be tested." (`alpine.LFD.1.00.0803041009210.12253@woody.linux-foundation.org`, 2008-03-04, https://lore.kernel.org/all/alpine.LFD.1.00.0803041009210.12253%40woody.linux-foundation.org/)
- Limit: "For suspend, the only other case we've seen has been the keyboard and mouse controller, which has exactly the same "we can special case it with a single 'let's do _this_ device asynchronously'". Again, it may not be pretty, but it sure is simple." (`alpine.LFD.2.00.0912150726510.14385@localhost.localdomain`, 2009-12-15, https://lore.kernel.org/all/alpine.LFD.2.00.0912150726510.14385%40localhost.localdomain/)
- Limit: "And then we'd limit the special case to where it matters (with a big comment about what's going on), rather than adding random special case handling to random _other_ places." (`CAHk-=wiA-WbrFrDs-kOfJZMXy4zMo9-SZfk=7B-GfmBJ866naw@mail.gmail.com`, 2019-05-03, https://lore.kernel.org/all/CAHk-%3DwiA-WbrFrDs-kOfJZMXy4zMo9-SZfk%3D7B-GfmBJ866naw%40mail.gmail.com/)
- Also: "Good taste is about really seeing the big patterns and kind of instinctively knowing what's the right way to do things." (same TED transcript)

**How well supported.** Strong. About 30 messages, 2002 to 2026 (plus 2009 tty locking, 2007 signalfd "Listign special cases is just ugly", 2014 PAGE_NUMA, 2023 splice "Pure random special cases", 2024 "Instead of adding _more_ special cases for size 8, we could just remove them").

---

## 2. Get the data structures right; the code follows

**Principle.** Review the data layout and its invariants before the code. A design with a few unambiguous core
concepts and data structures produces simple code; a muddled or ambiguous data structure produces special cases and
bugs that no amount of code polish fixes. Values the program needs belong in the real data structure, not in a side
cache.

**What triggers it in a review.**
- A format or struct that can represent the same thing two ways (two kinds of delta, optional fields that change
  meaning), or state that must be kept consistent across two places.
- A new cache/side table "because the main structure doesn't have it".
- An API that forces callers to allocate separately instead of letting them embed state in their own structures.
- Code that grows special cases to compensate for a data model that does not match the problem.

**His reasoning.** He attributes git's success to designing "around the data"; the 2006 aphorism (bad programmers
worry about code, good ones about data structures and relationships) is in the corpus verbatim. Good design "isn't
actually to be really smart about it, but to try to have a few basic concepts". When a bug appears he often traces it
to the data structure losing a property (unambiguity) rather than to the code.

**How serious.** High for anything persistent or shared (git formats, kernel core structures, interfaces); he
fights format changes that make the data "worse" and rejects side caches. For local data it is advice.

**Limits and exceptions.** He accepted a generation number embedded in pack files as not "ugly" because pack files
had become core data (2011). He admits his own mistakes (binary hashes in tree objects, 2008), so the principle is
about effort and priority, not infallibility.

**Outside the kernel.** Fully transferable: schema and type design first, one source of truth, avoid duplicate
representations, avoid derived caches without a consistency story, let callers own memory/state where performance
matters.

**Evidence.**
- "In fact, I'm a huge proponent of designing your code around the data, rather than the other way around, and I think it's one of the reasons git has been fairly successful (*)." (`Pine.LNX.4.64.0607270936200.4168@g5.osdl.org`, 2006-07-27, https://lore.kernel.org/all/Pine.LNX.4.64.0607270936200.4168%40g5.osdl.org/)
- "(*) I will, in fact, claim that the difference between a bad programmer and a good one is whether he considers his code or his data structures more important. Bad programmers worry about the code. Good programmers worry about data structures and their relationships." (same message)
- "I think the code got less understandable, and had more special cases, just because now we have two totally different kinds of deltas. So maybe I'm reacting to the fact that I think the bug happened in the first place for a very simple reason: the data structure wasn't unambiguous any more." (`Pine.LNX.4.64.0610171959180.3962@g5.osdl.org`, 2006-10-18, https://lore.kernel.org/all/Pine.LNX.4.64.0610171959180.3962%40g5.osdl.org/)
- "the way to do good basic design isn't actually to be really smart about it, but to try to have a few basic concepts." (`Pine.LNX.4.64.0610172014250.3962@g5.osdl.org`, 2006-10-18, https://lore.kernel.org/all/Pine.LNX.4.64.0610172014250.3962%40g5.osdl.org/)
- "I think that if we have a value that we need, then it should be recorded. In the data structures. Not in some random other location that isn't part of the real git data structures." (`CA+55aFyDzr+SfgSzWMr9pQuQUXTw9mcjZ-00NZof74PKZzbGPA@mail.gmail.com`, 2011-07-15, https://lore.kernel.org/all/CA%2B55aFyDzr%2BSfgSzWMr9pQuQUXTw9mcjZ-00NZof74PKZzbGPA%40mail.gmail.com/)
- "a willingness to not abstract away the data structures and algorithms, because those are the *whole*point* of core git." (`alpine.LFD.0.999.0709070203200.5626@evo.linux-foundation.org`, 2007-09-07, https://lore.kernel.org/all/alpine.LFD.0.999.0709070203200.5626%40evo.linux-foundation.org/)
- "It's really that the crypto interfaces are *designed* so that you have to allocate things separately, and can't embed these things in your own data structures." (`CAHk-=wjr1w7x9Rjre_ALnDLASYNjsEHxu6VJpk4eUwZXN0ntqw@mail.gmail.com`, 2019-09-27, https://lore.kernel.org/all/CAHk-%3Dwjr1w7x9Rjre_ALnDLASYNjsEHxu6VJpk4eUwZXN0ntqw%40mail.gmail.com/)

**How well supported.** Good. About 20 messages, 2001 to 2019. The aphorism itself occurs once; the supporting
pattern (fix the representation, not the code) recurs.

---

## 3. Rules and costs must be visible where the code runs

**Principle.** Access rules, locking, ordering and cost belong at the point of use, explicit in the code, not hidden
in a type declaration, a header, or a helper whose name does not say what it locks. A reader should be able to see
from the call site what is happening and roughly what it costs.

**What triggers it in a review.**
- `volatile` (or any "magic" qualifier/attribute/decorator) on data fields to get behaviour that is really a
  property of particular accesses.
- Helpers that take or drop locks internally with a name that does not say so; macros that hide whether a lock is a
  spinlock or a sleeping lock; macros that hide control flow or loops.
- Generic "abstraction" macros wrapping a plain operation so that the reader must look elsewhere to know the semantics.

**His reasoning.** "It's not the *data* that has access rules, it's the *code* that has rules of access." Hiding the rule in the declaration
means nobody reading the code can check it; hiding locks in helpers means you cannot grep for lock usage and makes
that use different from every other use.

**How serious.** High for concurrency and memory ordering (he has refused `volatile` on data structures since 2001
and still pushes READ_ONCE/WRITE_ONCE at the access); medium for style-level helpers.

**Limits and exceptions.** A wrapper that *documents a rule* is welcome (2015: a `d_revalidate_inode()` "would
actually be *documentation*"; 2020: he would hide `cred_guard_mutex` locking in a named `task_cred_read_lock()`
function). The objection is to hiding, not to naming. One historical exception: the low bits of `jiffies` (2004).

**Outside the kernel.** Transfers: avoid ORM/proxy magic that hides queries in attribute access, hidden locking in
getters, decorators that change concurrency semantics, implicit global state. Prefer explicit calls at the point
where the behaviour matters.

**Evidence.**
- "You should not hide algorithmic choices in your data structures. You should make them explicit, so that when you read the code you _see_ what assumptions people make." (`Pine.LNX.4.33.0107231546430.7916-100000@penguin.transmeta.com`, 2001-07-23, https://lore.kernel.org/all/Pine.LNX.4.33.0107231546430.7916-100000%40penguin.transmeta.com/)
- "Marking data structures is seriously stupid and wrong. It's not the *data* that has access rules, it's the *code* that has rules of access." (`CA+55aFw=z2SKFGoSE5e_0ZmKcAAjK5q0DBM4PaxBH2D9tuikzA@mail.gmail.com`, 2012-02-01, https://lore.kernel.org/all/CA%2B55aFw%3Dz2SKFGoSE5e_0ZmKcAAjK5q0DBM4PaxBH2D9tuikzA%40mail.gmail.com/)
- "I hate hiding locks in "helper functions". You search for the lock, and now you've hidden that "siglock" usage away and made it very different from all the other siglock usage." (`Pine.LNX.4.58.0502260947230.25732@ppc970.osdl.org`, 2005-02-26, https://lore.kernel.org/all/Pine.LNX.4.58.0502260947230.25732%40ppc970.osdl.org/)
- "abstraction like this is _bad_, for christ sake! Don't hide what locks you're using just to make the code look simpler." (`an0cd5$262$1@penguin.transmeta.com`, 2002-09-27, https://lore.kernel.org/all/an0cd5%24262%241%40penguin.transmeta.com/)
- "But I'm also a huge believer in *explicit*syntax*. People should see what is going on, and the abstraction should be explicit." (`alpine.LFD.0.999.0709230911360.16478@woody.linux-foundation.org`, 2007-09-23, https://lore.kernel.org/all/alpine.LFD.0.999.0709230911360.16478%40woody.linux-foundation.org/)
- "The advantage of READ_ONCE() over using "volatile" in a data structure tends to be that you explicitly mark the memory accesses that you care about." (`CA+55aFxOc7_s-BbWJx-kyit-pH9m5fQJk6MSMJ57tFFvMtNh-w@mail.gmail.com`, 2018-08-15, https://lore.kernel.org/all/CA%2B55aFxOc7_s-BbWJx-kyit-pH9m5fQJk6MSMJ57tFFvMtNh-w%40mail.gmail.com/)

**How well supported.** Strong for the volatile/locking core (about 20 messages, 2000 to 2019); the general
explicit-syntax claim fewer (about 6).

---

## 4. Simple and obvious beats subtle and clever

**Principle.** Prefer the straightforward version that is easy to reason about over the clever one, especially for
locking, state machines and anything that has been buggy before. Cleverness must buy something measurable in a path
that matters, and must not surprise the reader or the maintainer.

**What triggers it in a review.**
- Ad-hoc synchronisation schemes; invariants expressed as combinations of flags and NULL pointers.
- Bit tricks or macro cleverness in code that is not hot, or tricks that rely on input ranges the code does not
  guarantee (`(x) | 0x20` used on non-letters).
- A clever generalisation that has already needed several fixes, and a series that "doubles down" on it.
- An area with a history of bugs where the patch argues for reusing the existing subtle logic rather than adding a
  clear new state.

**His reasoning.** Subtlety is where bugs live ("Subtle and clever and complex is what got us to the crap
situation"); obvious rules can be checked by reviewers. In his own work he chooses "simple to think about" over
"optimal" when he cannot convince himself of correctness.

**How serious.** High when correctness is at stake (locking, cpu hotplug): he writes the simple patch himself and
argues for it. Lower for cosmetic cleverness: he grumbles and merges (2008 vsnprintf).

**Limits and exceptions.** He is not against cleverness as such ("I don't disagree with being clever"). He spent
weeks on word-at-a-time hashing and SHA1 code-generation tricks in hot paths and posted them proudly (2009 blog,
2012 G+), isolated in small commented helpers. Clean code matters less to him than good results: a cleaner rewrite that
is slower loses (2007). So: clever is fine where measured, isolated and labelled; not as a default.

**Outside the kernel.** Transfers: concurrency code, caches, retry logic, state machines. In application code the
bar for "hot path that justifies a trick" is higher still.

**Evidence.**
- "I do NOT understand why you seem to argue for being "subtle" and "clever", considering the history of this whole setup. Subtle and clever and complex is what got us to the crap situation." (`alpine.LFD.1.10.0807141707410.3017@woody.linux-foundation.org`, 2008-07-15, https://lore.kernel.org/all/alpine.LFD.1.10.0807141707410.3017%40woody.linux-foundation.org/)
- "Any time people do ad-hoc locking with "clever" schemes, it's almost invariably buggy. So the rule is: just don't do that. Make the locking rules "obvious".  Don't have subtle rules about "if head is NULL, then we're not going to add any new buffers to it, except if tail is also NULL"." (`alpine.LFD.2.01.0910131744590.3404@localhost.localdomain`, 2009-10-14, https://lore.kernel.org/all/alpine.LFD.2.01.0910131744590.3404%40localhost.localdomain/)
- "So at some point I just decided that "optimal" was less important than "simple to think about"." (`CA+55aFxJvGRjF63Dv=W7pc3tPcFom1-cGJcoFjGG1CeXkwtMVw@mail.gmail.com`, 2012-02-19, https://lore.kernel.org/all/CA%2B55aFxJvGRjF63Dv%3DW7pc3tPcFom1-cGJcoFjGG1CeXkwtMVw%40mail.gmail.com/)
- "So yes, it works, but let's face it, that clever trick saved something like two instructions and a branch from a code-path that wasn't really even critical!" and, same message, "In general, I don't disagree with being clever. People enjoy tricks like that, and I don't really disagree with the patch." (`alpine.LFD.1.00.0802092344070.2896@woody.linux-foundation.org`, 2008-02-10, https://lore.kernel.org/all/alpine.LFD.1.00.0802092344070.2896%40woody.linux-foundation.org/)
- Limit: "I'm a _huge_ believer in "clean code", but the fact is, I'm an even bigger believer in "reality bites". I'd really like to see some numbers." (`alpine.LFD.0.98.0706221432080.3593@woody.linux-foundation.org`, 2007-06-22, https://lore.kernel.org/all/alpine.LFD.0.98.0706221432080.3593%40woody.linux-foundation.org/)
- "I do get the feeling that the problem came from us being much too clever with out min/max macros, and now this series is  doubling down instead of saying "it wasn't really worth it"." (`CAHk-=wh_+muDANgpjC6_31QMh4OnKEOgbZiD_MymHxAHRZRyqg@mail.gmail.com`, 2024-07-24, https://lore.kernel.org/all/CAHk-%3Dwh_%2BmuDANgpjC6_31QMh4OnKEOgbZiD_MymHxAHRZRyqg%40mail.gmail.com/)

**How well supported.** Strong. About 35 messages ("too clever", "too subtle", "KISS", "obviously correct"),
2000 to 2024.

---

## 5. Overdesign is the archetype of bad taste

**Principle.** Solve the problem in front of you with the obvious, straightforward change. Generic frameworks,
configurable layers, "can expose anything" interfaces and multi-level algorithms need a demonstrated need. He names
overdesign explicitly as "bad taste".

**What triggers it in a review.**
- A small concrete need answered with new infrastructure, plug-in points, registries or a generic container.
- Interfaces that return "random structures of random things" because the author has not decided what to expose.
- Two-level or adaptive algorithms where the simple one is good enough.
- Code moved from one subsystem into a shared library with complex, unexplained interfaces.

**His reasoning.** Overdesign multiplies concepts and interfaces without users; it also usually signals the author
does not know what they want. Shared/generic code is held to a much higher standard than private code because
everyone has to understand it.

**How serious.** Very high in tone (2009: "I'm _soo_ unhappy with you, and am insulting you"); in practice he
often sends the simple patch himself (2010) or refuses the pull (2024 bcachefs library code).

**Limits and exceptions.** Overengineering kept inside your own subsystem is tolerated ("As long as you made it some
kind of bcachefs-only thing, I don't mind"). Generality is welcome when there are many real users of one interface
(VFS, driver model).

**Outside the kernel.** Transfers fully: YAGNI applied to frameworks, config systems, plugin architectures, generic
repositories, "flexible" JSON blobs. Raise it hardest on shared libraries and public APIs.

**Evidence.**
- "Overdesigning is a SIN. It's the archetypal example of what I call "bad taste". I get really upset when a subsystem maintainer starts overdesigning things." (`alpine.LFD.2.00.0912150726510.14385@localhost.localdomain`, 2009-12-15, https://lore.kernel.org/all/alpine.LFD.2.00.0912150726510.14385%40localhost.localdomain/)
- "Let's not overdesign things. Just do something like the attached patch, which is the obvious and straightforward thing to do." and "Overdesigning is a disease. It's fundamentally wrong." (`AANLkTikoD1OPjVcyvAAJ0QO6dGJxv40Np6LgRQ7X4tMM@mail.gmail.com`, 2010-07-06, https://lore.kernel.org/all/AANLkTikoD1OPjVcyvAAJ0QO6dGJxv40Np6LgRQ7X4tMM%40mail.gmail.com/)
- "It's a huge sign of over-design and "I don't know what the hell I want to expose, so I'll make this generic thing that can expose anything, and then I start adding random fields"." (`CAHk-=wig0ZqWxgWtD9F1xZzE7jEmgLmXRWABhss0+er3ZRtb9g@mail.gmail.com`, 2020-08-17, https://lore.kernel.org/all/CAHk-%3Dwig0ZqWxgWtD9F1xZzE7jEmgLmXRWABhss0%2Ber3ZRtb9g%40mail.gmail.com/)
- Limit: "As long as you made it some kind of bcachefs-only thing, I don't mind. But now you're trying to push this garbage as some kind of generic library code that others would use, and that immediately means that I *do* mind insanely overengineered interfaces." (`CAHk-=wg3djFJMeN3L_zx3P-6eN978Y1JTssxy81RhAbxB==L8Q@mail.gmail.com`, 2024-03-13, https://lore.kernel.org/all/CAHk-%3Dwg3djFJMeN3L_zx3P-6eN978Y1JTssxy81RhAbxB%3D%3DL8Q%40mail.gmail.com/)
- "For that reason I think the mark-and-sweep thing is the right thing to do, but I think the two-level algorithm is just over-engineering and not worth it." (`Pine.LNX.4.44.0208081312330.8705-100000@home.transmeta.com`, 2002-08-08, https://lore.kernel.org/all/Pine.LNX.4.44.0208081312330.8705-100000%40home.transmeta.com/)

**How well supported.** Strong. About 18 messages, 2002 to 2024 (also 2002 aio "I hate overdesign", 2007 signalfd
"better to start off simple than to overdesign", 2010 SAT solver, 2018 signal "over-engineered", 2020 printk dict,
2024 mseal "COMPLETELY OVER-ENGINEERED").

---

## 6. Abstraction must earn its keep: no layers that hide what happens

**Principle.** An abstraction layer is good when it captures a real concept and costs nothing at run time or in
understanding; it is bad when it only renames a plain operation, hides its cost, or exists because "abstraction is
good". The test he gives: does the reader still know what this costs and what it does?

**What triggers it in a review.**
- `getFoo(x)` wrappers for `x->foo` or `x.a.b` with no added meaning.
- Layering that makes a cheap operation look possibly expensive (or the reverse).
- "Over-abstraction" of a struct into sub-objects with no users needing the split.
- Indirection stacks ("fifteen million different abstraction layers") between the caller and the real work.

**His reasoning.** People are "taught" abstraction is good; he thinks it makes costs invisible. Good abstraction is
*defined* by zero penalty and making the system clearer (his 2003 Alpha port example made x86 faster and made bad
decisions visible).

**How serious.** Medium. Mostly a request to rework or drop the wrapper; occasionally a refusal when it arrives as
churn across many files.

**Limits and exceptions.** He values abstraction when there is real variation or a concept to name: VFS,
`d_negative()`, per-architecture page-table helpers, and when "we'd expect things to change in the future" (2006).
He also likes good OO-style interfaces in C as long as the syntax is explicit (2007).

**Outside the kernel.** Transfers strongly to Java/C#/TypeScript enterprise layering, repository/service/manager
stacks, getters/setters, and "clean architecture" layers with one implementation each.

**Evidence.**
- "Adding these kinds of "abstraction layers" is something that people are taught is good, but I personally tend to think that it makes it less obvious at the code level what the "costs" are. Unless you know things intimately, you really have no way of judging whether "fpath_inode()" is something expensive or not." (`Pine.LNX.4.64.0610211702410.3962@g5.osdl.org`, 2006-10-22, https://lore.kernel.org/all/Pine.LNX.4.64.0610211702410.3962%40g5.osdl.org/)
- "Over-abstraction is a real problem - it makes the code less obvious, and if there is no real gain from it then over-abstracting things is a bad thing." (`a95don$m5p$1@penguin.transmeta.com`, 2002-04-12, https://lore.kernel.org/all/a95don%24m5p%241%40penguin.transmeta.com/)
- "Good abstraction has zero performance penalty, and can make the system much more pleasant to work with. And I claim that this is the DEFINITION of good abstraction." (`news:1057375190.35698@palladium.transmeta.com`, 2003-07-04, https://yarchive.net/comp/microkernels.html#9)
- "I also find it disgusting to have that [set_]task_type() "helper" abstraction layer. It doesn't actually help anything at all, and just makes it less clear what is going on." (`AANLkTinjVNddRYDUBnVZ67QDEPGrpj4dmW5BMwq2+ozP@mail.gmail.com`, 2010-09-20, https://lore.kernel.org/all/AANLkTinjVNddRYDUBnVZ67QDEPGrpj4dmW5BMwq2%2BozP%40mail.gmail.com/)
- Limit: "If this was something where we'd expect things to change in the future, maybe it would be worth it for _that_ reason." (`Pine.LNX.4.64.0610211702410.3962@g5.osdl.org`, 2006-10-22)

**How well supported.** Good. About 20 messages, 2002 to 2024.

---

## 7. A helper must help: when wrappers are good and when they are harmful

**Principle.** A helper or wrapper is justified when it names a concept, encodes a rule, removes real duplication,
or makes a complex expression readable in pieces. It is harmful when it is a trivial rename, has odd semantics few
people know, is badly named, or is placed in a global header where everyone must learn it. Local, single-use helpers
that split a complicated expression are fine; exported, specialised helpers with one user are not.

**What triggers it in a review.**
- New wrapper with a search-and-replace across many call sites and no behaviour change.
- Families of near-identical wrappers (`foo()`, `foo_once()`, `dentry_foo()`) whose differences nobody can state.
- A shared/global utility added for one caller, or with semantics that require reading the implementation.
- Conversely: a long, complex expression or conditional that a named local helper would explain.

**His reasoning.** Wrappers carry costs: "Churn. Harder to see what the code actually *does*", new mental rules,
bad names. Specialised global helpers add "cognitive load" because readers must look up what they do. A well-named
local helper does the opposite: each part reads on its own, and it can replace a comment.

**How serious.** Medium. Usually a request to drop or rename; in 2015 he pulled while objecting; in 2022 he
proposed deleting the helpers outright.

**Limits and exceptions.** This is the most nuanced principle, and the apparent conflict between 2022 ("Helper
functions with one single use-case shouldn't be helper fucntions") and 2025 ("Helper wrappers that are just used
once or twice can still be nice readability improvements") resolves by scope: 2022 is about exported library helpers
in shared headers, 2025 about a local wrapper in the file that uses it. He also asks for helpers to replace
`IS_ENABLED()` patterns (2022) and comments (2007).

**Outside the kernel.** Transfers directly: utility modules full of one-caller functions, "helpers.ts" dumping
grounds, thin wrappers around library calls, versus small private functions that name a step.

**Evidence.**
- "Dammit, if we add wrapper and "helper" functions, they should *help*, not confuse." (`CA+55aFwZ9X2XYzwkTvxANOMN8T9aynUCLCr5wKdahfdOX5fXig@mail.gmail.com`, 2015-02-21, https://lore.kernel.org/all/CA%2B55aFwZ9X2XYzwkTvxANOMN8T9aynUCLCr5wKdahfdOX5fXig%40mail.gmail.com/)
- "I'm not arguing against those kinds of wrappers that actually _clarify_ things. I'm arguing against random wrappers that don't, and that really fundamentally seem like they cannot possibly ever have any other valid value." and "And there are downsides to arbitrary random wrappers/helpers. Churn. Harder to see what the code actually *does*." (`CA+55aFx4e1NKXUXBc9rTHpxMJet9i9hQ9JC2KJAfb2dsyUM7Mw@mail.gmail.com`, 2015-02-22, https://lore.kernel.org/all/CA%2B55aFx4e1NKXUXBc9rTHpxMJet9i9hQ9JC2KJAfb2dsyUM7Mw%40mail.gmail.com/)
- "Helper functions with one single use-case shouldn't be helper fucntions. They should be inlines in the one single file that uses them. Trying to make up abstraction layers is not "helping", it's just making code harder to read, and trying to convince people to use specialized helpers just causes more cognitive load." (`CAHk-=wi4ARjYWqoStREpT9EEGWEVsEknRJX5z2OGoSDcKor8ZA@mail.gmail.com`, 2022-05-16, https://lore.kernel.org/all/CAHk-%3Dwi4ARjYWqoStREpT9EEGWEVsEknRJX5z2OGoSDcKor8ZA%40mail.gmail.com/)
- "Helper wrappers that are just used once or twice can still be nice readability improvements just because they make each part be easier to read on its own." (`CAHk-=wjMMSAaqTjBSfYenfuzE1bMjLj+2DLtLWJuGt07UGCH_Q@mail.gmail.com`, 2025-11-18, https://lore.kernel.org/all/CAHk-%3DwjMMSAaqTjBSfYenfuzE1bMjLj%2B2DLtLWJuGt07UGCH_Q%40mail.gmail.com/)
- "But again - keep that helper if you want it. Just don't put a badly implemented and badly named "helper" it in a global header file that _everybody_ has to look at." (`CAHk-=wgK7+TtDRbSAmcM5ihBDxF4eCg7zAXDkrNm7DOg+RtzyA@mail.gmail.com`, 2019-09-19, https://lore.kernel.org/all/CAHk-%3DwgK7%2BTtDRbSAmcM5ihBDxF4eCg7zAXDkrNm7DOg%2BRtzyA%40mail.gmail.com/)

**How well supported.** Good. About 25 messages, 2005 to 2025.

---

## 8. Readability first; complexity per line, not lines of code

**Principle.** Readability is the primary goal, and it usually also helps the compiler. Judge complexity of
statements and expressions, not line counts: dense lines, nested ternaries, multi-line expressions and compound
conditionals are the problem. Look at code "from 10,000 feet": overlong functions and `#ifdef`s show up as shape.

**What triggers it in a review.**
- Long `?:` chains, `if ((a = f()) == NULL)`, conditions joined with `||` across several lines.
- Expressions split over several lines to satisfy a line limit.
- Code made less readable to save an include, a few instructions, or a warning.

```c
/* he prefers */                       /* over */
if (PageTestandClearReferenced(page))  if (PageTestandClearReferenced(page) ||
	goto dispose_continue;             (!page->buffers && page_count(page) > 1) ||
if (!page->buffers && page_count(page) > 1)   TryLockPage(page))
	goto dispose_continue;                 goto dispose_continue;
```

**His reasoning.** Readers parse statements, not lines; a complex expression should be described by a named
inline function or broken into several statements. Lines-of-code is "a completely bogus metric".

**How serious.** Medium: rework requests, sometimes a refusal to apply header cleanups that hurt readability (2002).

**Limits and exceptions.** He accepts the occasional long line over a split one (see 9). He praised a patch that
added lines because it was conceptually simpler (2020). Readability is weighed against measured performance (4).

**Outside the kernel.** Fully transferable.

**Evidence.**
- "Basically, dense lines are bad. And ?: can make for code that ends up "too dense"." (`https://yarchive.net/comp/linux/code_complexity.html#1`, 2000-08-30)
- "make an inline function that has a descriptive name. It's still complex, but now the complexity is _described_, and not mixed in with potentially other complex actions." (same message)
- "Basically, lines-of-code is a completely bogus metric for _anything_. Including maintainability." (same message)
- "It might not _always_ be a win size and performance-wise, but it can be, and so readability should generally always be the #1 goal, because quite often it actually does help the compiler too." (`alpine.LFD.0.999.0707181050572.27353@woody.linux-foundation.org`, 2007-07-18, https://lore.kernel.org/all/alpine.LFD.0.999.0707181050572.27353%40woody.linux-foundation.org/)
- "See if the code flow makes sense from 10,000 feet - you can pick up overlong functions and various other dubious practices really clearly (#ifdef's in code etc)." (`alpine.LFD.1.10.0807161732510.2835@woody.linux-foundation.org`, 2008-07-17, https://lore.kernel.org/all/alpine.LFD.1.10.0807161732510.2835%40woody.linux-foundation.org/)
- "It's a lot more important to have readable code than it is to try to avoid a file include. And this patch makes code less readable, just look at it." (`Pine.LNX.4.44.0211171036360.22525-100000@home.transmeta.com`, 2002-11-17, https://lore.kernel.org/all/Pine.LNX.4.44.0211171036360.22525-100000%40home.transmeta.com/)

**How well supported.** Good. About 20 messages, 2000 to 2025.

---

## 9. Shallow nesting and short functions; indentation, not column count, is the signal

**Principle.** Deep indentation is the clearest sign a function needs splitting; more than about three or four
levels means redesign. Function length matters through its complexity. Line length is a weak proxy: do not split
lines to satisfy a limit; simplify the code instead.

**What triggers it in a review.**
- Five or more indentation levels, especially new error handling nested inside old branches.
- A giant `switch`-based function where each case could be a helper (his sparse `linearize_statement()` split).
- 250-line functions with `#ifdef`s inside.
- Lines broken mid-expression to fit 80 columns, creating "false indentation".

**His reasoning.** Deep nesting is unreadable "even if you *can* fit it on a single line"; 8-wide tabs exist to make
this painful early. Splitting into named functions also helps debugging (stack traces name the case).

**How serious.** Medium: "violates my personal coding standards" and requests to split; not usually a hard reject.

**Limits and exceptions.** A long but conceptually simple function (one big flat switch) is acceptable (coding-style
says so; consistent with his mail). He rejects the 80-column rule as a hard limit (2009, 2012, 2016, 2020): occasional
long lines are better than split ones; consistently long lines signal a problem. In 2024 he corrected his own
suggestion of `scoped_guard()` because it added an indentation level.

**Outside the kernel.** Transfers: nesting depth and early returns/guard clauses, extracting per-case functions.
Do not enforce line-length linters at the expense of clarity.

**Evidence.**
- "if you have more than about 4 levels of indentation, you'd better redesign your function is my opinion." (`oldlinux:mail-archive/linux-devel/Volume1/digest3XX.tar.gz#2`, 1993-12-28, https://github.com/oldlinux-web/oldlinux-files/blob/master/mail-archive/linux-devel/Volume1/digest3XX.tar.gz)
- "deep indentation is unreadable even if you *can* fit it on a single line." and, about the coding-style passage quoted to him, "And yes, I also wrote the other quote:" (`alpine.LFD.0.98.0706151319430.14121@woody.linux-foundation.org`, 2007-06-15, https://lore.kernel.org/all/alpine.LFD.0.98.0706151319430.14121%40woody.linux-foundation.org/). That passage, in `coding-style.rst`: "The answer to that is that if you need more than 3 levels of indentation, you're screwed anyway, and should fix your program." (`https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/plain/Documentation/process/coding-style.rst`)
- "It really *does* end up encouraging people to split things up and write nested cases as separate functions etc, because it simply becomes so obvious when things are going south.." (`alpine.LFD.0.999.0710172102020.26902@woody.linux-foundation.org`, 2007-10-18, https://lore.kernel.org/all/alpine.LFD.0.999.0710172102020.26902%40woody.linux-foundation.org/)
- "80 columns do not matter. What matters is: - indentation - complex expressions and statements" (`alpine.LFD.2.01.0911120912160.31845@localhost.localdomain`, 2009-11-12, https://lore.kernel.org/all/alpine.LFD.2.01.0911120912160.31845%40localhost.localdomain/)
- "Also, that whole function could damn well be split into smaller pieces, which would make it much more readable than that horrible 250+ line piece of crap monster-function with #ifdef's inside the code." (`alpine.LFD.2.01.0907081103560.3352@localhost.localdomain`, 2009-07-08, https://lore.kernel.org/all/alpine.LFD.2.01.0907081103560.3352%40localhost.localdomain/)
- "But _splitting_ lines isn't the answer. Making code simpler is, but somehow the 80-column warning never causes that to happen - instead people just split." (`alpine.LFD.2.00.0904081341090.4583@localhost.localdomain`, 2009-04-08, https://lore.kernel.org/all/alpine.LFD.2.00.0904081341090.4583%40localhost.localdomain/)
- "So not only do we avoid a level of indentation, but this actually makes things much easier to follow in gdb" (`alpine.LFD.2.02.1108271429000.18733@i5.linux-foundation.org`, 2011-08-27, https://lore.kernel.org/all/alpine.LFD.2.02.1108271429000.18733%40i5.linux-foundation.org/)

**How well supported.** Strong. About 30 messages, 1993 to 2024. Explicit function-length numbers ("one or two
screenfuls", five to ten local variables) are only in `coding-style.rst`; I found no mail where he states them.

---

## 10. Names describe the concept, are written out, and stay consistent

**Principle.** Name things for what they mean to the caller, not for how they are implemented. Global names must be
descriptive and carry context; local names should not repeat context the file already gives. Consistency with
existing names beats a locally "better" name. Do not rename a good name to a worse one. Avoid letter jumbles, cute
names, Hungarian notation, and typedefs that hide that something is a pointer or a struct.

**What triggers it in a review.**
- Names that describe a mechanism (`RELEASED`, `safe`, `mcsafe`) rather than the condition the caller cares about.
- Abbreviations (`pcps`, `rdllink` vs `rdllist`), cute metaphors, redundant prefixes on locals (`mmn_`).
- Renames driven by "use the generic function" that make a clear name less clear; inconsistent sibling names.
- `typedef struct foo *foo_t;`; `typedef` for a struct that never changes by configuration.
- Misleading names (a flag whose absence does not do what its name says).

**His reasoning.** Bad names "create bugs" (2005 semaphore rant); a reader should not need to look up the definition.
A name that is too trivial to write out signals the function should not exist.

**How serious.** Can be a hard refusal ("I will not be taking a pull that makes a good name worse", 2023); usually
a rename request or a merge with a complaint.

**Limits and exceptions.** He accepts maintainer preference on cosmetic renames he dislikes (2022 VFIO: pulled).
Typedefs are acceptable for types that really vary by configuration or are opaque.

**Outside the kernel.** Fully transferable; the typedef point maps to type aliases hiding nullability/pointers or
`Ptr` types, and to opaque aliases that do not carry meaning.

**Evidence.**
- "Naming - like comments - shouldn't be about what some implementation is, but about the concept." (`CAHk-=wh1SPyuGkTkQESsacwKTpjWd=_-KwoCK5o=SuC3yMdf7A@mail.gmail.com`, 2020-05-01, https://lore.kernel.org/all/CAHk-%3Dwh1SPyuGkTkQESsacwKTpjWd%3D_-KwoCK5o%3DSuC3yMdf7A%40mail.gmail.com/)
- "name things for the _concept_, not for some odd implementation issue" (`AANLkTinGgZC7eHW_Q-aR5Vmur4yjv_kKSJ8z3MX60e-r@mail.gmail.com`, 2010-10-01, https://lore.kernel.org/all/AANLkTinGgZC7eHW_Q-aR5Vmur4yjv_kKSJ8z3MX60e-r%40mail.gmail.com/)
- "Write it out. If a function is so trivial that you can't be bothered to write out what the name means, that function shouldn't exist at all. Conversely, if it's worth doing, it's worth writing out a name." (`Pine.LNX.4.64.0511230834160.13959@g5.osdl.org`, 2005-11-23, https://lore.kernel.org/all/Pine.LNX.4.64.0511230834160.13959%40g5.osdl.org/)
- "Yes, global function names need to be unique, and if they aren't really core, they want some prefix that explains the context, because global functions are called from _outside_ the context that explains them." (`CAHk-=wgR7OSE9Bn2+MbOYDbiu7n1RQaQhdc6gkEywXL9rMFcpw@mail.gmail.com`, 2019-12-18, https://lore.kernel.org/all/CAHk-%3DwgR7OSE9Bn2%2BMbOYDbiu7n1RQaQhdc6gkEywXL9rMFcpw%40mail.gmail.com/)
- "Naming matters, and "use a generic function" is not an excuse for having bad names." (`CAHk-=whqdgepR+o844ePrRnvPh7-L9MYdOhbwmDfiTHSE8Oo9w@mail.gmail.com`, 2023-05-04, https://lore.kernel.org/all/CAHk-%3DwhqdgepR%2Bo844ePrRnvPh7-L9MYdOhbwmDfiTHSE8Oo9w%40mail.gmail.com/)
- "I don't _care_ whether people think it's a bad name - much worse than a bad name is to use a name that is not consistent." (`alpine.LFD.2.00.1005081455450.3711@i5.linux-foundation.org`, 2010-05-08, https://lore.kernel.org/all/alpine.LFD.2.00.1005081455450.3711%40i5.linux-foundation.org/)
- ""rdllink" isn't exactly obvious _and_ it's visually very close to "rdllist". They are related, yes, so you want them to be similar, but when it's a letter jumble, similarity ends up really being something you have to think about." (`CAHk-=wjjhgJ7J3Td5MzLE8L0ZXLqSd-bbMjf_5zy3P4kXa3xeA@mail.gmail.com`, 2026-04-24, https://lore.kernel.org/all/CAHk-%3DwjjhgJ7J3Td5MzLE8L0ZXLqSd-bbMjf_5zy3P4kXa3xeA%40mail.gmail.com/)
- "Quite frankly, I personally do hate typedefs that end up being pointers, and used as pointers, without showing that in the source code." (`alpine.LFD.2.00.0809300939450.3389@nehalem.linux-foundation.org`, 2008-09-30, https://lore.kernel.org/all/alpine.LFD.2.00.0809300939450.3389%40nehalem.linux-foundation.org/)

**How well supported.** Strong. About 35 messages, 2002 to 2026.

---

## 11. Share code when the concept is shared; duplicate when it is not

**Principle.** Merge copies that are the same concept (several versions of one macro, each driver writing its own
wrapper for a common helper). Do not force different things through one "common" routine or a shared middle layer:
simple duplicated code beats a complex shared interface, and separate functions for genuinely different cases beat
one routine full of mode checks.

**What triggers it in a review.**
- A new "common" layer joining two features with different rules, so changes to one now affect the other.
- A single function with three modes and different early-exit rules per mode (the 2020 wait-loop bug).
- A complex sharing interface introduced to remove a few lines of simple duplication.
- Conversely: N near-identical copies of a macro or wrapper that differ in one token.

**His reasoning.** Sharing ties "two conceptually totally separate things together" and makes the middle layer
serve conflicting needs; bugs come from the odd shape that shared code takes to accommodate all cases.

**How serious.** Medium to high: in 2010 his reaction to building seccomp on utrace "was and is just totally
negative"; in 2020 he fixed the bug minimally and asked someone to split the routine.

**Limits and exceptions.** He wants common code where one interface must face many users (VFS, driver layer), and
he wants obvious copy-paste merged (2009, 2021). The deciding question is whether the parts are the same concept, not
whether lines look alike.

**Outside the kernel.** Transfers fully; a good antidote to DRY applied mechanically.

**Evidence.**
- "it's a lot better to have the same (simple) code duplicated five times than it is to make a (much more complex) interface to have things shared." (`Pine.LNX.4.58.0501271312440.2362@ppc970.osdl.org`, 2005-01-27, https://lore.kernel.org/all/Pine.LNX.4.58.0501271312440.2362%40ppc970.osdl.org/)
- "But going the other way: trying to share code when the interfaces are fundamentally _different_ is generally not at all such a great idea. It ends up tying two conceptually totally separate things together, and suddenly people who work on feature X aneed to modify infrastructure that affects feature Y" (`alpine.LFD.2.00.1001221614520.13231@localhost.localdomain`, 2010-01-23, https://lore.kernel.org/all/alpine.LFD.2.00.1001221614520.13231%40localhost.localdomain/)
- "I actually think it would be a lot more readable if it was three different cases instead of trying to be one "common" routine." (`CAHk-=wjJKicPgmvf7atx=h6Li7ez9nFrpJdgTSRm5aUEnuVH6w@mail.gmail.com`, 2020-06-29, https://lore.kernel.org/all/CAHk-%3DwjJKicPgmvf7atx%3Dh6Li7ez9nFrpJdgTSRm5aUEnuVH6w%40mail.gmail.com/)
- Other side: "Having separate versions for "__[sync_|local_|]cmpxchg()" is disgusting. I bet you can do it with a single macro, and just pass in the LOCK_PREFIX (or empty, or "lock;") to that as needed. Rather than duplicating it three times." (`alpine.LFD.2.01.0910051210280.3432@localhost.localdomain`, 2009-10-05, https://lore.kernel.org/all/alpine.LFD.2.01.0910051210280.3432%40localhost.localdomain/)
- Other side: "If multiple chips just want a basic sw hamming helper, then they should have one. Not have to be forced to each write their own pointless wrapper like this." (`CAHk-=wh_ZHF685Fni8V9is17mj=pFisUaZ_0=gq6nbK+ZcyQmg@mail.gmail.com`, 2021-05-26, https://lore.kernel.org/all/CAHk-%3Dwh_ZHF685Fni8V9is17mj%3DpFisUaZ_0%3Dgq6nbK%2BZcyQmg%40mail.gmail.com/)

**How well supported.** Moderate. About 12 messages, 2005 to 2025. Both directions are clearly stated; the
dividing rule (same concept vs same text) is my synthesis from them.

---

## 12. Comments: why and what at a high level, never a narration of how

**Principle.** Make the code readable without comments first; if a block needs a comment to explain *what* it does,
prefer a well-named helper. Comments should explain the higher-level what and why, especially why something unusual
or unsafe is OK, and be aimed at the reader who will get it wrong. Put comments above code, not at the end of lines.
Wrong or stale comments are actively harmful.

**What triggers it in a review.**
- Line-by-line narration, end-of-line comments, box comments.
- A comment that explains what a messy block does instead of fixing the block.
- An unusual or "unsafe" choice (skipping a lock, a barrier, a `WRITE_ONCE`, an odd return-value ignore) with no
  comment saying why it is safe.
- A comment addressed to people already doing the safe thing, while the risky callers get no warning.
- Comments that contradict the code (barrier comments after the barrier semantics changed).

**His reasoning.** Comments about code details go stale and are "likely bogus"; end-of-line comments turn to mush
when code changes. What does not go stale is the reason; he repeatedly cannot remember why something is a "disgusting
mess" because nobody wrote it down.

**How serious.** Medium. He asks for "a big comment" often; refused one patch where a comment showed the author
misunderstood the problem (2020).

**Limits and exceptions.** End-of-line comments are acceptable in assembly (2001). He sometimes asks for a comment as
well as the helper (2022). `coding-style.rst` says comments should say WHAT not HOW; his mail stresses WHY and
"higher level", which is compatible.

**Outside the kernel.** Fully transferable, including docstrings that restate the signature.

**Evidence.**
- "If people feel the code is subtle enough that a comment is in order to explain *what* something does, I would rather introduce helper functions than add comments. I'm not a big believer in comments in the middle of code to explain the code, but I *am* a big believer in trying to make the code easy to read without them." (`alpine.LFD.0.999.0711051233270.15101@woody.linux-foundation.org`, 2007-11-05, https://lore.kernel.org/all/alpine.LFD.0.999.0711051233270.15101%40woody.linux-foundation.org/)
- "(I don't dislike comments per se, but I'd *much* rather have the comments explain what is going on at a higher level. Comments that talk about the details of the code itself is likely bogus)." (same message)
- "Write comments before your function. If your function is so long and complicated that you think it needs comments after the lines, then you should have split it up." (`https://yarchive.net/comp/linux/coding_style.html#2`, 2001-01-19)
- "This comment is useless - because it's aimed at the wrong people." and "The case I worry about is the people who do NOT say "break COW". Not because they are smart and know what they are doing, but because they don't think about the issue." (`CAHk-=whUVHA-=4mwGaUA42teESc2mX1nwZjbbOMQsvPaoYxh3w@mail.gmail.com`, 2020-08-10, https://lore.kernel.org/all/CAHk-%3DwhUVHA-%3D4mwGaUA42teESc2mX1nwZjbbOMQsvPaoYxh3w%40mail.gmail.com/)
- "I would still encourage that *comment* about it, but I think we really should strive for code that makes sense even without a comment." (`CAHk-=wizUgMbZKnOjvyeZT5E+WZM0sV+zS5Qxt84wp=BsRk3eQ@mail.gmail.com`, 2022-08-03, https://lore.kernel.org/all/CAHk-%3DwizUgMbZKnOjvyeZT5E%2BWZM0sV%2BzS5Qxt84wp%3DBsRk3eQ%40mail.gmail.com/)
- "I may have gotten that answered too, but there's no comment in the code about why it's such a disgusting mess, so I've long since forgotten _why_ it's such a disgusting mess." (`CA+55aFwjaY6Nv7x0d8BQaSddZwAK7fukrYOHWEG_v2-1JZi5Qg@mail.gmail.com`, 2018-05-02, https://lore.kernel.org/all/CA%2B55aFwjaY6Nv7x0d8BQaSddZwAK7fukrYOHWEG_v2-1JZi5Qg%40mail.gmail.com/)
- "So the comment should probably say that it needs to be reinited after all the existing completion users have actually woken up, so that it explains why the reinit isn't just done by complete_all()." (`CA+55aFz=Yg=eOgJ9cP3GzF9eJsAyZF+XkBBe2EBZYrpvT5oJ5Q@mail.gmail.com`, 2017-08-16, https://lore.kernel.org/all/CA%2B55aFz%3DYg%3DeOgJ9cP3GzF9eJsAyZF%2BXkBBe2EBZYrpvT5oJ5Q%40mail.gmail.com/)
- Mocked: "Now, box comments are stupid anyway, but they become truly mind-bogglingly pointless when they are then edited like this." (`CA+55aFwBvXVQavgwDKVV3epFhd4MTaQvDktpDahkPhxweXnMmQ@mail.gmail.com`, 2017-12-08, https://lore.kernel.org/all/CA%2B55aFwBvXVQavgwDKVV3epFhd4MTaQvDktpDahkPhxweXnMmQ%40mail.gmail.com/)

**How well supported.** Good. About 30 messages, 2001 to 2026.

---

## 13. No `#ifdef`s in code: one problem, abstracted, not two

**Principle.** Conditional compilation inside function bodies means the author treated one problem as two. Put the
variation behind a header-level interface (inline function or macro with a no-op/degenerate variant), so the main code
reads as one path; choose the abstraction "at a higher level" with a conceptual meaning. Syntax tricks that only
disguise the `#ifdef` do not count.

**What triggers it in a review.**
- `#ifdef CONFIG_X` / `#if VERSION` blocks in the middle of a function; feature flags checked inline in many places.
- A "fix" that moves the condition into a differently spelled macro without abstracting it.
- `IS_ENABLED()` (or runtime feature-flag) patterns repeated at call sites instead of a helper that names the intent.

**His reasoning.** `#ifdef`s "destroy the linearity of the code"; pushing them out forces better interfaces
("you have to choose your abstraction interfaces more carefully"). The single-CPU case should be the SMP case with one
CPU, not separate code.

**How serious.** Was a hard reject in 2001 ("no way I will ever apply this particular patch"). Since about 2010 more
often a request or a merge with a complaint.

**Limits and exceptions.** A one-off, local architecture special case may carry an `#ifdef` right where it is needed,
with a comment (2019). He weighs remedies: a "disgusting" macro trick to remove `#ifdef`s may not be worth it (2009).
`IS_ENABLED()` in normal control flow is better than `#ifdef` (2022-01), but a named helper is better still
(2022-08). Compatibility code for old versions belongs in the old tree, not the new one (2000).

**Outside the kernel.** Transfers to build tags, platform `#if` in C/C++/Rust `cfg`, feature flags and `if
(config.x)` scattered through business logic, and version checks: put the variation behind an interface.

**Evidence.**
- "I dislike #ifdef code.  Avoid it whenever possible.  #ifdefs become ugly, and destroy the linearity of the code (== hard to read)." (`oldlinux:mail-archive/linux-devel/Volume1/digest5XX.tar.gz#4`, 1994-03-19, https://github.com/oldlinux-web/oldlinux-files/blob/master/mail-archive/linux-devel/Volume1/digest5XX.tar.gz)
- "Note that there is no way I will ever apply this particular patch for a very simple reason: #ifdef's in code." and "I hate code that has #ifdef's. It's a major design mistake, and shows that the person who coded it didn't think of it as _one_ problem, but as two." (`https://yarchive.net/comp/linux/ifdefs.html#1`, 2001-08-08)
- "Having the #ifdef's outside the code tends to have two advantages: - it makes the code much more readable, and doesn't split things up. - you have to choose your abstraction interfaces more carefully, which in turn tends to make for better code." (`https://yarchive.net/comp/linux/ifdefs.html#2`, 2001-08-08)
- "#ifdef's in code is not about syntax, it's about abstraction. This is still the exact same thing as having an #ifdef around it, and in many ways it is *worse*, because now it's just made to look somewhat different with a particularly ugly #ifdef." (`alpine.LFD.1.00.0801180816120.2957@woody.linux-foundation.org`, 2008-01-18, https://lore.kernel.org/all/alpine.LFD.1.00.0801180816120.2957%40woody.linux-foundation.org/)
- "Please don't put #ifdef's inside code. It makes things really ugly and hard to read." (`CA+55aFy9uYifEQ20-tQXvFCYSqb2VG74XhM6ZofHJW_VuqWdZQ@mail.gmail.com`, 2012-10-18, https://lore.kernel.org/all/CA%2B55aFy9uYifEQ20-tQXvFCYSqb2VG74XhM6ZofHJW_VuqWdZQ%40mail.gmail.com/)
- Limit: "Would it need a #ifdef CONFIG_X86_32 around it because it's not needed on x86-64? Sure. But that #ifdef would be right there, and the comment that explains why the pt_regs need to be moved would also make it very obvious why it is only needed for x86-32." (`CAHk-=wiA-WbrFrDs-kOfJZMXy4zMo9-SZfk=7B-GfmBJ866naw@mail.gmail.com`, 2019-05-03)
- Limit: "Ugly? Yes. Less ugly than having variations of that #ifdef repeated many times? I dunno." (`alpine.LFD.2.01.0908161101470.3162@localhost.localdomain`, 2009-08-16, https://lore.kernel.org/all/alpine.LFD.2.01.0908161101470.3162%40localhost.localdomain/)

**How well supported.** Strong. About 40 messages, 1994 to 2024; one of his most consistent positions.

---

## 14. No code "for the future": real users first, delete what is unused

**Principle.** Do not add infrastructure, options or interfaces for hypothetical future users, and do not keep unused
code because it "might" be needed. New interfaces need real users (not examples); unused code and legacy paths
that complicate things should go.

**What triggers it in a review.**
- New API/syscall/flag/config with no in-tree or real-world user, or only a demo user.
- "Future-proofing" changes to code paths that have no future.
- Dummy definitions or stubs kept so that hypothetical code can compile; `#if 0` blocks with no explanation.
- Generic variants added "just because we can".

**His reasoning.** Interfaces with one or two minor users become "nasty long-term maintenance issues"; "what if" is
not an argument; dead legacy complicates the live code.

**How serious.** High for user-visible interfaces (he declines to merge without users); medium for internal dead code
(he happily applies removals: "I love seeing old nasty stuff like this go away", 2022).

**Limits and exceptions.** Infrastructure merged just ahead of its users is acceptable when it is safe and small
(2015 strscpy, "purely preparatory"). Some `#if 0` code is useful as commentary about a rejected implementation
(1999), but then it needs a comment (2003). Expected change can justify an abstraction (6).

**Outside the kernel.** Transfers fully: speculative extension points, unused feature flags, commented-out code,
"v2" APIs with no client.

**Evidence.**
- "Even if there might be some unlikely future reason why it might be revived some day, let's not use "what if" as an argument to keep unused code around." (`CA+55aFzX9CeRr3HZtVN5XKK2Ema5TjXo4FCgD8ukWz6Waz=pZw@mail.gmail.com`, 2018-05-05, https://lore.kernel.org/all/CA%2B55aFzX9CeRr3HZtVN5XKK2Ema5TjXo4FCgD8ukWz6Waz%3DpZw%40mail.gmail.com/)
- "So 32-bit x86 is dead, dead, dead. There's absolutely no future to it. We're not adding new stuff to "future-proof" it." (`CA+55aFz+OfvtXLxg4CA4C6GPGh8F_aDuG6nnFFCCBpjTPLP1zA@mail.gmail.com`, 2014-03-11, https://lore.kernel.org/all/CA%2B55aFz%2BOfvtXLxg4CA4C6GPGh8F_aDuG6nnFFCCBpjTPLP1zA%40mail.gmail.com/)
- "And if you actually have a real user, not just an example, that is worthy and shows why such a driver in user space is actually a good thing, _then_ we can push that." (`Pine.LNX.4.64.0612131252300.5718@woody.osdl.org`, 2006-12-13, https://lore.kernel.org/all/Pine.LNX.4.64.0612131252300.5718%40woody.osdl.org/)
- "We've had a fair number of kernel interfaces that ended up not being used all that much, but had one or two minor users and ended up being nasty long-term maintenance issues.. I don't want this to become yet another such one." (`CAHk-=wjrrOgznCy3yUmcmQY1z_7vXVr6GbvKiy8cLvWbxpmzcw@mail.gmail.com`, 2020-01-15, https://lore.kernel.org/all/CAHk-%3DwjrrOgznCy3yUmcmQY1z_7vXVr6GbvKiy8cLvWbxpmzcw%40mail.gmail.com/)
- "there is no reason to think that some random MIPS-only future code is a good enough reason to re-introduce these things" (`CA+55aFx==PGGLX9YXv1GOeTja4W0PSW8U4i8zkmtiZwqmFwHFw@mail.gmail.com`, 2011-11-22, https://lore.kernel.org/all/CA%2B55aFx%3D%3DPGGLX9YXv1GOeTja4W0PSW8U4i8zkmtiZwqmFwHFw%40mail.gmail.com/)
- Limit: "Some of the #if 0 code should certainly be removed. Some of it is useful as a kind of commentary - sometimes code is removed not because it doesn't make sense, but because the implementation wasn't quite good enough." (`Pine.LNX.3.95.990107112314.5025B-100000@penguin.transmeta.com`, 1999-01-07, https://lore.kernel.org/all/Pine.LNX.3.95.990107112314.5025B-100000%40penguin.transmeta.com/)
- "Ok. In that case, can we remove the '#if 0' blocks entirely, or at least add a big comment on why they are there but disabled?" (`Pine.LNX.4.44.0309281038270.6307-100000@home.osdl.org`, 2003-09-28, https://lore.kernel.org/all/Pine.LNX.4.44.0309281038270.6307-100000%40home.osdl.org/)

**How well supported.** Good for interfaces (about 15 messages, 2006 to 2024); thinner for dead code inside a
function (about 6 messages). "Dead code" phrasing is rare in his mail; he talks about "unused", "no users", "legacy".

---

## 15. A cleanup must improve something; churn and warning-driven edits make code worse

**Principle.** A patch labelled "cleanup" has to make the code demonstrably better (simpler, clearer, smaller in
concepts) without breaking anything. Mechanical renames, wrapper conversions across hundreds of sites, header
shuffles and edits made only to silence a tool are churn: they cost review, conflicts and bugs.

**What triggers it in a review.**
- Big diffstat, no behavioural or conceptual improvement; "use new helper" across 150 files.
- A cleanup that is less readable than the original, or that changes semantics while claiming not to.
- Code contorted to silence a compiler or static-analysis warning.
- Cleanups in fragile areas without testing (compat paths).

**His reasoning.** Change for its own sake has pain and no gain; cleanups have repeatedly introduced subtle bugs; a
warning-free contortion is "actively worse".

**How serious.** High once burned: he has said he will be "a *lot* less inclined" to take a developer's cleanups
(2015) and will stop applying a class of cleanups that break builds (2002). Revert of "cleanups" that are not.

**Limits and exceptions.** Pure cleanups with no technical impact are welcome when they really clean (2007), and
"looks cleaner" matters for maintenance because unexplained behaviour breeds hacks (2001). Large mechanical renames
are fine when trivially verifiable and they enable real follow-up (his own 2010 module-loader patch).

**Outside the kernel.** Transfers fully: refactor PRs, mass lint fixes, codemods, "modernisation" PRs.

**Evidence.**
- "I don't mind cleanups, but this is "churn". Change for its own sake. If it doesn't lead to any _improvement_, it's pointless." (`alpine.LFD.1.10.0804231914270.2779@woody.linux-foundation.org`, 2008-04-24, https://lore.kernel.org/all/alpine.LFD.1.10.0804231914270.2779%40woody.linux-foundation.org/)
- "cleanup just for the sake of cleanup always needs to take pain into account. If you cannot make each small step "worth it", then just don't do it. If the "cleanup" just adds another file and doesn't actually _help_ anything that you can point to, it's not a cleanup, it's just an exercise in wanking." (`Pine.LNX.4.58.0411281710490.22796@ppc970.osdl.org`, 2004-11-29, https://lore.kernel.org/all/Pine.LNX.4.58.0411281710490.22796%40ppc970.osdl.org/)
- "Here's a hint: if some stupid change requires you to mindlessly do 150 changes using a wrapper helper, it's churn." (`CA+55aFwrpd+fz3jxK3d6dckFcApc=aCZOrsKogxRYZozwUdHrg@mail.gmail.com`, 2017-09-07, https://lore.kernel.org/all/CA%2B55aFwrpd%2Bfz3jxK3d6dckFcApc%3DaCZOrsKogxRYZozwUdHrg%40mail.gmail.com/)
- "These "cleanups" have been buggy as hell, and test coverage for the compat case is clearly lacking." (`CA+55aFyhOgoZRGemkda5igTdqyOSrb-hP1nAmCcfMbtFUmq5HQ@mail.gmail.com`, 2015-08-13, https://lore.kernel.org/all/CA%2B55aFyhOgoZRGemkda5igTdqyOSrb-hP1nAmCcfMbtFUmq5HQ%40mail.gmail.com/)
- "I _hate_ those idiotic warnings, and in this case the "warning-free" code is actively worse than the original." (`alpine.LFD.2.01.0910290826350.31845@localhost.localdomain`, 2009-10-29, https://lore.kernel.org/all/alpine.LFD.2.01.0910290826350.31845%40localhost.localdomain/)
- Limit: ""Looks cleaner" is very important for me for maintenance reasons - having behaviour that you cannot explain tends to result in more and more ad-hoc hacks over time, and it just tends to get worse and worse." (`Pine.LNX.4.33.0109170942161.8900-100000@penguin.transmeta.com`, 2001-09-17, https://lore.kernel.org/all/Pine.LNX.4.33.0109170942161.8900-100000%40penguin.transmeta.com/)
- Limit: "I have no problem at all with the first four patches in the series, because those are cleanups that have no technical impact apart from that "cleanup-ness"." (`alpine.LFD.0.98.0706221432080.3593@woody.linux-foundation.org`, 2007-06-22)

**How well supported.** Strong. About 25 messages, 2001 to 2025.

---

## 16. What a pretty patch looks like, and why he says so

**Principle (for the reviewer's positive vocabulary).** His praise is specific and predicts his standards. A patch he
calls nice usually: removes special cases; removes more code than it adds *while fixing something*; makes a
component independent of the rest ("no impact what-so-ever on the rest"); is conceptually simpler even if it adds
lines; is set up so the compiler catches unconverted users; is "*practically* smaller" even if conceptually bigger.

**What triggers it in a review.** Say so when a patch does these things; it tells the author what to keep doing.
Do not praise line-count reduction by itself (he calls lines-of-code a bogus metric, 8).

**How serious.** Praise often comes with an immediate apply, even late in a cycle (2012: "Even at this stage of
-rc"), and with "Ack. Lovely." on removals.

**Outside the kernel.** Transfers fully.

**Evidence.**
- "Lovely. Simple and clean." (`CAHk-=whfh4Q_UiOo9uYdXVsggbLhCr4pRsB4VAWMhgZ2X9d_sw@mail.gmail.com`, 2020-04-04, https://lore.kernel.org/all/CAHk-%3Dwhfh4Q_UiOo9uYdXVsggbLhCr4pRsB4VAWMhgZ2X9d_sw%40mail.gmail.com/)
- "It removes more lines than it adds while fixing things, by removing the helper function that isn't good at anoymous unions, and using another one that does this all right.." (`CA+55aFzs_O780hEowt9vg69-Kxfwzn5j1eL2F2Tzw4C56koeRg@mail.gmail.com`, 2014-03-31, https://lore.kernel.org/all/CA%2B55aFzs_O780hEowt9vg69-Kxfwzn5j1eL2F2Tzw4C56koeRg%40mail.gmail.com/)
- "Now, I like this because it gets rid of the horrible PAGE_NUMA special cases, but it really seems to simplify things in general." (`CA+55aFzisEwtcBA93Xo74RM-6X9V=_go=YhN7eFJOHLeHs3HEQ@mail.gmail.com`, 2014-10-01, https://lore.kernel.org/all/CA%2B55aFzisEwtcBA93Xo74RM-6X9V%3D_go%3DYhN7eFJOHLeHs3HEQ%40mail.gmail.com/)
- "It adds more lines than it removes, but a lot of it is comments, and while it's somewhat subtle, I think it's actually conceptually simpler than what we had before." (`CAHk-=wiqzsK_c_jUXFnSXeumsRQpYEwv0Xbi3MiGKLcVxS2_kg@mail.gmail.com`, 2020-07-23, https://lore.kernel.org/all/CAHk-%3DwiqzsK_c_jUXFnSXeumsRQpYEwv0Xbi3MiGKLcVxS2_kg%40mail.gmail.com/)
- "And as far as I'm concerned, the nice part about not having any locking there is that now the spinning has no impact what-so-ever on the rest of the mutex logic." (`alpine.LFD.2.00.0901080849550.3283@localhost.localdomain`, 2009-01-08, https://lore.kernel.org/all/alpine.LFD.2.00.0901080849550.3283%40localhost.localdomain/)
- "patch#2 (which is the big one) was set up so that the compiler would not even compile code that wasn't properly converted, so it should all be good." (`Pine.LNX.4.64.0703210955370.6730@woody.linux-foundation.org`, 2007-03-21, https://lore.kernel.org/all/Pine.LNX.4.64.0703210955370.6730%40woody.linux-foundation.org/)
- "Sure, it might be a *conceptually* bigger change, but since it's both prettier and *practically* smaller, I do like it more." (`CA+55aFwt9Wd9cwk3B4U0+B+EyBJm8oG0r0ADQvEa0D4HmrMWQQ@mail.gmail.com`, 2012-09-18, https://lore.kernel.org/all/CA%2B55aFwt9Wd9cwk3B4U0%2BB%2BEyBJm8oG0r0ADQvEa0D4HmrMWQQ%40mail.gmail.com/)
- On taste itself: "But there is that occasional "inspiration" part, that "good taste" thing that is about more than just solving some problem - solving it cleanly and nicely and yes, even beautifully." (`https://www.tag1.com/blog/interview-linus-torvalds-linux-and-git/`, 2021-04-28)

**How well supported.** Good. About 35 praise messages, 2006 to 2026 ("removes more lines than it adds" alone ~12).

---

## Changes of position over time

| Topic | Earlier | Later / current |
|---|---|---|
| Tone of taste reviews | 2001 to 2018: "physically disgusting", "SIN", "piece of crap"; hard rejects for `#ifdef`s | After 2018 the reasoning is unchanged and still blunt ("horrendous interfaces", "disgusting"), but more often "I have pulled this, but…" plus a concrete suggestion. Hard refusals remain for interfaces and names (2023, 2024). |
| `#ifdef` remedies | 1994 to 2012: header-level inline/macro stubs | 2022: `IS_ENABLED()` in control flow is better than `#ifdef`, but a named helper that states intent is preferred to repeated `IS_ENABLED()` blocks. Same principle, newer tool. |
| Single-use helpers | 2007: prefer helper functions to comments; 2022: single-use exported helpers "shouldn't be helper fucntions" | 2025: single/double-use local wrappers are "nice readability improvements". Read as scope-dependent, not a reversal. Treat 2025 as current for local helpers. |
| 80 columns | Never in his original style (he says so, 2009) | Consistent: soft limit at most; 2020 "Excessive line breaks are BAD". 2025 (`CAHk-=wi2=v4cV6=jaxjA6ymaadxiWRRNdfzPa==EY6RQxWni3w@mail.gmail.com`, 2025-08-28) still calls fitting in 80 columns not a requirement but still good taste. |
| Scoped constructs | n/a | 2023 onward he designs and promotes `cleanup.h` guards, but rejects added nesting from `scoped_guard()` (2024). Shows the indentation rule applied to new language features. |

No principle in this theme has been reversed. The stable core across 1993 to 2026 is: shallow nesting, no
`#ifdef`s in code, no special cases, explicit rules, no overdesign.

## Not in corpus

- "Talk is cheap. Show me the code." The phrase "talk is cheap" occurs (1999 interview, several mails 2002 to 2007),
  but I did not check for the exact famous 2000 LKML wording and did not use it; it belongs to another theme anyway.
- The exact linked-list "good taste" slide code from TED 2016 is not in the corpus (the transcript is auto-captions
  of speech; the slide is described, not reproduced). The Slashdot 2012 answer has the code and is used instead.
- "if you need more than 3 levels of indentation, you're screwed anyway" exists only in `coding-style.rst` and in a
  `>` quote in his 2007 reply; his own line there is the authorship claim, which is how it is cited.
- Coding-style's "one or two screenfuls", five to ten local variables, functions that do one thing: I found no mail
  where he states these numbers himself.

## Looked for and did not find (or found thin)

- A clear statement on boolean/flag parameters that make one function do two things: only scattered remarks
  (2017 untyped `flags` arguments are confusing, 2022 drop a `flags` argument). Not enough for a principle.
- `goto`-based error handling as a taste point: no substantive defence or attack found in his own text beyond use in
  examples.
- Explicit rules on maximum function length in lines: none in mail; he talks about indentation and complexity.
- Dead code inside functions (unreachable branches, commented-out code) specifically: thin; most material is about
  unused interfaces and legacy support.
- Positive statements about OO hierarchies, inheritance or generics: one 2007 pro-OO-interfaces remark with "explicit
  syntax", and 2025 approval of kernel "generics" whose use cases are readable; not enough for a separate principle.

## Inferences vs checked facts

Checked: every quote (verifier 113/113), dates and URLs from the `docs` table, and the full text of about 45
messages, including the context of each "limit" quote. Inferred: the reconciliations between apparently conflicting
statements (helper scope in 7, sharing rule in 11, the post-2018 tone shift), the transfer notes in "Outside the
kernel", and the per-principle message counts, which are estimates from search hits I read rather than exact counts.
