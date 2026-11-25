#!/usr/bin/env python3
"""Normalise Linus Torvalds' commits from raw/git/<name>.git into docs/git.jsonl.

Read-only git log against bare clones (no hooks, no checkouts). Python stdlib only.

Kinds:
  commit  non-merge commit authored by Linus (name match or torvalds@ address), full message
  commit  non-merge commit by someone else, committed by Linus, with a bracketed note by him
  merge   merge commit authored by Linus whose message holds text he wrote (see own_merge_text)
Stats go to logs/git_stats.json; merge samples to logs/merge_samples.json.
"""
import json, re, subprocess, sys, random, collections, datetime, os, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPOS = {  # name -> commit url template
    "linux": "https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id={}",
    "history": "https://git.kernel.org/pub/scm/linux/kernel/git/tglx/history.git/commit/?id={}",
    "git": "https://git.kernel.org/pub/scm/git/git.git/commit/?id={}",
    "sparse": "https://git.kernel.org/pub/scm/devel/sparse/sparse.git/commit/?id={}",
    "subsurface": "https://github.com/subsurface/subsurface/commit/{}",
}
FMT = "%H%x1f%P%x1f%an%x1f%ae%x1f%aI%x1f%cn%x1f%ce%x1f%B%x00"


def is_linus_author(name, email):
    return name.strip() == "Linus Torvalds" or email.lower().startswith("torvalds@")


def is_linus_committer(name, email):
    return name.strip() == "Linus Torvalds" or email.lower().startswith("torvalds@")


def to_utc(iso):
    d = datetime.datetime.fromisoformat(iso)
    return d.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def records(repo_dir, extra):
    p = subprocess.Popen(["git", "-C", repo_dir, "-c", "core.quotepath=off", "log", "--all", "-z",
                          "--format=" + FMT] + extra, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    buf = b""
    while True:
        chunk = p.stdout.read(1 << 20)
        if not chunk:
            break
        buf += chunk
        parts = buf.split(b"\0")
        buf = parts.pop()
        for r in parts:
            if r.strip():
                yield r.decode("utf-8", "replace")
    if buf.strip():
        yield buf.decode("utf-8", "replace")
    p.wait()


# ---- bracketed note by Linus in someone else's commit -------------------------------------
NOTE_RE = re.compile(r"\[\s*(?:Linus\b[^\]]*|[^\]\[]*?(?:[-–—]|--)\s*Linus\s*|torvalds\s*:[^\]]*)\]", re.S | re.I)
NOTE_FIRSTPERSON = re.compile(r"\[\s*(?:Linus|torvalds)\s*[:,]", re.I)


def has_linus_note(body):
    for m in NOTE_RE.finditer(body):
        s = m.group(0)
        if NOTE_FIRSTPERSON.match(s) or re.search(r"[-–—]\s*Linus\s*\]$", s, re.I):
            return True
    return False


# ---- merge heuristic -----------------------------------------------------------------------
HEADER_RE = re.compile(r"^(Merge\b.*|Automatic merge of .*|Pull\b.*?(?:from|into)\b.*|Merging\b.*)$", re.I)
PULL_LINE = re.compile(r"^(Pull .+ from .+:?|Pull .+:)$")
TAGSTART = re.compile(r"^\* (tag|branch) '|^\* (\S+ )?[\w./-]+: |^(Linus Torvalds|[A-Z][^\n]{2,40}) \(\d+\):$|^Changes since |^(for-linus|git://|http)")
SHORTLOG = re.compile(r"^(\*\s|\s{2,}\S|[A-Z][\w .'-]+ \(\d+\):$|\S.* \(\d+ commits?\)|.* \| +\d+ [+-]*$|\d+ files? changed)")
SKIP_LINES = re.compile(r"^(Signed-off-by:|Acked-by:|Reviewed-by:|Conflicts?:|# gpg:|# Primary key|# Good signature|# WARNING|#\s+)", re.I)


def own_merge_text(msg):
    """Return the text Linus (probably) wrote in a merge message, or ''.

    Drop: subject line, the 'Pull X from Y:' line, the pasted maintainer tag message (everything
    after it up to the '* tag/branch' shortlog block) and the shortlog/diffstat. Maintainer text
    pasted by git is plain paragraphs, so we cannot separate it from Linus' text by form alone;
    we keep only text that carries a first-person/maintainer-voice signal from Linus:
      - a paragraph before the pull header or conflict note, or
      - a paragraph containing 'I ' first person, 'Conflict', 'merge resolution', 'I fixed up', etc.
    """
    paras = re.split(r"\n\s*\n", msg.strip("\n"))
    if len(paras) < 2:
        return ""
    body = paras[1:]  # drop subject paragraph
    kept = []
    for p in body:
        lines = p.split("\n")
        first = lines[0].strip()
        if PULL_LINE.match(first) or HEADER_RE.match(first):
            continue
        if re.match(r"^\d+\) ", first):  # davem-style numbered pull summary
            continue
        if TAGSTART.match(first) or SHORTLOG.match(first):
            continue
        if all(SKIP_LINES.match(l) or not l.strip() for l in lines):
            continue
        if re.match(r"^\s*(Signed-off-by|Acked-by|Reviewed-by|Tested-by|Cc):", p):
            continue
        kept.append(p)
    # Linus signals: first person singular or merge resolution talk, and not within a pasted block.
    sig = re.compile(r"(?<![A-Za-z/])(I|I'm|I've|I'll|I'd|my|me)(?![A-Za-z/_-])|[Cc]onflicts?|merge (resolution|fixup)|[Ff]ixed up|[Mm]anual(ly)? (merge|fix)|[Rr]esolved|[-–—]\s*Linus\.?\s*[)\]]?\s*$|^\[ .*\]\s*$", re.S | re.M)
    return "\n\n".join(p for p in kept if sig.search(p) and not p.startswith(" ")).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repos", nargs="*", default=list(REPOS))
    ap.add_argument("--out", default=os.path.join(ROOT, "docs", "git.jsonl"))
    ap.add_argument("--seed", type=int, default=20261125)
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    stats, samples = {}, {}
    rng = random.Random(a.seed)
    seen = set()
    with open(a.out, "w", encoding="utf-8") as out:
        for name in a.repos:
            rd = os.path.join(ROOT, "raw", "git", name + ".git")
            if not os.path.isdir(rd):
                print("missing", rd, file=sys.stderr); continue
            st = collections.Counter(); emails = collections.Counter(); dates = []
            kept_m, drop_m = [], []
            st["total_commits"] = int(subprocess.check_output(["git", "-C", rd, "rev-list", "--all", "--count"]))
            # pass 1: everything authored by Linus; pass 2: everything committed by Linus
            for extra in (["--author=Torvalds"], ["--committer=Torvalds", "--no-merges"]):
                for r in records(rd, extra):
                    f = r.split("\x1f", 7)
                    if len(f) < 8: continue
                    sha, parents, an, ae, adate, cn, ce, msg = f
                    if sha in seen: continue
                    msg = msg.rstrip() 
                    merge = len(parents.split()) > 1
                    la = is_linus_author(an, ae)
                    if la:
                        emails[ae.lower()] += 1
                        if merge:
                            st["merges_total"] += 1
                            txt = own_merge_text(msg)
                            if not txt:
                                st["merges_dropped"] += 1; drop_m.append(sha); continue
                            st["merges_kept"] += 1; kept_m.append(sha); kind = "merge"; msg = msg.split("\n", 1)[0] + "\n\n" + txt
                        else:
                            st["authored_commits"] += 1; kind = "commit"
                    elif is_linus_committer(cn, ce) and not merge and has_linus_note(msg):
                        st["committed_with_note"] += 1; kind = "commit"
                    else:
                        continue
                    seen.add(sha)
                    d = to_utc(adate); dates.append(d)
                    title = msg.split("\n", 1)[0]
                    out.write(json.dumps({"id": sha, "source": "git", "kind": kind, "date": d, "title": title,
                                          "url": REPOS[name].format(sha), "venue": name, "in_reply_to": None,
                                          "body": msg, "reviews_code": False}, ensure_ascii=False) + "\n")
            st["date_min"], st["date_max"] = (min(dates), max(dates)) if dates else (None, None)
            st["author_emails"] = dict(emails.most_common())
            stats[name] = dict(st)
            samples[name] = {"kept": rng.sample(kept_m, min(10, len(kept_m))), "dropped": rng.sample(drop_m, min(10, len(drop_m)))}
            print(name, dict(st), file=sys.stderr)
    with open(os.path.join(ROOT, "logs", "git_stats.json"), "w") as f: json.dump(stats, f, indent=1)
    with open(os.path.join(ROOT, "logs", "merge_samples.json"), "w") as f: json.dump(samples, f, indent=1)


if __name__ == "__main__":
    main()
