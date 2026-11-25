#!/usr/bin/env python3
"""Fetch Linus-written kernel documentation and historic release files into raw/kernel-docs/,
then write docs/kernel-docs.jsonl. Stdlib only, sequential, 1s apart, resumable (skips cached files).

  fetch   : Documentation/process/*.rst at linux master (git.kernel.org plain), kernel.org Historic files
  select  : INCLUDE below (decided by reading each file's own attribution, see report notes)
Usage: kernel_docs_fetch.py [--all-process]   (--all-process only caches every process doc, for attribution checks)
"""
import json, os, re, sys, time, urllib.request, urllib.error, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw", "kernel-docs")
UA = "corpus-research-fetch/1.0"
LINUX = "https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git"
HIST = "https://www.kernel.org/pub/linux/kernel/Historic/old-versions/"

# Process docs that are Linus's own writing (wholly or in the main), see README of this run.
PROCESS_INCLUDE = ["coding-style.rst", "management-style.rst"]
# extra process docs added after attribution check are appended here by the checker
PROCESS_EXTRA = []
HIST_FILES = ["README", "RELNOTES-0.01", "RELNOTES-0.12", "RELNOTES-0.95", "RELNOTES-0.95a", "RELNOTES-0.97"]

_last = [0.0]


def get(url, retries=3):
    for i in range(retries):
        wait = 1.0 - (time.time() - _last[0])
        if wait > 0: time.sleep(wait)
        _last[0] = time.time()
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read(), r.headers
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                print("BLOCKED/backoff", e.code, url, file=sys.stderr)
                if i == retries - 1: sys.exit("stopping: server is rate-limiting us")
                time.sleep(30 * (i + 1)); continue
            raise
    raise RuntimeError(url)


def cached(path, url):
    if os.path.exists(path): return open(path, "rb").read(), None
    data, hdr = get(url)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "wb").write(data)
    return data, hdr


def main():
    all_process = "--all-process" in sys.argv
    rows = []
    names = PROCESS_INCLUDE + PROCESS_EXTRA
    if all_process:
        idx, _ = cached(os.path.join(RAW, "process-tree.html"), LINUX + "/tree/Documentation/process")
        names = sorted(set(re.findall(r"Documentation/process/([A-Za-z0-9_.-]+\.rst)['\"?]", idx.decode())))
    for n in names:
        url = f"{LINUX}/plain/Documentation/process/{n}"
        data, hdr = cached(os.path.join(RAW, "process", n), url)
        if all_process: continue
        text = data.decode("utf-8", "replace")
        rows.append({"id": url, "source": "kernel-docs", "kind": "doc", "date": datetime.date.today().isoformat(),
                     "title": "Documentation/process/" + n, "url": url, "venue": "linux/Documentation",
                     "in_reply_to": None, "body": text, "reviews_code": False})
    if all_process: return
    # Historic: dates from the directory listing (Last modified column)
    idx, _ = cached(os.path.join(RAW, "historic-index.html"), HIST)
    listing = re.sub(r"<[^>]+>", " ", idx.decode("utf-8", "replace"))
    for n in HIST_FILES:
        url = HIST + n
        data, hdr = cached(os.path.join(RAW, "hist", n), url)
        m = re.search(re.escape(n) + r"\s+(\d{2}-[A-Za-z]{3}-\d{4})", listing)
        date = datetime.datetime.strptime(m.group(1), "%d-%b-%Y").date().isoformat() if m else None
        title = "Linux historic " + n
        if n == "README":  # not the 0.01 README: it is Linus's post announcing 0.95a patch part 1/2
            date, title = "1992-04-04", "Linux historic README (post: Second 0.95a alpha-patch, part 1/2)"
        rows.append({"id": url, "source": "kernel-docs", "kind": "doc", "date": date,
                     "title": title, "url": url, "venue": "kernel.org/Historic",
                     "in_reply_to": None, "body": data.decode("latin-1" if b"\xe4" in data and not _utf8(data) else "utf-8", "replace"),
                     "reviews_code": False})
    with open(os.path.join(ROOT, "docs", "kernel-docs.jsonl"), "w", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    for r in rows: print(len(r["body"]), r["date"], r["url"])


def _utf8(b):
    try: b.decode("utf-8"); return True
    except UnicodeDecodeError: return False


if __name__ == "__main__":
    main()
