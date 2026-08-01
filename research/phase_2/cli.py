"""Command line interface for Phase 2 planning and summaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .aggregation import aggregate_result_files
from .design import build_default_design
from .harness import prepare_run


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan or summarize the Phase 2 ablation.")
    subparsers = parser.add_subparsers(dest="mode", required=True)
    plan = subparsers.add_parser("plan")
    plan.add_argument("--output", required=True)
    plan.add_argument("--runs-root", required=True)
    plan.add_argument("--repetitions", type=int, default=10)
    summary = subparsers.add_parser("summary")
    summary.add_argument("--output", required=True)
    summary.add_argument("results", nargs="+")
    args = parser.parse_args()
    if args.mode == "plan":
        design = build_default_design(args.repetitions)
        design.write_manifest(args.output)
        for cell in design.cells:
            prepare_run(cell, args.runs_root)
        print(f"planned {len(design.cells)} cells in {args.runs_root}")
        return
    result = aggregate_result_files(args.results)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"wrote {len(result['groups'])} groups to {args.output}")


if __name__ == "__main__":
    main()
