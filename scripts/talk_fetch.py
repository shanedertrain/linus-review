#!/usr/bin/env python3
"""Talks and conversations with Linus Torvalds that have public captions on YouTube.

Uses the already-installed yt-dlp (no download of media: --skip-download; captions and info json only).
Manual captions are preferred over auto-captions. Speakers are NOT marked in YouTube captions; each document
starts with a header line naming the event, the other speaker(s) and the caption type, so downstream use can
tell. Output: raw/talk/<id>.{info.json,en.json3}, docs/talk.jsonl.  Resumable.
"""
import glob, json, os, re, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

RAW = os.path.join(ROOT, "raw", "talk"); os.makedirs(RAW, exist_ok=True)
# id, event, other speaker(s)
TALKS = [
 ("4XpnKHJAok8", "Google Tech Talk: Linus Torvalds on git (2007-05-03)", "audience Q&A"),
 ("o8NPllzkFhE", "TED 2016: The mind behind Linux", "Chris Anderson"),
 ("5PmHRSeA2c8", "DebConf 14 Q&A with Linus Torvalds (2014)", "Q&A with audience, moderator"),
 ("MShbP3OpASA", "Aalto University talk with Linus Torvalds (2012)", "Q&A with audience, moderator"),
 ("bAop_8l6_cI", "linux.conf.au 2015 keynote (Auckland)", "Q&A with audience"),
 ("5vPAHS11fq4", "LinuxCon Japan 2017: Linus Torvalds and Greg Kroah-Hartman, 20 years of Linux", "Greg Kroah-Hartman"),
 ("mfv0V1SxbNA", "Linus Tech Tips: Building the perfect Linux PC with Linus Torvalds", "Linus Sebastian"),
 ("s4wlrxFf2lM", "TFiR interview: Linus Torvalds on the kernel, GenAI, EVs, programming languages", "interviewer"),
 ("1giMBbPJKhk", "TFiR: 45 minutes with Linus Torvalds", "interviewer"),
 ("mysM-V5h9z8", "TFiR: Linus Torvalds on the future of desktop Linux", "interviewer"),
 ("YKkEe-PxW10", "Linux Foundation keynote conversation", "Dirk Hohndel"),
 ("OM_8UOPFpqE", "Linux Foundation keynote conversation", "Dirk Hohndel"),
 ("0PSA2LFFlvk", "Linux Foundation keynote conversation", "Dirk Hohndel"),
 ("fi29pfLcW4I", "Linux Foundation keynote conversation", "Dirk Hohndel"),
 ("OvuEYtkOH88", "Linux Foundation keynote conversation", "Dirk Hohndel"),
 ("H8Gd9t7FQqI", "Linux Foundation keynote conversation", "Dirk Hohndel"),
 ("tWx769t1JKg", "Linux Foundation keynote conversation", "Dirk Hohndel"),
 ("cPvRIWXNgaM", "Linux Foundation keynote conversation", "Dirk Hohndel"),
 ("sLimmpZWRNI", "Linux Foundation keynote conversation", "Dirk Hohndel"),
 ("XB550IYYG-w", "Linux Foundation keynote conversation", "Dirk Hohndel"),
 ("PVDsnK_8QdQ", "Linux Foundation keynote conversation", "Dirk Hohndel"),
 ("yEzdHYjY_RU", "Linux Foundation keynote conversation", "Dirk Hohndel"),
 ("NLQZzEvavGs", "Linux Foundation keynote conversation", "Dirk Hohndel"),
 ("N3m6XbK_a_w", "Open Source Summit Japan 2023 keynote conversation (third-party upload)", "Dirk Hohndel"),
]
UA = "linus-corpus-research/0.1 (personal research archive)"


def fetch_one(vid):
    if glob.glob(os.path.join(RAW, vid + ".en*.json3")) and os.path.exists(os.path.join(RAW, vid + ".info.json")): return True
    cmd = ["yt-dlp", "--no-update", "--skip-download", "--write-subs", "--write-auto-subs", "--sub-langs", "en,en-orig",
           "--sub-format", "json3", "--write-info-json", "--user-agent", UA, "-o", os.path.join(RAW, "%(id)s"),
           "https://www.youtube.com/watch?v=" + vid]
    r = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=300)
    ok = bool(glob.glob(os.path.join(RAW, vid + ".en*.json3"))) and os.path.exists(os.path.join(RAW, vid + ".info.json"))
    if not ok: log_fail("talk", vid, (r.stderr or r.stdout)[-300:].replace("\n", " "))
    time.sleep(30)
    return ok


def captions(vid):
    fs = sorted(glob.glob(os.path.join(RAW, vid + ".en*.json3")))
    # manual subtitles are written as <id>.en.json3, auto as <id>.en-orig.json3 or en.json3 (auto)
    info = json.load(open(os.path.join(RAW, vid + ".info.json")))
    manual = "en" in (info.get("subtitles") or {}) or any(k.startswith("en") for k in (info.get("subtitles") or {}))
    f = fs[0]
    ev = json.load(open(f))["events"]
    out, buf, last_end = [], [], 0
    for e in ev:
        if "segs" not in e: continue
        t = "".join(s.get("utf8", "") for s in e["segs"]).replace("\n", " ")
        if not t.strip(): continue
        start = e.get("tStartMs", 0)
        if buf and start - last_end > 2500:
            out.append(" ".join(buf)); buf = []
        buf.append(t.strip())
        last_end = start + e.get("dDurationMs", 0)
    if buf: out.append(" ".join(buf))
    text = "\n\n".join(re.sub(r"\s+", " ", p).strip() for p in out)
    return text, manual, info


def main():
    docs = []
    for vid, ev, other in TALKS:
        if not fetch_one(vid): print("FAILED", vid); continue
        text, manual, info = captions(vid)
        ud = info.get("upload_date", "")
        date = "%s-%s-%s" % (ud[:4], ud[4:6], ud[6:8]) if ud else ""
        head = "[%s. Speakers: Linus Torvalds and %s. YouTube %s captions: speaker turns are not marked.]" % (ev, other, "manual" if manual else "automatic")
        url = "https://www.youtube.com/watch?v=" + vid
        docs.append(dict(id=url, source="talk", kind="transcript", date=date, title=info.get("title", ev), url=url,
                         venue=info.get("channel", "YouTube") + " / " + ev, in_reply_to=None, body=head + "\n\n" + text, reviews_code=False))
        print(vid, date, len(text), "manual" if manual else "auto", info.get("title"), flush=True)
    print("talk docs:", write_jsonl(os.path.join(ROOT, "docs", "talk.jsonl"), docs))


if __name__ == "__main__":
    main()
