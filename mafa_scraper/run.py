"""Single-command pipeline driver: search -> detail -> webcheck -> socials -> dork -> merge_csv.

Subprocess driver, stdlib only: each stage keeps working standalone with
identical flags. Every stage is append-only + resumable, so reruns and
--from pick up where the previous run stopped. Aborts on the first
failing stage.
"""
import argparse
import subprocess
import sys

from mafa_scraper.config import ROOT

STAGES = ["search", "detail", "webcheck", "socials", "dork", "merge_csv"]
HEADED_STAGES = {"search", "detail", "socials"}


def stage_argv(stage, args):
    argv = [sys.executable, "-m", f"mafa_scraper.{stage}"]
    if stage == "search":
        if args.keyword:
            argv += ["--keyword", args.keyword]
        if args.max_cells is not None:
            argv += ["--max-cells", str(args.max_cells)]
    if stage in ("detail", "webcheck", "socials", "dork") \
            and args.limit is not None:
        argv += ["--limit", str(args.limit)]
    if stage in HEADED_STAGES and args.headed:
        argv.append("--headed")
    if stage in ("socials", "dork") and args.all:
        argv.append("--all")
    return argv


def parse_skip(value):
    skip = [s.strip() for s in value.split(",") if s.strip()]
    unknown = [s for s in skip if s not in STAGES]
    if unknown:
        raise argparse.ArgumentTypeError(
            f"unknown stages: {', '.join(unknown)}")
    return set(skip)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None,
                    help="cap for detail/webcheck/socials/dork")
    ap.add_argument("--keyword", default=None,
                    help="search: single keyword instead of all 20")
    ap.add_argument("--max-cells", type=int, default=None,
                    help="search: cap grid cells")
    ap.add_argument("--headed", action="store_true",
                    help="search/detail/socials: visible browser")
    ap.add_argument("--all", action="store_true",
                    help="socials/dork: also process rows that "
                         "already have a website")
    ap.add_argument("--from", dest="from_stage", default="search",
                    choices=STAGES, help="resume from this stage")
    ap.add_argument("--skip", type=parse_skip, default=set(),
                    help="comma list, e.g. --skip socials,dork")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the stage commands without running them")
    args = ap.parse_args()

    plan = [s for s in STAGES[STAGES.index(args.from_stage):]
            if s not in args.skip]
    if not plan:
        print("run: nothing to do (all stages skipped)")
        return
    for i, stage in enumerate(plan, 1):
        argv = stage_argv(stage, args)
        print(f"=== [{i}/{len(plan)}] {' '.join(argv[2:])} ===",
              flush=True)
        if args.dry_run:
            continue
        try:
            subprocess.run(argv, cwd=ROOT, check=True)
        except subprocess.CalledProcessError as e:
            print(f"run: stage '{stage}' failed "
                  f"(exit {e.returncode}), aborting")
            sys.exit(e.returncode or 1)
    print("run: DONE" + (" (dry-run)" if args.dry_run else ""))


if __name__ == "__main__":
    main()
