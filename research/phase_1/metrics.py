"""Deterministic diff metrics; structural labels are conservative heuristics."""

from __future__ import annotations

import ast
import difflib
import re
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class DiffMetrics:
    raw_added: int
    raw_removed: int
    raw_net: int
    changed_tokens: int
    similar_removed_lines: int
    likely_move_or_copy: bool
    boilerplate_added: int
    structural_symbols_added: int
    structural_symbols_removed: int
    structural_symbols_net: int
    symbols_added: tuple[str, ...]
    symbols_removed: tuple[str, ...]
    dependencies_added: tuple[str, ...]
    dependencies_removed: tuple[str, ...]
    gaming_flags: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


def _tokens(source: str) -> list[str]:
    return re.findall(r"[A-Za-z_][A-Za-z_0-9]*|[^\sA-Za-z_0-9]", source)


def _symbols(source: str) -> set[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    return {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.ClassDef))}


def _dependencies(source: str) -> set[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


def _line_kinds(before: str, after: str) -> tuple[list[str], list[str]]:
    matcher = difflib.SequenceMatcher(None, before.splitlines(), after.splitlines(), autojunk=False)
    added, removed = [], []
    for tag, before_start, before_end, after_start, after_end in matcher.get_opcodes():
        if tag in {"replace", "delete"}:
            removed.extend(before.splitlines()[before_start:before_end])
        if tag in {"replace", "insert"}:
            added.extend(after.splitlines()[after_start:after_end])
    return added, removed


def measure_diff(before: str, after: str) -> DiffMetrics:
    added_lines, removed_lines = _line_kinds(before, after)
    similar_removed = sum(
        1
        for old in removed_lines
        if any(difflib.SequenceMatcher(None, old.strip(), new.strip()).ratio() >= 0.7 for new in added_lines)
    )
    boilerplate = sum(
        1 for line in added_lines if not line.strip() or line.lstrip().startswith(("#", '"""', "'''"))
    )
    before_symbols, after_symbols = _symbols(before), _symbols(after)
    before_deps, after_deps = _dependencies(before), _dependencies(after)
    flags = []
    if before.count("\n") > after.count("\n") and len(_tokens(after)) < len(_tokens(before)) * 0.65:
        flags.append("possible_compression")
    if len(after.splitlines()) < len(before.splitlines()) and "test" in after.lower() and "test" not in before.lower():
        flags.append("test_surface_changed")
    return DiffMetrics(
        raw_added=len(added_lines),
        raw_removed=len(removed_lines),
        raw_net=len(added_lines) - len(removed_lines),
        changed_tokens=len(_tokens(after)) - len(_tokens(before)),
        similar_removed_lines=similar_removed,
        likely_move_or_copy=similar_removed > 0 and len(added_lines) > 0,
        boilerplate_added=boilerplate,
        structural_symbols_added=len(after_symbols - before_symbols),
        structural_symbols_removed=len(before_symbols - after_symbols),
        structural_symbols_net=len(after_symbols - before_symbols) - len(before_symbols - after_symbols),
        symbols_added=tuple(sorted(after_symbols - before_symbols)),
        symbols_removed=tuple(sorted(before_symbols - after_symbols)),
        dependencies_added=tuple(sorted(after_deps - before_deps)),
        dependencies_removed=tuple(sorted(before_deps - after_deps)),
        gaming_flags=tuple(flags),
    )
