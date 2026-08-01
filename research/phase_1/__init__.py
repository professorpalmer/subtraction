"""Runnable, dependency-free Phase 1 benchmark for subtraction research."""

from __future__ import annotations

from .arms import ARM_NAMES, COMPONENT_SCREEN_ARMS, choose_arm, prompt_for
from .fixtures import build_fixture_corpus
from .harness import run_dry_run

__all__ = [
    "ARM_NAMES",
    "COMPONENT_SCREEN_ARMS",
    "build_fixture_corpus",
    "choose_arm",
    "prompt_for",
    "run_dry_run",
]
