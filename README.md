# mafa-scraper — Canggu business scraper (Google Maps → CSV)

Full-code scraper. No paid APIs. Stdlib + Playwright. All stages
append-only JSONL and resumable.

Requires: Python 3.10+, `pip install playwright`, `playwright install chromium`.

## Quick start

```powershell
python -m mafa_scraper.search --keyword cafe --max-cells 1
python -m mafa_scraper.detail --limit 10
python -m mafa_scraper.webcheck --limit 10
python -m mafa_scraper.merge_csv
```

## Full run

```powershell
python -m mafa_scraper.search
python -m mafa_scraper.detail
python -m mafa_scraper.webcheck
python -m mafa_scraper.socials
python -m mafa_scraper.dork
python -m mafa_scraper.merge_csv
```

Outputs in `out/`: `gmaps_raw.jsonl`, `gmaps_detail.jsonl`,
`webcheck.jsonl`, `socials.jsonl`, `dork.jsonl`, `canggu_businesses.csv`.

See `Canggu Scraper Docs.md` for the end-to-end design.
