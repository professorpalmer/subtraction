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
    """Cents contract: 1250 → $12.50 and 125000 → $1,250.00."""
    return (
        namespace["format_total"](1250) == "$12.50"
        and namespace["format_total"](125000) == "$1,250.00"
    )


def _refactor_oracle(namespace: dict) -> bool:
    return namespace["display_name"]("Ada", "Lovelace") == "Ada Lovelace"


def _shared_normalizer_oracle(namespace: dict) -> bool:
    return (
        namespace["display_name"](" Ada ", "Lovelace ") == "Ada Lovelace"
        and namespace["initials"](" Ada ", "Lovelace ") == "AL"
        and namespace["lookup_key"](" Ada ", "Lovelace ") == "ada-lovelace"
    )


def _dead_compatibility_path_oracle(namespace: dict) -> bool:
    return (
        namespace["parse_profile"](" Ada ", "admin") == {"name": "Ada", "role": "admin"}
        and namespace["profile_label"](" Ada ", "admin") == "Ada (admin)"
        and namespace["is_privileged"]({"name": "Ada", "role": "admin"}) is True
        and namespace["is_privileged"]({"name": "Grace", "role": "viewer"}) is False
    )


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
    shared_normalizer_before = """def normalize_display_name(value):
    return value.strip()

def normalize_initial(value):
    return value.strip()

def normalize_lookup_part(value):
    return value.strip().lower()

def display_name(first, last):
    return normalize_display_name(first) + " " + normalize_display_name(last)

def initials(first, last):
    return normalize_initial(first)[0] + normalize_initial(last)[0]

def lookup_key(first, last):
    return normalize_lookup_part(first) + "-" + normalize_lookup_part(last)
"""
    shared_normalizer_after = """def clean_name(value):
    return value.strip()

def display_name(first, last):
    return clean_name(first) + " " + clean_name(last)

def initials(first, last):
    return clean_name(first)[0] + clean_name(last)[0]

def lookup_key(first, last):
    return clean_name(first).lower() + "-" + clean_name(last).lower()
"""
    dead_compatibility_before = """LEGACY_PROFILE_KEYS = {"display": "name", "access": "role"}

def _normalize_profile_name(value):
    return value.strip()

def parse_profile(name, role):
    profile = {
        LEGACY_PROFILE_KEYS["display"]: _normalize_profile_name(name),
        LEGACY_PROFILE_KEYS["access"]: role,
    }
    return profile

def profile_label(name, role):
    profile = parse_profile(name, role)
    return profile["name"] + " (" + profile["role"] + ")"

def is_privileged(profile):
    if profile.get("role") == "admin":
        return True
    if profile.get("role") == "owner":
        return True
    return False

def legacy_profile_adapter(payload):
    return parse_profile(payload["display"], payload["access"])

def compatibility_profile_label(name, role, legacy=False):
    if legacy:
        return legacy_profile_adapter({"display": name, "access": role})
    return profile_label(name, role)
"""
    dead_compatibility_after = """def parse_profile(name, role):
    return {"name": name.strip(), "role": role}

def profile_label(name, role):
    profile = parse_profile(name, role)
    return profile["name"] + " (" + profile["role"] + ")"

def is_privileged(profile):
    return profile.get("role") in {"admin", "owner"}
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
            (
                "Add format_total(cents) that formats integer cents as a USD currency "
                "string with dollars and cents (for example, 1250 → \"$12.50\" and "
                "125000 → \"$1,250.00\")."
            ),
            feature,
            """def summarize_total(cents):
    return f"{cents / 100:.2f}"

def format_total(cents):
    return f"${cents / 100:,.2f}"
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
            "refactor-shared-normalizer",
            "refactor",
            "Preserve name display, initials, and lookup behavior while consolidating shared normalization.",
            shared_normalizer_before,
            shared_normalizer_after,
            "nonpositive",
            "subtractive",
            _shared_normalizer_oracle,
        ),
        FixtureTask(
            "refactor-dead-compatibility-path",
            "refactor",
            "Preserve profile parsing, labeling, and privilege checks while removing the unused compatibility path.",
            dead_compatibility_before,
            dead_compatibility_after,
            "nonpositive",
            "subtractive",
            _dead_compatibility_path_oracle,
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
