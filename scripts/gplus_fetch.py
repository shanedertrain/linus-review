#!/usr/bin/env python3
"""Linus Torvalds' Google+ posts (2011-2019) from Wayback Machine captures of plus.google.com.

Enumeration: Wayback CDX for plus.google.com/102150693225130002912/posts/* (and /u/0/...) with HTTP 200;
latest 200 capture per post id. Parse: the post text (<div class="uj"> in the 2011-12 markup) and every
comment by 'Linus Torvalds' under it (he argued a lot in comments). Posts whose capture holds no readable
text (JS-only shells) are logged in raw/gplus/failures.txt. There is no systematic export of the full stream.
"""
import html, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

RAW = os.path.join(ROOT, "raw", "gplus"); os.makedirs(os.path.join(RAW, "pages"), exist_ok=True)
UID = "102150693225130002912"
PREFIXES = ["plus.google.com/%s/posts/" % UID, "plus.google.com/u/0/%s/posts/" % UID, "plus.google.com/u/1/%s/posts/" % UID]
CDX = "https://web.archive.org/cdx/search/cdx?url=%s&matchType=prefix&output=text&fl=original,timestamp,statuscode&filter=statuscode:200"


def cdx():
    caps = {}
    for i, pre in enumerate(PREFIXES):
        fn = os.path.join(RAW, "cdx_prefix%d.txt" % i)
        if not os.path.exists(fn):
            open(fn, "w").write(fetch(CDX % pre, min_gap=2.0, timeout=180))
        for line in open(fn):
            p = line.split()
            if len(p) < 2: continue
            m = re.match(r"https?://plus\.google\.com/(?:u/\d/)?%s/posts/([A-Za-z0-9]+)(?:\?.*)?$" % UID, p[0])
            if m: caps.setdefault(m.group(1), set()).add((p[1], p[0]))
    return {k: sorted(v) for k, v in caps.items()}


def parse(t, pid, ts):
    tx = lambda s: html_to_text(s.replace("<br />", "<br>"))
    out = []
    m = re.search(r'<div class="uj">(.*?)</div></div><div class="lp">', t, re.S)
    d = re.search(r"Post date:\s*(\d{4}-\d\d-\d\d)", t)
    if m:
        out.append(("post", tx(m.group(1)), d.group(1) if d else ts[:4] + "-" + ts[4:6] + "-" + ts[6:8], None))
    for c in re.finditer(r'<a href="/%s"[^>]*>Linus Torvalds</a><span class="CE"> - </span><span class="nm">(.*?)</span></div>' % UID, t, re.S):
        # exact comment time sits in the OZ_initData blob as epoch ms next to the text
        body = tx(c.group(1))
        em = re.search(r',"%s",(\d{13}),"' % re.escape(html.unescape(re.sub(r"<[^>]+>", "", c.group(1))).replace("\\", "\\\\")[:40]), t) if False else None
        out.append(("comment", body, None, None))
    if out: return out
    # fallback 1 (2011 OZ_initData blob): ["...","Linus Torvalds","<post html with \\u003cbr />>", ...
    m = re.search(r'"Linus Torvalds","((?:[^"\\]|\\.){40,}?)"', t)
    if m:
        try: txt = tx(json.loads('"' + m.group(1) + '"'))
        except ValueError: txt = ""
        d = re.search(r"Post date:\s*(\d{4}-\d\d-\d\d)", t)
        if txt: return [("post", txt, d.group(1) if d else ts[:4] + "-" + ts[4:6] + "-" + ts[6:8], None)]
    # fallback 2 (2012-2019 AF_initDataCallback): Linus's own text blocks  ["Linus Torvalds","<uid>"...]  [[[0,"text"]
    pieces = []
    for mm in re.finditer(r'\["Linus Torvalds","%s"' % UID, t):
        seg = t[mm.end():mm.end() + 3000]
        tm = re.search(r'\[\[\[0,"((?:[^"\\]|\\.)*)"\]', seg)
        if tm:
            try: txt = tx(json.loads('"' + tm.group(1) + '"'))
            except ValueError: continue
            if txt and txt not in [p[1] for p in pieces]: pieces.append(("post" if not pieces else "comment", txt, None, None))
    dm = re.search(r'"Linus Torvalds","",(\d{13})', t)
    if pieces:
        import datetime
        dd = datetime.datetime.fromtimestamp(int(dm.group(1)) / 1000, datetime.timezone.utc).strftime("%Y-%m-%d") if dm else ts[:4] + "-" + ts[4:6] + "-" + ts[6:8]
        pieces[0] = (pieces[0][0], pieces[0][1], dd, None)
    return pieces


def main():
    caps = cdx()
    print(len(caps), "posts with a 200 capture", flush=True)
    docs = []
    for pid, lst in sorted(caps.items()):
        parts = None
        for ts, orig in lst[:6]:           # oldest captures first: they carry server-rendered text
            fn = os.path.join(RAW, "pages", "%s_%s.html" % (pid, ts))
            if not os.path.exists(fn):
                try: open(fn, "w", encoding="utf-8").write(fetch("https://web.archive.org/web/%sid_/%s" % (ts, orig), min_gap=2.0))
                except Exception as e: log_fail("gplus", orig, repr(e)); continue
            t = open(fn, encoding="utf-8", errors="replace").read()
            parts = parse(t, pid, ts)
            if any(k == "post" for k, *_ in parts): break
            parts = None
        if not parts:
            log_fail("gplus", pid, "no readable post text in %d capture(s) tried" % min(6, len(lst))); continue
        wb = "https://web.archive.org/web/%s/%s" % (ts, orig)
        base = "https://plus.google.com/%s/posts/%s" % (UID, pid)
        n = 0
        for kind, body, date, _ in parts:
            if kind == "post":
                docs.append(dict(id=base, source="gplus", kind="post", date=date, title=body.split("\n")[0][:100], url=wb, venue="Google+",
                                 in_reply_to=None, body=body, reviews_code=False))
            else:
                n += 1
                docs.append(dict(id="%s#linus-comment-%d" % (base, n), source="gplus", kind="post", date=parts[0][2], title="Comment: " + parts[0][1].split("\n")[0][:80],
                                 url=wb, venue="Google+ (comment by Linus under his post)", in_reply_to=base, body=body, reviews_code=False))
    print("gplus docs:", write_jsonl(os.path.join(ROOT, "docs", "gplus.jsonl"), docs))


if __name__ == "__main__":
    main()
