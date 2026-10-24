"""Merge raw + detail + webcheck into canggu_businesses.csv.

Usage:
    python -m mafa_scraper.merge_csv
Dedupe key: place URL. Bbox filter: lat/lng inside config.BBOX.
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mafa_scraper.config import (
    BBOX, CSV_OUT, DETAIL_JSONL, OUT_DIR, RAW_JSONL, WEB_JSONL, in_bbox,
)

COLUMNS = ["name", "categories", "lat", "lng", "address", "phone_gmaps",
           "website_gmaps", "website_status", "final_url", "emails",
           "emails_social", "emails_dork", "phones_all", "whatsapp_links",
           "has_website", "maps_url", "keyword_hit"]


def load_jsonl(path):
    recs = []
    if not os.path.exists(path):
        return recs
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                recs.append(json.loads(line))
            except ValueError:
                continue
    return recs


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    raws = load_jsonl(RAW_JSONL)
    details = {r.get("url"): r for r in load_jsonl(DETAIL_JSONL)}
    webs = {r.get("url"): r for r in load_jsonl(WEB_JSONL)}
    socials = {r.get("url"): r for r in load_jsonl(os.path.join(OUT_DIR, "socials.jsonl"))}
    dorks = {r.get("url"): r for r in load_jsonl(os.path.join(OUT_DIR, "dork.jsonl"))}

    merged = {}
    for r in raws:
        u = r.get("url")
        if not u or u in merged:
            if u in merged:
                # accumulate keyword hits
                prev = merged[u]["keyword_hit"]
                if r.get("keyword") and r["keyword"] not in prev.split("|"):
                    merged[u]["keyword_hit"] = prev + "|" + r["keyword"]
            continue
        d = details.get(u, {})
        w = webs.get(u, {})
        lat = d.get("lat", r.get("lat"))
        lng = d.get("lng", r.get("lng"))
        if lat is not None and lng is not None and not in_bbox(lat, lng):
            continue
        name = d.get("name") or r.get("name")
        emails = w.get("emails", [])
        phones = w.get("phones_all", [])
        wa = list(w.get("whatsapp_links", []))
        s = socials.get(u, {})
        se = s.get("emails_social", [])
        wa += [x for x in s.get("whatsapp_social", []) if x not in wa]
        de = dorks.get(u, {}).get("emails_dork", [])
        merged[u] = {
            "name": name,
            "categories": r.get("keyword", ""),
            "lat": lat, "lng": lng,
            "address": (d.get("panel_text") or "")[:300].replace("\n", " | "),
            "phone_gmaps": d.get("phone_gmaps") or "",
            "website_gmaps": d.get("website_gmaps") or "",
            "website_status": w.get("website_status", ""),
            "final_url": w.get("final_url", ""),
            "emails": ";".join(emails),
            "emails_social": ";".join(se),
            "emails_dork": ";".join(de),
            "phones_all": ";".join(phones),
            "whatsapp_links": ";".join(wa),
            "has_website": bool((d.get("website_gmaps")) or w.get("has_website")),
            "maps_url": u,
            "keyword_hit": r.get("keyword", ""),
        }

    with open(CSV_OUT, "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=COLUMNS)
        wr.writeheader()
        for v in merged.values():
            wr.writerow(v)
    print(f"rows={len(merged)} bbox={BBOX} -> {CSV_OUT}")


if __name__ == "__main__":
    main()
