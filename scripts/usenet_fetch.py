#!/usr/bin/env python3
"""Merge every Usenet-era input into docs/usenet.jsonl (dedupe by Message-ID).

Inputs
  raw/usenet/oldlinux/linus-in-minix.txt, linus-in-linux.txt  - Google Groups search dumps of his comp.os.minix /
        comp.os.linux posts (1991-1992), from github.com/oldlinux-web/oldlinux-files (mail-archive/linux-activists/)
  raw/usenet/oldlinux/cmu-history.html  - his own 1992 compilation of the first posts (cs.cmu.edu/~awb/linux.history.html)
  raw/usenet/oldlinux/appa.html         - Tanenbaum-Torvalds debate (O'Reilly Open Sources appendix A copy of the Usenet posts)
  raw/usenet/yarchive_posts.jsonl       - from yarchive_fetch.py
Fetching is resumable (existing raw files are kept).
"""
import html, json, os, re, sys
from email.utils import parsedate_to_datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

RAW = os.path.join(ROOT, "raw", "usenet", "oldlinux"); os.makedirs(RAW, exist_ok=True)
GH = "https://raw.githubusercontent.com/oldlinux-web/oldlinux-files/master/mail-archive/linux-activists/"
GHV = "https://github.com/oldlinux-web/oldlinux-files/blob/master/mail-archive/linux-activists/"
FILES = [("linus-in-minix.txt", GH + "Linus%20in%20Minix-group.txt", GHV + "Linus%20in%20Minix-group.txt"),
         ("linus-in-linux.txt", GH + "Linus%20in%20Linux-group.txt", GHV + "Linus%20in%20Linux-group.txt"),
         ("cmu-history.html", "https://www.cs.cmu.edu/~awb/linux.history.html", None),
         ("appa.html", "https://www.oreilly.com/openbook/opensources/book/appa.html", None)]


def get(fn, url):
    p = os.path.join(RAW, fn)
    if not os.path.exists(p):
        try: open(p, "w", encoding="utf-8").write(fetch(url, min_gap=2.0))
        except Exception as e: log_fail("usenet", url, repr(e)); return ""
    return open(p, encoding="utf-8").read()


def to_date(s):
    try: return parsedate_to_datetime(s).isoformat()
    except Exception: pass
    m = re.match(r"(\d{4})/(\d\d)/(\d\d)(?:\s+(\d\d:\d\d:\d\d))?", s)
    if m: return "%s-%s-%sT%s+00:00" % (m.group(1), m.group(2), m.group(3), m.group(4) or "00:00:00")
    return s


def parse_block(blk, url):
    """One post: RFC-1036 style headers, blank line, body."""
    hdr, _, body = blk.strip("\n").partition("\n\n")
    hd = {}
    last = None
    for line in hdr.split("\n"):
        if line[:1] in " \t" and last: hd[last] += " " + line.strip(); continue
        m = re.match(r"([A-Za-z-]+):\s*(.*)", line)
        if m: last = m.group(1).lower(); hd[last] = m.group(2).strip()
    if "torvalds" not in hd.get("from", "").lower() or "message-id" not in hd: return None
    body = body.strip("\n")
    refs = hd.get("references", "").split()
    mid = re.match(r"<?([^<>\s]+)", hd["message-id"]).group(1)
    return dict(id="news:" + mid, source="usenet", kind="usenet", date=to_date(hd.get("date", "")),
                title=hd.get("subject", ""), url=url, venue=hd.get("newsgroups", ""),
                in_reply_to=("news:" + refs[-1].strip("<>")) if refs else None, body=body, reviews_code=reviews_code(body))


def from_dump(text, url):
    out = []
    for blk in re.split(r"\n={20,}\n(?:={20,}\n)?", text):
        if "\nMessage-ID:" in blk or blk.lstrip().startswith("From:"):
            d = parse_block(blk[blk.find("From:"):] if "From:" in blk else blk, url)
            if d: out.append(d)
    return out


def from_cmu(text, url):
    """Linus's July 1992 compilation of his own first posts with his commentary: one document."""
    t = html.unescape(re.sub(r"<[^>]+>", "", text))
    body = "\n".join(l[2:] if l.startswith("  ") else l for l in t.split("\n")).strip()
    return [dict(id=url, source="usenet", kind="usenet", date="1992-07-31", title="LINUX's History (his 1992 compilation of the first posts, with commentary)",
                 url=url, venue="comp.os.minix / comp.os.linux (compiled)", in_reply_to=None, body=body, reviews_code=False)]


def from_appa(text, url):
    """Tanenbaum-Torvalds debate: posts are blocks that start with a column-0 'From:' line; keep his."""
    t = html.unescape(re.sub(r"<[^>]+>", "", text)).replace("\xa0", "")
    parts = re.split(r"(?m)^(?=From: )", t)
    out = []
    for i, blk in enumerate(parts):
        if not re.match(r"From: .*torvalds", blk, re.I): continue
        hdr, _, body = blk.partition("\n\n") if "\n\n" in blk else blk.partition("\n")
        hd = {}
        for line in hdr.split("\n"):
            m = re.match(r"([A-Za-z-]+):\s*(.*)", line)
            if m: hd[m.group(1).lower()] = m.group(2).strip()
        body = re.sub(r"(?m)^\s*$\n(?=\s*$)", "", body).strip()
        body = re.split(r"\n\s*Appendix A|\n\s*Back to|\n\s*Copyright ", body)[0].strip()
        out.append(dict(id="%s#%s|%s" % (url, hd.get("date", i), hd.get("subject", "")), source="usenet", kind="usenet",
                        date=to_date(hd.get("date", "")), title=hd.get("subject", ""), url=url, venue="comp.os.minix",
                        in_reply_to=None, body=body, reviews_code=False))
    return out


def main():
    docs = {}
    for fn, url, view in FILES:
        text = get(fn, url)
        ds = from_dump(text, view) if view else (from_cmu(text, url) if "cmu" in fn else from_appa(text, url))
        print(fn, len(ds), "linus posts", flush=True)
        for d in ds:
            if fn == "appa.html" and any(x["date"] == d["date"] and x["title"] == d["title"] for x in docs.values()):
                continue  # same post already present with its Message-ID
            docs.setdefault(d["id"], d)
    from datetime import datetime
    def fixdate(d):
        if d["date"][:1].isalpha():
            try: d["date"] = datetime.strptime(d["date"], "%b %d %Y").strftime("%Y-%m-%dT00:00:00+00:00")
            except ValueError: pass
        return d
    yp = os.path.join(ROOT, "raw", "usenet", "yarchive_posts.jsonl")
    if os.path.exists(yp):
        for l in open(yp, encoding="utf-8"):
            d = fixdate(json.loads(l)); docs.setdefault(d["id"], d)
    extra = os.path.join(ROOT, "raw", "usenet", "activists_posts.jsonl")
    if os.path.exists(extra):
        for l in open(extra, encoding="utf-8"):
            d = fixdate(json.loads(l)); docs.setdefault(d["id"], d)
    print("usenet docs:", write_jsonl(os.path.join(ROOT, "docs", "usenet.jsonl"), list(docs.values())))


if __name__ == "__main__":
    main()
