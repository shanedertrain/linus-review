#!/usr/bin/env python3
"""Linus Torvalds' messages in the 1991-95 Linux mailing-list digests and funet kernel list archives
(github.com/oldlinux-web/oldlinux-files, mail-archive/; cloned sparse by oldlinux_fetch.sh) plus the early
alt.os.linux / sfnet Usenet captures there.  Writes raw/usenet/activists_posts.jsonl, merged by usenet_fetch.py.

These are email lists (linux-activists, linux-devel, linux-admin, linux-misc, funet 'kernel'), not lore.
Messages have no stable Message-ID in the digests; id = 'oldlinux:<path>#<n>' of the first copy found.
"""
import gzip, hashlib, io, json, os, re, sys, tarfile
from email.utils import parsedate_to_datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

BASE = os.path.join(ROOT, "raw", "usenet", "oldlinux-files")
MA = os.path.join(BASE, "mail-archive")
GH = "https://github.com/oldlinux-web/oldlinux-files/blob/master/"
FROM = re.compile(r"^From: .*(torvalds|Linus B)", re.I)
HDR = re.compile(r"^[A-Za-z][A-Za-z0-9-]*:( |$)")
SEP = re.compile(r"^(-{20,}|={20,}|_{20,}|\*{20,})\s*$")
MBOX = re.compile(r"^From \S+.*\d{4}\s*$")
STARTHDR = re.compile(r"^(Subject|Date|Newsgroups|To|Message-ID|Reply-To|Organization|References):", re.I)


def blobs(path):
    """Yield (label, text) for a file, unpacking gzip/tar."""
    rel = os.path.relpath(path, BASE)
    data = open(path, "rb").read()
    def dec(b):
        if b[:2] == b"\x1f\x8b":
            try: return gzip.decompress(b)
            except Exception: return b
        return b
    data = dec(data)
    if len(data) > 512 and data[257:262] == b"ustar":
        with tarfile.open(fileobj=io.BytesIO(data)) as t:
            for m in t:
                if m.isfile():
                    b = dec(t.extractfile(m).read())
                    yield rel + "!" + m.name, b.decode("latin-1")
        return
    if data[:4] == b"\x1f\x9d\x90":  # unix compress, not supported by the stdlib
        log_fail("usenet", rel, "compress(1) format, skipped (a gzip copy usually exists)"); return
    yield rel, data.decode("latin-1")


def messages(label, text):
    lines = text.replace("\r\n", "\n").split("\n")
    n = 0
    for i, l in enumerate(lines):
        if not FROM.match(l): continue
        # header start: walk back over header-looking / continuation lines
        s = i
        while s > 0 and (HDR.match(lines[s - 1]) or lines[s - 1][:1] in " \t") and lines[s - 1].strip():
            s -= 1
        # a header block needs a Subject/Date/Newsgroups in the following lines
        if not any(STARTHDR.match(x) for x in lines[s:i + 12]): continue
        j = i
        while j < len(lines) and lines[j].strip(): j += 1  # end of headers
        k = j
        while k < len(lines):
            if SEP.match(lines[k]) or MBOX.match(lines[k]): break
            if k > j and lines[k].startswith("From: ") and not lines[k - 1].strip() and any(STARTHDR.match(x) for x in lines[k + 1:k + 4]): break
            k += 1
        hd = {}; last = None
        for x in lines[s:j]:
            if x[:1] in " \t" and last: hd[last] += " " + x.strip(); continue
            m = re.match(r"([A-Za-z-]+):\s*(.*)", x)
            if m: last = m.group(1).lower(); hd.setdefault(last, m.group(2).strip())
        body = "\n".join(lines[j:k]).strip("\n")
        n += 1
        yield n, hd, body


def to_date(s):
    try: return parsedate_to_datetime(s).isoformat()
    except Exception: return s


def main():
    seen = {}; docs = []; files = 0
    for dp, dn, fn in os.walk(MA):
        for f in sorted(fn):
            p = os.path.join(dp, f)
            if f.endswith(".SUBJECTS") or f.startswith("CONTENTS"): continue
            files += 1
            try:
                for label, text in blobs(p):
                    for n, hd, body in messages(label, text):
                        if len(body) < 20: continue
                        key = hashlib.sha1((to_date(hd.get("date", "")) + hd.get("subject", "") + re.sub(r"\s+", " ", body)[:300]).encode()).hexdigest()
                        if key in seen: continue
                        seen[key] = 1
                        mid = re.match(r"<?([^<>\s]+)", hd["message-id"]).group(1) if hd.get("message-id") else None
                        rel = label.split("!")[0]
                        refs = hd.get("references", "").split()
                        docs.append(dict(id=("news:" + mid) if mid else "oldlinux:%s#%d" % (label, n), source="usenet", kind="usenet",
                                         date=to_date(hd.get("date", "")), title=hd.get("subject", ""), url=GH + rel.replace(" ", "%20"),
                                         venue=hd.get("newsgroups") or ("linux mailing lists (" + rel.split("/")[1] + ")" if "/" in rel else rel),
                                         in_reply_to=("news:" + refs[-1].strip("<>")) if refs else None, body=body, reviews_code=reviews_code(body)))
            except Exception as e:
                log_fail("usenet", p, repr(e))
    print(files, "files;", len(docs), "messages")
    print("activists:", write_jsonl(os.path.join(ROOT, "raw", "usenet", "activists_posts.jsonl"), docs))


if __name__ == "__main__":
    main()
