"""Visit each raw place URL, extract phone/website/address/category.

Usage:
    python -m mafa_scraper.detail [--limit N]
Resumable: skips urls already in DETAIL_JSONL.
"""
import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mafa_scraper.config import DETAIL_JSONL, OUT_DIR, RAW_JSONL, UA

DETAIL_JS = """() => {
  const main = document.querySelector('div[role="main"]');
  const text = main ? main.innerText : document.body.innerText;
  const tel = [...document.querySelectorAll('a[href^="tel:"]')].map(a => a.getAttribute("href").slice(4));
  const all = [...document.querySelectorAll('a[href]')].map(a => a.href);
  const site = all.filter(h => h && !h.includes("google.") && !h.includes("g.page") && h.startsWith("http")).slice(0, 10);
  const h1 = document.querySelector("h1");
  return {name: h1 ? h1.innerText : "", text: (text || "").slice(0, 3000), tel, site};
}"""


def load_urls():
    urls = {}
    if not os.path.exists(RAW_JSONL):
        return urls
    with open(RAW_JSONL, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            u = o.get("url")
            if u and u not in urls:
                urls[u] = o
    return urls


def load_done():
    done = set()
    if not os.path.exists(DETAIL_JSONL):
        return done
    with open(DETAIL_JSONL, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                done.add(json.loads(line).get("url"))
            except ValueError:
                continue
    return done


async def run(limit=None, headless=True):
    from playwright.async_api import async_playwright

    os.makedirs(OUT_DIR, exist_ok=True)
    urls = load_urls()
    done = load_done()
    todo = [u for u in urls if u not in done]
    if limit:
        todo = todo[:limit]
    print(f"detail: {len(urls)} known, {len(done)} done, {len(todo)} todo")
    fw = open(DETAIL_JSONL, "a", encoding="utf-8")
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=headless)
            ctx = await browser.new_context(user_agent=UA, locale="en-US")
            page = await ctx.new_page()
            for i, u in enumerate(todo):
                base = urls[u]
                try:
                    await page.goto(u, wait_until="domcontentloaded", timeout=60000)
                    await page.wait_for_timeout(3500)
                    d = await page.evaluate(DETAIL_JS)
                except Exception as e:
                    print(f"FAIL {i} {e}", flush=True)
                    rec = {"url": u, "name": base.get("name"), "lat": base.get("lat"),
                           "lng": base.get("lng"), "keyword": base.get("keyword"), "error": str(e)[:200]}
                    fw.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    continue
                rec = {"url": u, "name": d.get("name") or base.get("name"),
                       "lat": base.get("lat"), "lng": base.get("lng"),
                       "keyword": base.get("keyword"), "phone_gmaps": (d.get("tel") or [None])[0],
                       "alt_phones": d.get("tel"), "website_gmaps": (d.get("site") or [None])[0],
                       "site_links": d.get("site"), "panel_text": d.get("text")}
                fw.write(json.dumps(rec, ensure_ascii=False) + "\n")
                if i % 25 == 0:
                    print(f"detail {i}/{len(todo)}", flush=True)
                await page.wait_for_timeout(2000)
            await browser.close()
    finally:
        fw.close()
    print(f"DONE -> {DETAIL_JSONL}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    asyncio.run(run(limit=args.limit, headless=not args.headed))


if __name__ == "__main__":
    main()
