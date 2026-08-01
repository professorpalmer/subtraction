"""Command line interface for Phase 2 planning and summaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .aggregation import aggregate_result_files
from .design import build_ablation_screen_design, build_default_design
from .harness import prepare_run
from .variance import analyze_result_files


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan or summarize the Phase 2 ablation.")
    subparsers = parser.add_subparsers(dest="mode", required=True)
    plan = subparsers.add_parser("plan")
    plan.add_argument("--output", required=True)
    plan.add_argument("--runs-root", required=True)
    plan.add_argument("--repetitions", type=int, default=10)
    plan.add_argument("--tasks", nargs="+")
    plan.add_argument("--arms", nargs="+")
    plan.add_argument(
        "--ablation-screen",
        action="store_true",
        help="Materialize the preregistered 8-arm component screen (120 cells at R=5).",
    )
    summary = subparsers.add_parser("summary")
    summary.add_argument("--output", required=True)
    summary.add_argument("results", nargs="+")
    variance = subparsers.add_parser("variance")
    variance.add_argument("--output", required=True)
    variance.add_argument("results", nargs="+")
    args = parser.parse_args()
    if args.mode == "plan":
        if args.ablation_screen:
            if args.tasks or args.arms:
                raise SystemExit("--ablation-screen is mutually exclusive with --tasks/--arms")
            design = build_ablation_screen_design(args.repetitions)
        else:
            design = build_default_design(
                args.repetitions, task_ids=args.tasks, arms=args.arms,
            )
        design.write_manifest(args.output)
        for cell in design.cells:
            prepare_run(cell, args.runs_root)
        print(f"planned {len(design.cells)} cells in {args.runs_root}")
        return
    if args.mode == "summary":
        result = aggregate_result_files(args.results)
        Path(args.output).write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {len(result['groups'])} groups to {args.output}")
        return
    result = analyze_result_files(args.results)
    Path(args.output).write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(result['groups'])} variance groups to {args.output}")


if __name__ == "__main__":
    main()
