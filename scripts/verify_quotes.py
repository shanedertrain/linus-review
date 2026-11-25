#!/usr/bin/env python3
"""Check that every quote in analysis/*.quotes.jsonl is in corpus.db, verbatim, in his own text.

Each line of a quotes file: {"principle": "...", "id": "<doc id>", "quote": "..."}.
A quote passes when, with whitespace collapsed, it is a substring of the document's
unquoted lines (lines not starting with '>'). It is reported as QUOTED when it is only
found in text he was quoting from someone else, and MISSING otherwise.

Usage: verify_quotes.py <corpus.db> <quotes.jsonl> [<quotes.jsonl> ...]
Exit status 1 when anything is not OK.
"""
import json
import re
import sqlite3
import sys


def squash(text):
    return re.sub(r"\s+", " ", text).strip()


def main():
    db, files = sys.argv[1], sys.argv[2:]
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    bad = 0
    for path in files:
        ok = total = 0
        for n, line in enumerate(open(path, encoding="utf-8"), 1):
            if not line.strip():
                continue
            total += 1
            try:
                rec = json.loads(line)
                doc_id, quote = rec["id"], rec["quote"]
            except (ValueError, KeyError) as err:
                print(f"BADLINE {path}:{n} {err}")
                bad += 1
                continue
            row = con.execute("SELECT body FROM docs WHERE id=?", (doc_id,)).fetchone()
            if row is None:
                print(f"NOID    {path}:{n} {doc_id}")
                bad += 1
                continue
            body = row[0] or ""
            own = squash("\n".join(l for l in body.splitlines() if not l.lstrip().startswith(">")))
            want = squash(quote)
            if want and want in own:
                ok += 1
            elif want and want in squash(re.sub(r"(?m)^\s*(>\s?)+", "", body)):
                print(f"QUOTED  {path}:{n} {doc_id} :: {want[:70]}")
                bad += 1
            else:
                print(f"MISSING {path}:{n} {doc_id} :: {want[:70]}")
                bad += 1
        print(f"{path}: {ok}/{total} ok")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
