"""Pass over social links (Instagram/Facebook/TikTok) from detail rows.

Extracts mailto: + email addresses + whatsapp links from public bio/about pages.
Instagram without login often returns a login wall -> recorded as limited.

Usage:
    python -m mafa_scraper.socials [--limit N] [--only-no-website]
Resumable: skips urls already in SOCIAL_JSONL.
"""
import argparse
import asyncio
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mafa_scraper.config import DETAIL_JSONL, OUT_DIR, UA

SOCIAL_JSONL = os.path.join(OUT_DIR, "socials.jsonl")
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
WA_RE = re.compile(r"https?://(?:wa\.me|api\.whatsapp\.com|chat\.whatsapp\.com)/[^\s\"'<>]+", re.I)

SOCIAL_DOMAINS = ("instagram.com", "facebook.com", "fb.com", "tiktok.com")

SOCIAL_JS = """() => {
  const mailtos = [...document.querySelectorAll('a[href^="mailto:"]')].map(a => a.getAttribute("href").slice(7).split("?")[0]);
  const text = (document.body ? document.body.innerText : "").slice(0, 20000);
  const bio = document.querySelector('meta[property="og:description"]');
  const wa = [...document.querySelectorAll('a[href]')].map(a => a.href)
    .filter(h => /wa\\.me|whatsapp\\.com/.test(h)).slice(0, 10);
  const loginWall = /log in|login.*continue|cookies/i.test(document.title || "") && (document.body ? document.body.innerText.length : 0) < 500;
  return {mailtos, text, bio: bio ? bio.getAttribute("content") : "", wa, loginWall, title: document.title || ""};
}"""


def social_links(rec):
    out = []
    for h in (rec.get("site_links") or []) + ([rec.get("website_gmaps")] if rec.get("website_gmaps") else []):
        if h and any(d in h for d in SOCIAL_DOMAINS):
            if h not in out:
                out.append(h)
    return out


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
    if os.path.exists(SOCIAL_JSONL):
        with open(SOCIAL_JSONL, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    done.add(json.loads(line).get("url"))
                except ValueError:
                    continue
    todo = []
    for r in recs:
        if r.get("url") in done or not social_links(r):
            continue
        if only_no_website:
            site = r.get("website_gmaps") or ""
            if site and not any(d in site for d in SOCIAL_DOMAINS):
                continue
        todo.append(r)
    return todo


async def run(limit=None, only_no_website=True, headless=True):
    from playwright.async_api import async_playwright

    os.makedirs(OUT_DIR, exist_ok=True)
    todo = load_todo(only_no_website)
    if limit:
        todo = todo[:limit]
    print(f"socials: {len(todo)} todo (only_no_website={only_no_website})")
    fw = open(SOCIAL_JSONL, "a", encoding="utf-8")
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=headless)
            ctx = await browser.new_context(user_agent=UA, locale="en-US")
            page = await ctx.new_page()
            for i, r in enumerate(todo):
                emails, wa, notes = set(), set(), []
                for s in social_links(r)[:3]:
                    try:
                        await page.goto(s, wait_until="domcontentloaded", timeout=45000)
                        await page.wait_for_timeout(3000)
                        d = await page.evaluate(SOCIAL_JS)
                    except Exception as e:
                        notes.append(f"{s} -> error:{type(e).__name__}")
                        continue
                    for m in d.get("mailtos", []):
                        if "@" in m:
                            emails.add(m.strip())
                    blob = (d.get("text") or "") + "\n" + (d.get("bio") or "")
                    for m in EMAIL_RE.findall(blob):
                        emails.add(m)
                    for w in d.get("wa", []):
                        wa.add(w)
                    if d.get("loginWall"):
                        notes.append(f"{s} -> login-wall(limited)")
                    await page.wait_for_timeout(2000)
                fw.write(json.dumps({"url": r["url"], "name": r.get("name"),
                                     "emails_social": sorted(emails)[:20],
                                     "whatsapp_social": sorted(wa)[:20],
                                     "notes": notes}, ensure_ascii=False) + "\n")
                if i % 25 == 0:
                    print(f"socials {i}/{len(todo)}", flush=True)
            await browser.close()
    finally:
        fw.close()
    print(f"DONE -> {SOCIAL_JSONL}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--only-no-website", action="store_true", default=True)
    ap.add_argument("--all", dest="only_no_website", action="store_false")
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    asyncio.run(run(limit=args.limit, only_no_website=args.only_no_website,
                    headless=not args.headed))


if __name__ == "__main__":
    main()
