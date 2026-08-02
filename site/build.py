"""Assemble a self-contained GitHub Pages publication artifact."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Iterable


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SITE_SOURCE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = REPOSITORY_ROOT / "site-dist"

PUBLISHED_FILES = (
    ("paper/subtraction-study.pdf", "paper/subtraction-study.pdf"),
    ("paper/subtraction-study.tex", "paper/subtraction-study.tex"),
    (
        "research/phase-2/LARGER_REFACTOR_PROTOCOL.md",
        "research/phase-2/LARGER_REFACTOR_PROTOCOL.md",
    ),
    (
        "research/phase-2/LARGER_REFACTOR_FINDINGS.md",
        "research/phase-2/LARGER_REFACTOR_FINDINGS.md",
    ),
    (
        "research/phase-2/live/larger-refactor-r5-report.json",
        "research/phase-2/live/larger-refactor-r5-report.json",
    ),
    (
        "research/phase-2/live/larger-refactor-r5-factor-effects.json",
        "research/phase-2/live/larger-refactor-r5-factor-effects.json",
    ),
    (
        "research/phase-2/live/larger-refactor-r5-wave-meta.json",
        "research/phase-2/live/larger-refactor-r5-wave-meta.json",
    ),
)

DEPLOYED_LINKS = (
    ("../paper/", "paper/"),
    ("../research/", "research/"),
    (
        "../README.md",
        "https://github.com/professorpalmer/subtraction#readme",
    ),
)


def _copy_files(output_directory: Path, files: Iterable[tuple[str, str]]) -> None:
    for source_name, destination_name in files:
        source_path = REPOSITORY_ROOT / source_name
        if not source_path.is_file():
            raise FileNotFoundError(f"publication input is missing: {source_path}")
        destination_path = output_directory / destination_name
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)


def build_publication_site(output_directory: Path) -> Path:
    """Create a Pages-ready site with its evidence links and assets bundled."""
    resolved_output = output_directory.resolve()
    if resolved_output == SITE_SOURCE.resolve():
        raise ValueError("output directory must not replace the site source")
    if resolved_output.exists():
        shutil.rmtree(resolved_output)
    resolved_output.mkdir(parents=True)

    for asset_name in ("styles.css",):
        shutil.copy2(SITE_SOURCE / asset_name, resolved_output / asset_name)

    index_html = (SITE_SOURCE / "index.html").read_text(encoding="utf-8")
    for source_link, deployed_link in DEPLOYED_LINKS:
        index_html = index_html.replace(source_link, deployed_link)
    (resolved_output / "index.html").write_text(index_html, encoding="utf-8")

    _copy_files(resolved_output, PUBLISHED_FILES)
    return resolved_output


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="directory to create for the Pages upload",
    )
    return parser.parse_args()


def main() -> None:
    output_directory = build_publication_site(parse_arguments().output)
    print(f"Built publication site at {output_directory}")


if __name__ == "__main__":
    main()
