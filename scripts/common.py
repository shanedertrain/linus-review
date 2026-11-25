"""Shared helpers for the web-source fetchers (stdlib only)."""
import fcntl, html, json, os, re, sys, time, urllib.request, urllib.error
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "linus-corpus-research/0.1 (personal research archive)"
_last = {}


def fetch(url, min_gap=1.5, tries=5, binary=False, timeout=60):
    """GET with per-host spacing and backoff on 429/5xx. Returns str/bytes or raises."""
    host = urllib.parse.urlparse(url).netloc
    delay = 10
    for attempt in range(tries):
        # one request at a time per host across all fetcher processes: lock file + shared last-request stamp
        lk = open(os.path.join("/tmp", "linus-corpus-%s.lock" % host), "a+")
        fcntl.flock(lk, fcntl.LOCK_EX)
        try:
            lk.seek(0); prev = float((lk.read() or "0").strip() or 0)
        except ValueError:
            prev = 0
        wait = max(prev, _last.get(host, 0)) + min_gap - time.time()
        if wait > 0:
            time.sleep(wait)
        _last[host] = time.time()
        lk.seek(0); lk.truncate(); lk.write(str(time.time())); lk.flush()
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
                if data[:2] == b"\x1f\x8b":
                    import gzip; data = gzip.decompress(data)
                _last[host] = time.time()
                if binary:
                    return data
                cs = r.headers.get_content_charset() or "utf-8"
                return data.decode(cs, "replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(delay); delay *= 2; continue
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            time.sleep(delay); delay *= 2
        finally:
            fcntl.flock(lk, fcntl.LOCK_UN); lk.close()
    raise RuntimeError("giving up after %d tries: %s" % (tries, url))


import urllib.parse  # noqa: E402


class _T(HTMLParser):
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre", "ul", "ol", "table"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []; self.pre = 0; self.skip = 0; self.bq = 0

    def handle_starttag(self, t, a):
        if t in ("script", "style"): self.skip += 1
        if t == "pre": self.pre += 1; self.out.append("\n\n")
        elif t == "br": self.out.append("\n")
        elif t == "blockquote": self.bq += 1; self.out.append("\n\n")
        elif t == "li": self.out.append("\n- ")
        elif t in self.BLOCK: self.out.append("\n\n")

    def handle_endtag(self, t):
        if t in ("script", "style"): self.skip = max(0, self.skip - 1)
        if t == "pre": self.pre = max(0, self.pre - 1); self.out.append("\n\n")
        elif t == "blockquote": self.bq = max(0, self.bq - 1); self.out.append("\n\n")
        elif t in self.BLOCK: self.out.append("\n\n")

    def handle_data(self, d):
        if self.skip: return
        if not self.pre: d = re.sub(r"[ \t\r\n]+", " ", d)
        self.out.append(d)


def html_to_text(h):
    p = _T(); p.feed(h); p.close()
    t = "".join(p.out)
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n[ \t]+(?=\S)", "\n", t) if False else t
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def reviews_code(body):
    return bool(re.search(r"^\s*(>\s*)+(\+|-|@@|diff --git|index [0-9a-f]+\.\.)", body, re.M)
                or re.search(r"^\s*(>\s*)+\s*(static |int |void |struct |#include|#define|\w+\s*\([^)]*\)\s*\{|\}\s*$|if \(|for \(|return\b.*;)", body, re.M))


def write_jsonl(path, docs):
    seen = {}
    for d in docs: seen[d["id"]] = d
    with open(path, "w", encoding="utf-8") as f:
        for d in sorted(seen.values(), key=lambda d: (d["date"], d["id"])):
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    return len(seen)


def log_fail(source, url, why):
    with open(os.path.join(ROOT, "raw", source, "failures.txt"), "a") as f:
        f.write("%s\t%s\t%s\n" % (time.strftime("%F %T"), url, why))
