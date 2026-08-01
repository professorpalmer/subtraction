"""Run preparation and candidate ingestion without contacting model providers."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Optional, Union

from research.phase_1.fixtures import build_fixture_corpus
from research.phase_1.harness import TokenUsage, measure_candidate_patch

from .design import DesignCell

_CELL_ID = re.compile(r"^cell-[0-9a-f]{12}$")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _task_map() -> dict:
    return {task.task_id: task for task in build_fixture_corpus()}


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise ValueError(f"invalid JSON artifact: {path}") from exc


def prepare_run(cell: DesignCell, runs_root: Union[str, Path]) -> Path:
    """Create an isolated cell directory containing only immutable inputs."""
    if not _CELL_ID.fullmatch(cell.cell_id):
        raise ValueError("unsafe cell ID")
    root = Path(runs_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    run_dir = (root / cell.cell_id).resolve()
    if run_dir.parent != root:
        raise ValueError("cell path escapes runs root")
    if run_dir.exists() and any(run_dir.iterdir()):
        raise FileExistsError(f"run already exists and is non-empty: {run_dir}")
    run_dir.mkdir(exist_ok=True)
    task = _task_map().get(cell.task_id)
    if task is None:
        raise ValueError(f"unknown task: {cell.task_id}")
    if task.task_type != cell.task_class:
        raise ValueError("cell task class does not match fixture")
    initial_dir = run_dir / "initial"
    candidate_dir = run_dir / "candidate"
    initial_dir.mkdir()
    candidate_dir.mkdir()
    (initial_dir / "source.py").write_text(task.before)
    _write_json(initial_dir / "task.json", {
        "task_id": task.task_id,
        "task_class": task.task_type,
        "instruction": task.instruction,
        "expected_sign": task.expected_sign,
        "expected_class": task.expected_class,
        "source_sha256": _sha256(task.before),
    })
    _write_json(run_dir / "manifest.json", {
        "protocol": "phase-2-controlled-ablation-v1",
        "cell": cell.to_dict(),
        "initial_source_sha256": _sha256(task.before),
        "initial_source_path": "initial/source.py",
        "task_metadata_path": "initial/task.json",
        "candidate_directory": "candidate",
    })
    return run_dir


def _validate_manifest(run_dir: Path, cell: DesignCell) -> dict:
    manifest = _read_json(run_dir / "manifest.json")
    if manifest.get("cell") != cell.to_dict():
        raise ValueError("run manifest does not match prepared cell")
    source = run_dir / "initial" / "source.py"
    metadata = _read_json(run_dir / "initial" / "task.json")
    if not source.is_file() or metadata.get("source_sha256") != _sha256(source.read_text()):
        raise ValueError("immutable initial source has been modified")
    if manifest.get("initial_source_sha256") != _sha256(source.read_text()):
        raise ValueError("manifest initial source hash mismatch")
    return manifest


def ingest_candidate(
    cell: DesignCell,
    run_dir: Union[str, Path],
    candidate: Union[str, Path],
    *,
    model: str,
    reasoning_effort: str,
    execution_source: str,
    turns: Optional[int],
    tool_calls: Optional[int],
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
    total_tokens: Optional[int] = None,
    adapter_status: str = "completed",
    adapter_job_id: Optional[str] = None,
) -> dict:
    """Measure one candidate and persist a deterministic JSON result."""
    run_path = Path(run_dir).resolve()
    _validate_manifest(run_path, cell)
    if model != cell.model or reasoning_effort != cell.reasoning_effort:
        raise ValueError(
            "actual model/reasoning_effort does not match prepared design cell"
        )
    result_path = run_path / "candidate" / "result.json"
    candidate_source_path = run_path / "candidate" / "source.py"
    if result_path.exists() or candidate_source_path.exists():
        raise FileExistsError(f"candidate artifacts already exist under {run_path / 'candidate'}")
    task = _task_map().get(cell.task_id)
    if task is None or task.task_type != cell.task_class:
        raise ValueError("cell task does not match immutable fixture")
    candidate_path = Path(candidate)
    if candidate_path.is_file():
        candidate_source = candidate_path.read_text()
        if candidate_path.resolve() == (run_path / "initial" / "source.py").resolve():
            raise ValueError("candidate cannot be the immutable initial source")
    else:
        candidate_source = str(candidate)
    if candidate_source == task.before:
        raise ValueError("candidate cannot equal immutable initial source")
    if (turns is not None and turns < 0) or (tool_calls is not None and tool_calls < 0):
        raise ValueError("turns and tool_calls cannot be negative")
    record = measure_candidate_patch(
        task, cell.arm, candidate_source, model=model,
        reasoning_effort=reasoning_effort, execution_source=execution_source,
        turns=turns, tool_calls=tool_calls,
        token_usage=TokenUsage(input_tokens, output_tokens), dry_run=False,
    )
    result = {
        "protocol": "phase-2-controlled-ablation-v1",
        "cell": cell.to_dict(),
        "actual": {
            "model": model, "reasoning_effort": reasoning_effort,
            "execution_source": execution_source, "turns": turns,
            "tool_calls": tool_calls, "input_tokens": input_tokens,
            "output_tokens": output_tokens, "total_tokens": total_tokens,
            "adapter_status": adapter_status, "adapter_job_id": adapter_job_id,
        },
        "candidate_sha256": _sha256(candidate_source),
        "record": record.to_dict(),
    }
    result = json.loads(json.dumps(result, sort_keys=True))
    _write_json(result_path, result)
    candidate_source_path.write_text(candidate_source)
    return result
