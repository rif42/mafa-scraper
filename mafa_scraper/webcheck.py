"""Check each website, extract emails/phones/whatsapp links. Stdlib HTTP.

Usage:
    python -m mafa_scraper.webcheck [--limit N]
Reads DETAIL_JSONL, writes WEB_JSONL keyed by url. Resumable.
"""
import argparse
import html
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mafa_scraper.config import DETAIL_JSONL, OUT_DIR, UA, WEB_JSONL

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+62|\(\d{3,4}\)|0\d{2,4})[\s\-.]?\d{3,4}[\s\-.]?\d{3,5}")
WA_RE = re.compile(r"https?://(?:wa\.me|api\.whatsapp\.com|chat\.whatsapp\.com)/[^\s\"'<>]+", re.I)


def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            final = r.geturl()
            status = r.status
            raw = r.read(1_500_000)
            ctype = r.headers.get("Content-Type", "")
    except Exception as e:
        return {"website_status": f"error:{type(e).__name__}", "final_url": url,
                "emails": [], "phones_all": [], "whatsapp_links": [], "has_website": False}
    try:
        text = raw.decode("utf-8", errors="replace")
    except Exception:
        text = ""
    text = html.unescape(text)
    emails = sorted(set(EMAIL_RE.findall(text)))[:20]
    phones = sorted(set(p.strip() for p in PHONE_RE.findall(text)))[:20]
    wa = sorted(set(WA_RE.findall(text)))[:20]
    ok = 200 <= status < 400
    return {"website_status": status, "final_url": final, "content_type": ctype[:80],
            "emails": emails, "phones_all": phones, "whatsapp_links": wa,
            "has_website": ok}


def load_detail():
    recs = []
    if not os.path.exists(DETAIL_JSONL):
        return recs
    with open(DETAIL_JSONL, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                recs.append(json.loads(line))
            except ValueError:
                continue
    return recs


def load_done():
    done = set()
    if not os.path.exists(WEB_JSONL):
        return done
    with open(WEB_JSONL, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                done.add(json.loads(line).get("url"))
            except ValueError:
                continue
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)
    recs = load_detail()
    done = load_done()
    todo = [r for r in recs if r.get("url") not in done and r.get("website_gmaps")]
    if args.limit:
        todo = todo[:args.limit]
    print(f"webcheck: {len(recs)} detail, {len(done)} done, {len(todo)} todo (with website)")
    fw = open(WEB_JSONL, "a", encoding="utf-8")
    try:
        for i, r in enumerate(todo):
            out = fetch(r["website_gmaps"])
            out["url"] = r["url"]
            fw.write(json.dumps(out, ensure_ascii=False) + "\n")
            if i % 25 == 0:
                print(f"webcheck {i}/{len(todo)}", flush=True)
    finally:
        fw.close()
    print(f"DONE -> {WEB_JSONL}")


if __name__ == "__main__":
    main()
