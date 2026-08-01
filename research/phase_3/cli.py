"""JSON command line interface for Phase 3 analysis and scenarios."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .analysis import analyze_files, calculate_context_savings


def _write_json(path: str, value: Any) -> None:
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze Phase 2 token usage.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="summarize Phase 2 result receipts")
    analyze.add_argument("results", nargs="+", help="Phase 2 JSON result files")
    analyze.add_argument("--pricing", help="optional model pricing JSON")
    analyze.add_argument("--output", required=True)

    scenario = subparsers.add_parser("scenario", help="calculate hypothetical context savings")
    scenario.add_argument("--baseline-input-tokens-per-turn", type=float, required=True)
    scenario.add_argument("--reduction-fraction", type=float, required=True)
    scenario.add_argument("--future-turn-count", type=int, required=True)
    scenario.add_argument("--price-per-million-input-tokens", type=float)
    scenario.add_argument("--output", required=True)
    return parser


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "analyze":
        pricing = None
        if args.pricing:
            pricing = json.loads(Path(args.pricing).read_text())
            if not isinstance(pricing, dict):
                raise ValueError("pricing JSON must contain an object")
        result = analyze_files(args.results, pricing)
    else:
        result = calculate_context_savings(
            args.baseline_input_tokens_per_turn,
            args.reduction_fraction,
            args.future_turn_count,
            args.price_per_million_input_tokens,
        )
    _write_json(args.output, result)


if __name__ == "__main__":
    main()
