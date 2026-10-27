# mafa-scraper — Canggu business scraper (Google Maps → CSV)

Full-code scraper. No paid APIs. Stdlib + Playwright. All stages
append-only JSONL and resumable.

## Installation

Prerequisites: Python 3.10+, git.

```powershell
git clone https://github.com/rif42/mafa-scraper.git
cd mafa-scraper
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install playwright
playwright install chromium
```

`playwright` is the only third-party dependency; everything else is
stdlib. Set `CANGGU_OUT` to override the output directory
(default `out/`).

## Usage

Single command (runs all six stages in order, stops on first failure):

```powershell
python -m mafa_scraper.run --limit 10 --keyword cafe --max-cells 1  # smoke test
python -m mafa_scraper.run                                          # full run
python -m mafa_scraper.run --from webcheck --skip dork               # resume, skip dork
python -m mafa_scraper.run --dry-run                                 # print plan only
```

Per-stage (same commands the driver runs):

Smoke test (1 search + 10 details, ~2 min):

```powershell
python -m mafa_scraper.search --keyword cafe --max-cells 1
python -m mafa_scraper.detail --limit 10
python -m mafa_scraper.webcheck --limit 10
python -m mafa_scraper.merge_csv
```

Full run (180 searches, ~70 min + ~6 s/detail page):

```powershell
python -m mafa_scraper.search
python -m mafa_scraper.detail
python -m mafa_scraper.webcheck
python -m mafa_scraper.socials
python -m mafa_scraper.dork
python -m mafa_scraper.merge_csv
```

Flags: `--limit N` on detail/webcheck/socials/dork,
`--keyword <kw> --max-cells N` on search, `--headed` on
search/detail/socials (visible browser for debugging blocks),
`--all` on socials/dork (also process rows that already
have a website). Driver only: `--from STAGE` resumes mid-pipeline,
`--skip a,b` excludes stages (e.g. `--skip socials,dork`),
`--dry-run` prints the plan without running. Every stage writes
append-only JSONL and skips done keys, so rerun the same command to
resume.

Outputs in `out/`: `gmaps_raw.jsonl`, `gmaps_detail.jsonl`,
`webcheck.jsonl`, `socials.jsonl`, `dork.jsonl`, `canggu_businesses.csv`.

See `Canggu Scraper Docs.md` for the end-to-end design.
