"""Google Maps keyword x grid-cell search. Appends cards to gmaps_raw.jsonl.

Usage:
    python -m mafa_scraper.search
    python -m mafa_scraper.search --keyword cafe --max-cells 1
Resumable: skips (keyword, cell) pairs already present in RAW_JSONL.
"""
import argparse
import asyncio
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mafa_scraper.config import KEYWORDS, OUT_DIR, RAW_JSONL, UA
from mafa_scraper.grid import cells

CARD_JS = """() => {
  const feed = document.querySelector('div[role="feed"]');
  if (!feed) return [];
  const links = [...feed.querySelectorAll('a[href*="/maps/place/"]')];
  const seen = new Map();
  for (const a of links) {
    const href = a.href;
    const label = (a.getAttribute("aria-label") || a.innerText || "").trim();
    if (!label || seen.has(href)) continue;
    let lat = null, lng = null;
    let m = href.match(/!3d(-?\\d+\\.\\d+)!4d(-?\\d+\\.\\d+)/) || href.match(/@(-?\\d+\\.\\d+),(-?\\d+\\.\\d+)/);
    if (m) { lat = parseFloat(m[1]); lng = parseFloat(m[2]); }
    seen.set(href, {name: label, url: href, lat, lng});
  }
  return [...seen.values()];
}"""


def load_done(path):
    done = set()
    if not os.path.exists(path):
        return done
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                o = json.loads(line)
                done.add((o.get("keyword"), o.get("cell_lat"), o.get("cell_lng"), o.get("url")))
            except ValueError:
                continue
    return done


async def run(keywords, cell_list, headless=True):
    from playwright.async_api import async_playwright

    os.makedirs(OUT_DIR, exist_ok=True)
    done = load_done(RAW_JSONL)
    fw = open(RAW_JSONL, "a", encoding="utf-8")
    total_new = 0
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=headless)
            ctx = await browser.new_context(user_agent=UA, locale="en-US")
            page = await ctx.new_page()
            for kw in keywords:
                for (clat, clng) in cell_list:
                    q = urllib.parse.quote(kw)
                    url = f"https://www.google.com/maps/search/{q}/@{clat},{clng},14z"
                    try:
                        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    except Exception as e:
                        print(f"SKIP goto fail {kw} {clat},{clng}: {e}", flush=True)
                        continue
                    await page.wait_for_timeout(4000)
                    # scroll feed to load more
                    for _ in range(10):
                        has_feed = await page.evaluate(
                            "() => !!document.querySelector('div[role=\"feed\"]')")
                        if not has_feed:
                            break
                        await page.evaluate(
                            "() => { const f = document.querySelector('div[role=\"feed\"]'); if (f) f.scrollBy(0, 900); }")
                        await page.wait_for_timeout(1200)
                    try:
                        cards = await page.evaluate(CARD_JS)
                    except Exception as e:
                        print(f"SKIP extract fail {kw} {clat},{clng}: {e}", flush=True)
                        continue
                    n = 0
                    for c in cards:
                        key = (kw, clat, clng, c["url"])
                        if key in done:
                            continue
                        rec = {"keyword": kw, "cell_lat": clat, "cell_lng": clng,
                               "name": c["name"], "url": c["url"],
                               "lat": c["lat"], "lng": c["lng"]}
                        fw.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        done.add(key)
                        n += 1
                    total_new += n
                    print(f"{kw} @ {clat},{clng}: {len(cards)} cards, +{n} new", flush=True)
            await browser.close()
    finally:
        fw.close()
    print(f"DONE +{total_new} records -> {RAW_JSONL}")
    return total_new


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keyword", default=None)
    ap.add_argument("--max-cells", type=int, default=None)
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    kws = [args.keyword] if args.keyword else KEYWORDS
    cl = cells()
    if args.max_cells:
        cl = cl[:args.max_cells]
    asyncio.run(run(kws, cl, headless=not args.headed))


if __name__ == "__main__":
    main()
