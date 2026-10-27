"""Search-dork pass: Bing HTML for '<name> Canggu email/gmail/kontak'.

No API key. Stdlib HTTP + regex on result snippets.
Polite (3s delay), resumable, writes DORK_JSONL keyed by url.

Usage:
    python -m mafa_scraper.dork [--limit N] [--only-no-website]
"""
import argparse
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mafa_scraper.config import DETAIL_JSONL, OUT_DIR, UA

DORK_JSONL = os.path.join(OUT_DIR, "dork.jsonl")
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
TAG_RE = re.compile(r"<[^>]+>")


def bing_search(query, timeout=20):
    url = "https://www.bing.com/search?q=" + urllib.parse.quote(query) + "&count=10"
    req = urllib.request.Request(url, headers={"User-Agent": UA,
        "Accept-Language": "en-US,en;q=0.9,id;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(1_000_000).decode("utf-8", errors="replace")
    except Exception as e:
        return f"ERROR:{type(e).__name__}"


def load_todo(only_no_website):
    recs = []
    if os.path.exists(DETAIL_JSONL):
        with open(DETAIL_JSONL, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    recs.append(json.loads(line))
                except ValueError:
                    continue
    done = set()
    if os.path.exists(DORK_JSONL):
        with open(DORK_JSONL, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    done.add(json.loads(line).get("url"))
                except ValueError:
                    continue
    todo = [r for r in recs
            if r.get("url") not in done
            and (not only_no_website or not r.get("website_gmaps"))]
    return todo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--only-no-website", action="store_true", default=True)
    ap.add_argument("--all", dest="only_no_website", action="store_false")
    args = ap.parse_args()
    todo = load_todo(args.only_no_website)
    if args.limit:
        todo = todo[:args.limit]
    print(f"dork: {len(todo)} todo (only_no_website={args.only_no_website})")
    os.makedirs(OUT_DIR, exist_ok=True)
    fw = open(DORK_JSONL, "a", encoding="utf-8")
    try:
        for i, r in enumerate(todo):
            name = (r.get("name") or "").strip()
            query = f'"{name}" Canggu email OR gmail OR kontak'
            page = bing_search(query)
            if page.startswith("ERROR:"):
                out = {"url": r["url"], "name": name, "query": query,
                       "emails_dork": [], "note": page}
            else:
                text = html.unescape(TAG_RE.sub(" ", page))
                emails = sorted(set(EMAIL_RE.findall(text)))
                # drop bing/msn noise
                emails = [e for e in emails if not e.lower().endswith(
                    ("@microsoft.com", "@bing.com", "@live.com"))][:20]
                out = {"url": r["url"], "name": name, "query": query,
                       "emails_dork": emails}
            fw.write(json.dumps(out, ensure_ascii=False) + "\n")
            if i % 25 == 0:
                print(f"dork {i}/{len(todo)}", flush=True)
            time.sleep(3)
    finally:
        fw.close()
    print(f"DONE -> {DORK_JSONL}")


if __name__ == "__main__":
    main()
