#!/usr/bin/env python3
"""List double-quoted phrases (4+ words) in analysis/skill markdown that are not his own text anywhere in corpus.db.

Usage: check_inline_quotes.py <corpus.db> <file.md> [...]
A hit is not always an error (made-up examples, labels), but each one should be looked at.
"""
import re, sqlite3, sys

def squash(t): return re.sub(r"\s+", " ", t).strip()

db, files = sys.argv[1], sys.argv[2:]
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
own = " \x00 ".join(
    squash("\n".join(l for l in (b or "").splitlines() if not l.lstrip().startswith(">")))
    for (b,) in con.execute("SELECT body FROM docs"))
for path in files:
    text = open(path, encoding="utf-8").read()
    miss = 0
    for m in re.finditer(r'["“]([^"“”\n]{20,400})["”]', text):
        q = squash(m.group(1)).rstrip(".,;:")
        if len(q.split()) < 4: continue
        if q not in own:
            miss += 1
            line = text.count("\n", 0, m.start()) + 1
            print(f"{path}:{line}: {q[:110]}")
    print(f"== {path}: {miss} unmatched")
