#!/usr/bin/env python3
"""Download every message whose From header matches 'torvalds' from lore.kernel.org/all/.

One month window per file: raw/lore/all-YYYY-MM.mbox.gz. Resumable: a window whose file exists and is a
valid gzip is skipped (the current and previous month are always refetched, they are still growing).
Strictly sequential, >= 1.5 s between requests, exponential backoff on 429/5xx, stops on anything that
looks like a block or a challenge. A window that returns >= SPLIT_AT messages is refetched as weekly
windows (all-YYYY-MM-wN.mbox.gz) in case a result cap exists (none was observed up to 1500/year).
Python standard library only.
"""
import argparse, calendar, datetime, gzip, os, sys, time, urllib.error, urllib.parse, urllib.request

UA = "linus-corpus-research/0.1 (personal research archive)"
BASE = "https://lore.kernel.org/all/"
QUERY = "f:torvalds"
MIN_GAP = 1.6
SPLIT_AT = 1000
_last = 0.0


class Blocked(Exception):
    pass


def valid_gzip(path):
    try:
        with gzip.open(path, "rb") as f:
            while f.read(1 << 20):
                pass
        return True
    except Exception:
        return False


def count_msgs(path):
    n = 0
    with gzip.open(path, "rb") as f:
        for line in f:
            if line.startswith(b"From "):
                n += 1
    return n


def request(d1, d2):
    """POST the search with x=m. Returns bytes of mbox (possibly empty b'')."""
    global _last
    q = f"{QUERY} d:{d1:%Y%m%d}..{d2:%Y%m%d}"
    url = BASE + "?" + urllib.parse.urlencode({"q": q, "x": "m"})
    delay = 10
    for attempt in range(8):
        wait = MIN_GAP - (time.monotonic() - _last)
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(url, data=b"", method="POST", headers={"User-Agent": UA})
        status, body = None, b""
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                status, body = r.status, r.read()
        except urllib.error.HTTPError as e:
            status, body = e.code, e.read()
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            print(f"  network error {e!r}, retry in {delay}s", flush=True)
            _last = time.monotonic()
            time.sleep(delay); delay = min(delay * 2, 600)
            continue
        _last = time.monotonic()
        if status == 200 and body[:2] == b"\x1f\x8b":
            return gzip.decompress(body)
        if status == 404 and b"No results" in body[:200]:
            return b""
        if status == 429 or status >= 500:
            print(f"  HTTP {status}, backing off {delay}s", flush=True)
            time.sleep(delay); delay = min(delay * 2, 600)
            continue
        raise Blocked(f"HTTP {status} for {q}: {body[:200]!r}")
    raise Blocked(f"gave up after repeated 429/5xx/network errors for {q}")


def write(path, data):
    tmp = path + ".part"
    with gzip.open(tmp, "wb", compresslevel=6) as f:
        f.write(data)
    os.replace(tmp, path)


def months(start_year):
    today = datetime.date.today()
    for y in range(start_year, today.year + 1):
        for m in range(1, 13):
            if (y, m) > (today.year, today.month):
                return
            yield y, m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "raw", "lore"))
    ap.add_argument("--start-year", type=int, default=1991)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    today = datetime.date.today()
    prev = (today.replace(day=1) - datetime.timedelta(days=1))
    fresh = {(today.year, today.month), (prev.year, prev.month)}
    t0 = time.time(); reqs = 0; total = 0
    try:
        for y, m in months(a.start_year):
            name = f"all-{y}-{m:02d}"
            path = os.path.join(a.out, name + ".mbox.gz")
            split_marker = os.path.join(a.out, name + ".split")
            if os.path.exists(path) and valid_gzip(path) and (y, m) not in fresh:
                continue
            if os.path.exists(split_marker) and (y, m) not in fresh:
                weekly = [f for f in os.listdir(a.out) if f.startswith(name + "-w") and f.endswith(".mbox.gz")]
                if len(weekly) >= 4 and all(valid_gzip(os.path.join(a.out, f)) for f in weekly):
                    continue
            last = calendar.monthrange(y, m)[1]
            d1, d2 = datetime.date(y, m, 1), datetime.date(y, m, last)
            data = request(d1, d2); reqs += 1
            write(path, data)
            n = count_msgs(path); total += n
            print(f"{name}: {n} msgs, {len(data)} bytes", flush=True)
            if n >= SPLIT_AT:
                print(f"  {name} >= {SPLIT_AT}: also fetching weekly windows", flush=True)
                bounds = [(1, 7), (8, 14), (15, 21), (22, last)]
                for i, (a1, a2) in enumerate(bounds, 1):
                    wd = request(datetime.date(y, m, a1), datetime.date(y, m, a2)); reqs += 1
                    write(os.path.join(a.out, f"{name}-w{i}.mbox.gz"), wd)
                open(split_marker, "w").write("weekly files supplement the month file; normaliser dedupes\n")
    except Blocked as e:
        print(f"STOPPED (blocked or challenged?): {e}", file=sys.stderr)
        sys.exit(2)
    print(f"done: {reqs} requests, {total} msgs (this run), {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
