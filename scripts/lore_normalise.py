#!/usr/bin/env python3
"""raw/lore/*.mbox.gz -> docs/lore.jsonl (README schema). Standard library only.

Keeps only messages whose From is Linus Torvalds, dedupes by Message-ID (venues merged), decodes MIME and
charsets without ever raising, and writes stats/failures to docs/lore.report.json (not a docs/*.jsonl file).
Downloaded mail is data: nothing in it is executed.
"""
import argparse, collections, email, email.header, email.policy, email.utils, glob, gzip, hashlib, json, os, re, sys, urllib.parse, datetime

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
STATS = collections.Counter()
FAILS = []          # (file, what, detail)
ADDRS = collections.Counter()
EXCLUDED = collections.Counter()


def fail(src, what, detail=""):
    STATS["fail_" + what] += 1
    if len(FAILS) < 500:
        FAILS.append([src, what, str(detail)[:200]])


def split_mbox(data):
    """Yield (from_line, message_bytes). A message starts at a 'From ' line at BOF or after a blank line."""
    start = None; prev_blank = True; pos = 0; from_line = b""
    n = len(data)
    while pos < n:
        e = data.find(b"\n", pos)
        if e < 0:
            e = n
        line = data[pos:e]
        if line.startswith(b"From ") and prev_blank and (b"@" in line or b" 19" in line or b" 20" in line):
            if start is not None:
                yield from_line, data[start:pos]
            from_line = line; start = e + 1
        prev_blank = (line.strip() == b"")
        pos = e + 1
    if start is not None:
        yield from_line, data[start:]


def dec_hdr(v):
    if v is None:
        return ""
    v = str(v)
    try:
        out = []
        for s, cs in email.header.decode_header(v):
            if isinstance(s, bytes):
                for c in (cs, "utf-8", "latin-1"):
                    try:
                        out.append(s.decode(c or "ascii")); break
                    except Exception:
                        continue
            else:
                out.append(s)
        return re.sub(r"\s+", " ", "".join(out)).strip()
    except Exception:
        return re.sub(r"\s+", " ", v).strip()


def dec_payload(part):
    raw = part.get_payload(decode=True)
    if raw is None:
        p = part.get_payload()
        return p if isinstance(p, str) else ""
    cs = part.get_content_charset() or "utf-8"
    for c in (cs, "utf-8"):
        try:
            return raw.decode(c)
        except Exception:
            continue
    STATS["charset_fallback_latin1"] += 1
    return raw.decode("latin-1", "replace")


def strip_html(h):
    h = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "", h)
    h = re.sub(r"(?i)<br\s*/?>|</p>|</div>", "\n", h)
    h = re.sub(r"<[^>]+>", "", h)
    import html
    return html.unescape(h)


def get_body(msg):
    inline, attach, html = [], [], []
    for part in msg.walk():
        if part.is_multipart():
            continue
        ct = part.get_content_type()
        disp = str(part.get("Content-Disposition") or "").lower()
        if ct == "text/plain":
            (attach if disp.startswith("attachment") else inline).append(dec_payload(part))
        elif ct == "text/html":
            html.append(dec_payload(part))
    if inline:
        body = "\n".join(inline)
    elif attach:
        body = "\n".join(attach); STATS["body_from_attachment"] += 1
    elif html:
        body = "\n".join(strip_html(h) for h in html); STATS["body_from_html"] += 1
    else:
        body = ""; STATS["body_empty"] += 1
    return body.replace("\r\n", "\n").replace("\r", "\n")


def list_names(msg):
    names = []
    for h in ("List-Id", "X-Mailing-List", "Mailing-List"):
        for v in msg.get_all(h, []) or []:
            v = dec_hdr(v)
            m = re.search(r"<([^>]+)>", v) if h == "List-Id" else None
            tok = m.group(1) if m else v.split()[0] if v.split() else ""
            tok = tok.split("@")[0] if "@" in tok else tok
            tok = tok.split(".")[0]
            if tok and tok not in names:
                names.append(tok.lower())
        if names:
            break
    return names


def parse_date(msg, from_line):
    for cand in (msg.get("Date"),):
        if cand:
            try:
                d = email.utils.parsedate_to_datetime(str(cand))
                if d.tzinfo is None:
                    d = d.replace(tzinfo=datetime.timezone.utc)
                return d.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                pass
    STATS["date_from_mbox_fromline"] += 1
    try:
        t = from_line.decode("latin-1").split(None, 2)[2]
        d = datetime.datetime.strptime(t.strip(), "%a %b %d %H:%M:%S %Y")
        return d.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        fail("", "date_unparseable", msg.get("Message-ID"))
        return ""


QUOTE = re.compile(r"^\s*>")
HUNK = re.compile(r"^(?:>\s?)+(?:@@ -\d|diff --git |diff -[a-zA-Z]|Index: |--- \S|\+\+\+ \S|---$)")
PM = re.compile(r"^(?:>\s?)+[+-](?![+-]{2}\s)")
CLINE = re.compile(r"^(?:>\s?)+\s*(?:[^\s].*[;{}]\s*$|#\s*(?:include|define|if|endif|else)\b|(?:if|for|while|switch|return|static|struct|else|case|unsigned|int|void)\b.*|.*->\w+.*)")
ATTR = re.compile(r"(?i)^\s*(on .{5,200}wrote:?|.{1,100} writes:|\* .{1,100} wrote:|.*said:)\s*$")


def reviews_code(body):
    lines = body.split("\n")
    q_hunk = 0; q_pm = 0; run = 0; best = 0; own = 0; in_sig = False
    for ln in lines:
        if QUOTE.match(ln):
            if HUNK.match(ln): q_hunk += 1
            if PM.match(ln): q_pm += 1
            if CLINE.match(ln): run += 1; best = max(best, run)
            else: run = 0
        else:
            run = 0
            s = ln.strip()
            if ln.rstrip() == "--" or ln.startswith("-- "):
                in_sig = True
            if in_sig or not s or ATTR.match(ln):
                continue
            if len(re.sub(r"[^A-Za-z0-9]", "", s)) >= 3:
                own += 1
    quoted_diff = q_hunk >= 1 and q_pm >= 2
    quoted_c = best >= 4
    return bool((quoted_diff or quoted_c) and own >= 1)


def is_linus(name, addr):
    """From must be Linus Torvalds: display name has 'linus' (and torvalds in name or address), or the
    address is torvalds@... with no display name. Anything else (other Torvalds, spoofs) is excluded and reported."""
    a = addr.lower(); n = name.lower()
    if re.search(r"\bfor\s+linus|bot\d*\b", n):   # "tip-bot2 for Linus Torvalds" is a bot, not him
        return False
    if "linus" in n and ("torvalds" in n or "torvalds" in a):
        return True
    if a.startswith("torvalds@") and a.split("@")[1].endswith(("osdl.org", "transmeta.com", "linux-foundation.org", "linuxfoundation.org", "helsinki.fi", "kernel.org")):
        return True   # his own addresses, whatever the display name ("OSDL", empty)
    if not n.strip() and a.startswith("torvalds@"):
        return True
    if n.strip() in ("torvalds", "linux torvalds", "linus torvald"):
        return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=os.path.join(ROOT, "raw", "lore"))
    ap.add_argument("--out", default=os.path.join(ROOT, "docs", "lore.jsonl"))
    a = ap.parse_args()
    docs = {}
    for path in sorted(glob.glob(os.path.join(a.raw, "*.mbox.gz"))):
        src = os.path.basename(path)
        try:
            data = gzip.open(path, "rb").read()
        except Exception as e:
            fail(src, "bad_gzip", e); continue
        for from_line, mb in split_mbox(data):
            STATS["messages_read"] += 1
            try:
                mb = re.sub(rb"(?m)^>(>*From )", rb"\1", mb)   # undo mboxrd escaping
                msg = email.message_from_bytes(mb, policy=email.policy.compat32)
                name, addr = email.utils.parseaddr(dec_hdr(msg.get("From")))
                addr = addr.strip().lower()
                if not is_linus(name, addr):
                    STATS["excluded_not_linus"] += 1
                    EXCLUDED[f"{name} <{addr}>"] += 1
                    continue
                ADDRS[addr] += 1
                mid = (msg.get("Message-ID") or "").strip()
                m = re.search(r"<([^>]+)>", mid)
                mid = m.group(1).strip() if m else mid.strip("<> ")
                venues = list_names(msg)
                if not mid:
                    mid = "noid-" + hashlib.sha1(mb).hexdigest()
                    STATS["synthetic_message_id"] += 1
                if mid in docs:
                    d = docs[mid]
                    for v in venues:
                        if v not in d["_v"]: d["_v"].append(v)
                    STATS["duplicates_merged"] += 1
                    continue
                irt = re.search(r"<([^>]+)>", dec_hdr(msg.get("In-Reply-To")) or "")
                if not irt:
                    refs = re.findall(r"<([^>]+)>", dec_hdr(msg.get("References")))
                    irt = None
                    irt_v = refs[-1] if refs else None
                else:
                    irt_v = irt.group(1)
                body = get_body(msg)
                docs[mid] = {
                    "id": mid, "source": "lore", "kind": "email",
                    "date": parse_date(msg, from_line),
                    "title": dec_hdr(msg.get("Subject")),
                    "url": "https://lore.kernel.org/all/" + urllib.parse.quote(mid, safe="") + "/",
                    "_v": venues, "in_reply_to": irt_v, "body": body,
                    "reviews_code": reviews_code(body), "_addr": addr,
                }
            except Exception as e:
                fail(src, "parse_exception", e)
    out = sorted(docs.values(), key=lambda d: (d["date"], d["id"]))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    tmp = a.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for d in out:
            d["venue"] = ",".join(d.pop("_v")) or "lore"
            d.pop("_addr")
            f.write(json.dumps({k: d[k] for k in ("id", "source", "kind", "date", "title", "url", "venue", "in_reply_to", "body", "reviews_code")}, ensure_ascii=False) + "\n")
    os.replace(tmp, a.out)
    STATS["docs_written"] = len(out)
    STATS["reviews_code_true"] = sum(1 for d in out if d["reviews_code"])
    rep = {"stats": STATS, "addresses": ADDRS.most_common(), "excluded_senders": EXCLUDED.most_common(200),
           "failures": FAILS}
    json.dump(rep, open(os.path.join(os.path.dirname(a.out), "lore.report.json"), "w"), indent=1)
    print(json.dumps(STATS, indent=1))


if __name__ == "__main__":
    main()
