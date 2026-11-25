#!/usr/bin/env python3
"""Published written interviews / Q&As with Linus Torvalds on freely readable pages.

URLS lists (url, title, venue, date, start-regex, end-regex). The page is downloaded once to raw/interview/,
the article region is cut with the regexes and converted to text. The interviewer's questions are kept so each
answer makes sense; page chrome, comments and related-article lists are cut. Speaker markers come from the
interview's own formatting (the text keeps the question lines as published). Output docs/interview.jsonl.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

RAW = os.path.join(ROOT, "raw", "interview"); os.makedirs(RAW, exist_ok=True)
A = r"<article\b"
URLS = [
 ("https://www.tag1.com/blog/interview-linus-torvalds-linux-and-git/", "An Interview With Linus Torvalds: Linux and Git, Part 1 (Jeremy Andrews, Tag1)", "Tag1 Consulting", "2021-04-28", A, r"</article>"),
 ("https://meta.slashdot.org/story/12/10/11/0030249/linus-torvalds-answers-your-questions", "Linus Torvalds Answers Your Questions (Slashdot)", "Slashdot", "2012-10-11", r'<article id="firehose-', r"</article>"),
 ("https://spectrum.ieee.org/linux-at-25-qa-with-linus-torvalds", "Linux at 25: Q&A With Linus Torvalds", "IEEE Spectrum", "2016-08-25", r'<article elid=', r"</article>"),
 ("https://www.linuxjournal.com/article/3103", "LJ Interviews Linus Torvalds (1998)", "Linux Journal", "1998-12-01", r"field--name-body[^>]*>", r'id="comments"|<section[^>]*comment|</article>'),
 ("https://www.linuxjournal.com/article/146", "LJ Interviews Linus Torvalds (1996)", "Linux Journal", "1996-09-01", r"field--name-body[^>]*>", r'id="comments"|<section[^>]*comment|</article>'),
 ("https://www.linuxjournal.com/article/5027", "A Conversation with Linus Torvalds (Doc Searls, Linux For Suits)", "Linux Journal", "1999-10-12", r"field--name-body[^>]*>", r'id="comments"|<section[^>]*comment|</article>'),
 ("https://www.linuxjournal.com/content/25-years-later-interview-linus-torvalds", "25 Years Later: Interview with Linus Torvalds (reprint of LJ issue 1, 1994)", "Linux Journal", "2019-04-02", A, r'id="comments"|<section[^>]*comment|</article>'),
 ("https://techcrunch.com/2012/04/19/an-interview-with-millenium-technology-prize-finalist-linus-torvalds/", "An Interview With Millennium Technology Prize Finalist Linus Torvalds (TechCrunch, Scott Merrill)", "TechCrunch", "2012-04-19", r'class="[^"]*entry-content[^"]*"[^>]*>', r"</article>|<footer"),
 ("https://www.linuxfoundation.org/blog/blog/10-years-of-git-an-interview-with-git-creator-linus-torvalds", "10 Years of Git: An Interview with Git Creator Linus Torvalds (Linux Foundation)", "Linux Foundation", "2015-04-06", r"<main\b", r"</main>"),
 ("https://lwn.net/Articles/37719/", "An interview with Linus Torvalds (LWN.net, 2003)", "LWN.net", "2003-10-01", r'class="ArticleText"[^>]*>', r"<hr|<div class=\"(?:CommentBox|Footer)"),
 ("https://www.computerworld.com/article/1685910/linus-torvalds.html", "Linus Torvalds Q&A (Computerworld)", "Computerworld", "2007-10-22", r'<article id="post-', r"</article>"),
 ("https://web.archive.org/web/2021id_/https://www.tag1.com/blog/interview-linus-torvalds-open-source-and-beyond/", "An Interview With Linus Torvalds: Open Source and Beyond, Part 2 (Jeremy Andrews, Tag1; Wayback copy, site returns 403)", "Tag1 Consulting", "2021-05-05", A, r"</article>"),
]


import hashlib
def slug(u): return re.sub(r"[^A-Za-z0-9]+", "_", u.split("//")[1])[:60] + hashlib.md5(u.encode()).hexdigest()[:8] + ".html"


def main(urls=URLS):
    docs = []
    for u, title, venue, date, st, en in urls:
        fn = os.path.join(RAW, slug(u))
        if not os.path.exists(fn):
            try: open(fn, "w", encoding="utf-8").write(fetch(u, min_gap=2.0))
            except Exception as e: log_fail("interview", u, repr(e)); continue
        t = open(fn, encoding="utf-8", errors="replace").read()
        m = re.search(st, t)
        if not m: log_fail("interview", u, "start marker not found"); continue
        rest = t[m.start():]
        e = re.search(en, rest[200:])
        seg = rest[:200 + e.start()] if e else rest
        body = html_to_text(seg)
        body = re.sub(r"^(field--name-body|class=)[^>]*>\s*", "", body)
        for tail in (r"\n+Share\s*\n+Related", r"\n+From Your Site Articles", r"\n+Related Insights", r"\n+© 20", r"\n+- PRIVACY POLICY",
                     r"\n+Related Stories", r"\n+-\s*Opinion:", r"\n+Git Success Stories", r"\n+Related (Articles|Posts|Reading)", r"\n+Loading the next", r"\n+Topics\s*\n", r"\n+Tags?\s*[:\n]", r"\n+Share this", r"\n+\s*Load Disqus", r"\n+←", r"\n+In the second part of this interview", r"\n+You May Like", r"\n+Linus Explains What Surprises", r"\n+(Share|Sponsored) ", r"\n+Related\s*\n", r"\n+More from "):
            mm = re.search(tail, body)
            if mm and mm.start() > 2000: body = body[:mm.start()]
        docs.append(dict(id=u, source="interview", kind="transcript", date=date, title=title, url=u, venue=venue,
                         in_reply_to=None, body=body, reviews_code=False))
        print(len(body), title, flush=True)
    print("interview docs:", write_jsonl(os.path.join(ROOT, "docs", "interview.jsonl"), docs))


if __name__ == "__main__":
    main()
