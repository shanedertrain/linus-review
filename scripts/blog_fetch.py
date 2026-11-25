#!/usr/bin/env python3
"""Fetch every post of torvalds-family.blogspot.com via the Blogger JSON feed."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

BASE = "https://torvalds-family.blogspot.com/feeds/posts/default?alt=json&max-results=150&start-index=%d"
raw = os.path.join(ROOT, "raw", "blog"); os.makedirs(raw, exist_ok=True)
docs = []; start = 1; page = 0
while True:
    fn = os.path.join(raw, "feed_%05d.json" % start)
    if os.path.exists(fn):
        txt = open(fn, encoding="utf-8").read()
    else:
        try:
            txt = fetch(BASE % start)
        except Exception as e:
            log_fail("blog", BASE % start, repr(e)); break
        open(fn, "w", encoding="utf-8").write(txt)
    feed = json.loads(txt)["feed"]
    entries = feed.get("entry", [])
    if not entries: break
    for e in entries:
        link = next((l["href"] for l in e["link"] if l["rel"] == "alternate"), None)
        if not link: continue
        body = html_to_text(e.get("content", {}).get("$t", ""))
        docs.append(dict(id=link, source="blog", kind="post", date=e["published"]["$t"],
                         title=e.get("title", {}).get("$t", ""), url=link,
                         venue="torvalds-family.blogspot.com", in_reply_to=None,
                         body=body, reviews_code=False))
    start += len(entries)
    if len(entries) < 150: break
print("blog docs:", write_jsonl(os.path.join(ROOT, "docs", "blog.jsonl"), docs))
