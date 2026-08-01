"""Controlled Phase 2 ablation design and measurement infrastructure."""

from __future__ import annotations

from .design import (
    DEFAULT_ARMS,
    DEFAULT_MODEL_EFFORTS,
    DesignCell,
    FactorialDesign,
    build_default_design,
)
from .harness import ingest_candidate, prepare_run
from .variance import analyze_result_files, analyze_variance_records, load_result_files

__all__ = [
    "DEFAULT_ARMS",
    "DEFAULT_MODEL_EFFORTS",
    "DesignCell",
    "FactorialDesign",
    "build_default_design",
    "ingest_candidate",
    "prepare_run",
    "analyze_result_files",
    "analyze_variance_records",
    "load_result_files",
]
