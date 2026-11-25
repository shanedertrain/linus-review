#!/usr/bin/env python3
"""Linus Torvalds' Usenet / forum posts as archived topic-by-topic on yarchive.net (comp/ section).

Index page lists each topic page with its authors; every page whose authors include Linus Torvalds
is fetched into raw/usenet/yarchive/, each <pre> block is a whole original post with its headers.
Writes raw/usenet/yarchive_posts.jsonl; scripts/usenet_fetch.py merges all Usenet inputs into docs/usenet.jsonl.
"""
import html, json, os, re, sys
from email.utils import parsedate_to_datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

RAW = os.path.join(ROOT, "raw", "usenet", "yarchive"); os.makedirs(RAW, exist_ok=True)
HOST = "https://yarchive.net/comp/"


def get(url, fn):
    if os.path.exists(fn) and os.path.getsize(fn): return open(fn, encoding="utf-8").read()
    try: t = fetch(url, min_gap=2.0)
    except Exception as e:
        log_fail("usenet", url, repr(e)); return None
    open(fn, "w", encoding="utf-8").write(t); return t


def main():
    idx = get(HOST + "index.html", os.path.join(RAW, "index.html"))
    pages = [(h, t, a) for h, t, a in re.findall(r'<a href="([^"]+)">([^<]*)</a>\s*\(([^)]*)\)', idx) if "Linus Torvalds" in a]
    print(len(pages), "pages with Linus", flush=True)
    for h, t, a in pages:
        get(HOST + h, os.path.join(RAW, h.replace("/", "__")))
    build(pages)


def build(pages):
    docs, rwt = [], []
    for h, title, _ in pages:
        fn = os.path.join(RAW, h.replace("/", "__"))
        if not os.path.exists(fn): continue
        page = open(fn, encoding="utf-8").read()
        pageurl = HOST + h
        for m in re.finditer(r'<a name="(\d+)"></a>\s*<pre>(.*?)</pre>', page, re.S):
            n, blk = m.group(1), m.group(2)
            hdr, _, body = blk.partition("\n\n")
            hd = html.unescape(re.sub(r"<[^>]+>", "", hdr))
            if not re.search(r"^From:.*Linus", hd, re.M | re.I): continue
            g = lambda k: (re.search(r"^%s:\s*(.*)$" % k, hd, re.M | re.I) or [None, ""])[1].strip()
            mid = g("Message-ID").strip("<>")
            try: date = parsedate_to_datetime(g("Date")).isoformat()
            except Exception: date = g("Date")
            text = html.unescape(re.sub(r"<[^>]+>", "", body)).strip("\n")
            ng = g("Newsgroups")
            d = dict(id=("news:" + mid) if mid else "%s#%s" % (pageurl, n), source="usenet", kind="usenet", date=date,
                     title=g("Subject") or title.strip(), url="%s#%s" % (pageurl, n), venue=ng or "yarchive.net",
                     in_reply_to=None, body=text, reviews_code=reviews_code(text))
            refs = g("References")
            if refs: d["in_reply_to"] = "news:" + refs.split()[-1].strip("<>")
            docs.append(d)
    print("yarchive posts:", write_jsonl(os.path.join(ROOT, "raw", "usenet", "yarchive_posts.jsonl"), docs))


if __name__ == "__main__":
    main()
