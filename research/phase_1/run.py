"""Command-line entry point: python -m research.phase_1.run."""

from __future__ import annotations

import argparse

from .harness import run_dry_run


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the offline Phase 1 subtraction benchmark.")
    parser.add_argument("--output", default="research/phase-1/dry-run.json")
    args = parser.parse_args()
    records = run_dry_run(args.output)
    passed = sum(record.tests.passed for record in records)
    print(f"wrote {len(records)} records to {args.output}; tests passed in {passed}/{len(records)} runs")


if __name__ == "__main__":
    main()
