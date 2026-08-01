"""Small deterministic Python fixtures with executable behavior oracles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


TaskType = str


@dataclass(frozen=True)
class FixtureTask:
    task_id: str
    task_type: TaskType
    instruction: str
    before: str
    after: str
    expected_sign: str
    expected_class: str
    oracle: Callable[[dict], bool]

    def is_valid(self) -> bool:
        return self.is_source_valid(self.after)

    def is_source_valid(self, source: str) -> bool:
        """Execute source and evaluate this task's behavior oracle."""
        namespace = {}
        try:
            exec(source, namespace)
            return self.oracle(namespace)
        except Exception:
            return False


def _feature_oracle(namespace: dict) -> bool:
    return namespace["format_total"](1250) == "$1,250"


def _refactor_oracle(namespace: dict) -> bool:
    return namespace["display_name"]("Ada", "Lovelace") == "Ada Lovelace"


def _cleanup_oracle(namespace: dict) -> bool:
    return namespace["parse_enabled"]("true") is True and namespace["parse_enabled"]("off") is False


def _control_oracle(namespace: dict) -> bool:
    return namespace["slugify"]("Hello World") == "hello-world"


def build_fixture_corpus() -> tuple[FixtureTask, ...]:
    """Return hand-authored tasks; no filesystem or network state is involved."""
    feature = """def summarize_total(cents):
    return f"{cents / 100:.2f}"
"""
    refactor = """def first_name(first, last):
    return first.strip()

def last_name(first, last):
    return last.strip()

def display_name(first, last):
    return first_name(first, last) + " " + last_name(first, last)
"""
    cleanup = """LEGACY_FLAG = True

def parse_enabled(value):
    if value == "true":
        return True
    if value in {"false", "off"}:
        return False
    return bool(value)

def obsolete_debug_message():
    return "debug"
"""
    cleanup_dead_branch = """def parse_enabled(value):
    if value == "true":
        return True
    if False:
        return "unreachable"
    if value in {"false", "off"}:
        return False
    return bool(value)
"""
    control = """def slugify(value):
    return value.lower().replace(" ", "-")
"""
    return (
        FixtureTask(
            "feature-format-total",
            "feature",
            "Add format_total(cents), returning a currency string such as $1,250.",
            feature,
            """def summarize_total(cents):
    return f"{cents / 100:.2f}"

def format_total(cents):
    return f"${cents:,}"
""",
            "positive",
            "additive",
            _feature_oracle,
        ),
        FixtureTask(
            "feature-clamp-score",
            "feature",
            "Add clamp_score(value) that limits a score to the inclusive range 0..100.",
            "def score(value):\n    return value\n",
            """def score(value):
    return value

def clamp_score(value):
    return max(0, min(100, value))
""",
            "positive",
            "additive",
            lambda namespace: namespace["clamp_score"](-2) == 0 and namespace["clamp_score"](101) == 100,
        ),
        FixtureTask(
            "refactor-shared-strip",
            "refactor",
            "Preserve display_name behavior while removing duplicated name normalization.",
            refactor,
            """def clean_name(value):
    return value.strip()

def display_name(first, last):
    return clean_name(first) + " " + clean_name(last)
""",
            "nonpositive",
            "subtractive",
            _refactor_oracle,
        ),
        FixtureTask(
            "refactor-inline-default",
            "refactor",
            "Preserve greeting behavior while removing the unnecessary temporary variable.",
            """def greeting(name):
    normalized = name.strip()
    return "Hello, " + normalized
""",
            """def greeting(name):
    return "Hello, " + name.strip()
""",
            "nonpositive",
            "subtractive",
            lambda namespace: namespace["greeting"](" Ada ") == "Hello, Ada",
        ),
        FixtureTask(
            "cleanup-legacy-flag",
            "cleanup",
            "Remove the unused legacy flag and obsolete debug helper without changing parsing.",
            cleanup,
            """def parse_enabled(value):
    if value == "true":
        return True
    if value in {"false", "off"}:
        return False
    return bool(value)
""",
            "negative",
            "subtractive",
            _cleanup_oracle,
        ),
        FixtureTask(
            "cleanup-dead-branch",
            "cleanup",
            "Remove the unreachable branch while preserving parse_enabled behavior.",
            cleanup_dead_branch,
            """def parse_enabled(value):
    if value == "true":
        return True
    if value in {"false", "off"}:
        return False
    return bool(value)
""",
            "negative",
            "subtractive",
            _cleanup_oracle,
        ),
        FixtureTask(
            "control-rename",
            "measurement_control",
            "Rename the local parameter for clarity without changing behavior.",
            control,
            """def slugify(text):
    return text.lower().replace(" ", "-")
""",
            "semantic_zero",
            "raw_churn",
            _control_oracle,
        ),
        FixtureTask(
            "control-formatting",
            "measurement_control",
            "Reformat the function without changing its behavior.",
            control,
            """def slugify(value):
    return value.lower().replace(
        " ",
        "-",
    )
""",
            "semantic_zero",
            "raw_churn",
            _control_oracle,
        ),
    )
