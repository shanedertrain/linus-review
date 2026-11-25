#!/usr/bin/env python3
"""Build corpus.db from every docs/*.jsonl present. Rebuilt from scratch each run. Standard library only."""
import glob, json, os, sqlite3, sys, time

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FIELDS = ["id", "source", "kind", "date", "title", "url", "venue", "in_reply_to", "body", "reviews_code"]


def main():
    db_path = os.path.join(ROOT, "corpus.db")
    tmp = db_path + ".tmp"
    for p in (tmp, tmp + "-wal", tmp + "-shm"):
        if os.path.exists(p):
            os.remove(p)
    con = sqlite3.connect(tmp)
    con.executescript("""
    PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;
    CREATE TABLE docs(
      rowid INTEGER PRIMARY KEY,
      id TEXT NOT NULL UNIQUE, source TEXT NOT NULL, kind TEXT NOT NULL, date TEXT, title TEXT,
      url TEXT, venue TEXT, in_reply_to TEXT, body TEXT, reviews_code INTEGER NOT NULL DEFAULT 0);
    CREATE VIRTUAL TABLE docs_fts USING fts5(title, body, content='docs', content_rowid='rowid',
      tokenize='porter unicode61');
    """)
    t0 = time.time(); per_file = {}; bad = 0; dupes = 0; missing = 0
    for path in sorted(glob.glob(os.path.join(ROOT, "docs", "*.jsonl"))):
        n = 0
        with open(path, encoding="utf-8", errors="replace") as f:
            for ln, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    d = json.loads(line)
                    if not d.get("id") or not d.get("source") or not d.get("kind"):
                        raise ValueError("missing id/source/kind")
                except Exception as e:
                    bad += 1
                    print(f"skip {os.path.basename(path)}:{ln}: {e}", file=sys.stderr)
                    continue
                row = [d.get(k) for k in FIELDS]
                row[9] = 1 if d.get("reviews_code") else 0
                for i in (3, 4, 5, 6, 7, 8):
                    if row[i] is not None and not isinstance(row[i], str):
                        row[i] = str(row[i])
                if row[8] is None: row[8] = ""
                try:
                    con.execute("INSERT INTO docs(id,source,kind,date,title,url,venue,in_reply_to,body,reviews_code) VALUES(?,?,?,?,?,?,?,?,?,?)", row)
                    n += 1
                except sqlite3.IntegrityError:
                    dupes += 1
        per_file[os.path.basename(path)] = n
    con.execute("INSERT INTO docs_fts(rowid,title,body) SELECT rowid,coalesce(title,''),coalesce(body,'') FROM docs")
    con.executescript("""
    CREATE INDEX docs_date ON docs(date); CREATE INDEX docs_source ON docs(source);
    CREATE INDEX docs_kind ON docs(kind); CREATE INDEX docs_reviews ON docs(reviews_code);
    INSERT INTO docs_fts(docs_fts) VALUES('optimize');
    """)
    con.commit(); con.close()
    os.replace(tmp, db_path)
    print(f"corpus.db built in {time.time()-t0:.0f}s: {per_file}; bad lines {bad}; duplicate ids skipped {dupes}")


if __name__ == "__main__":
    main()
