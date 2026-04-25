"""Validation engine for Cortex decision records."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pydantic import ValidationError

from cortex.models import DecisionRecord


@dataclass
class Issue:
    """A single validation issue."""

    file: str
    message: str
    field: str | None = None
    severity: str = "error"  # error | warning


@dataclass
class ValidationResult:
    """Result of validating decision records."""

    issues: list[Issue] = field(default_factory=list)
    valid_count: int = 0
    total_count: int = 0

    @property
    def is_valid(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "warning"]


def load_record(path: Path) -> tuple[DecisionRecord | None, list[Issue]]:
    """Load and validate a single decision record from a YAML file."""
    issues: list[Issue] = []
    filename = path.name

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        issues.append(Issue(file=filename, message=f"Cannot read file: {e}"))
        return None, issues

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        issues.append(Issue(file=filename, message=f"Invalid YAML: {e}"))
        return None, issues

    if not isinstance(data, dict):
        issues.append(Issue(file=filename, message="File must contain a YAML mapping"))
        return None, issues

    # Check ID matches filename before pydantic validation
    expected_id = path.stem
    file_id = data.get("id")
    if file_id is not None and str(file_id) != expected_id:
        issues.append(
            Issue(
                file=filename,
                message=f"ID '{file_id}' does not match filename '{expected_id}'",
                field="id",
            )
        )

    try:
        record = DecisionRecord.model_validate(data)
    except ValidationError as e:
        for err in e.errors():
            loc = " → ".join(str(part) for part in err["loc"])
            issues.append(
                Issue(
                    file=filename,
                    message=err["msg"],
                    field=loc or None,
                )
            )
        return None, issues

    return record, issues


def _detect_cycles(records: dict[str, DecisionRecord]) -> list[list[str]]:
    """Detect cycles in the decision DAG using DFS."""
    children: dict[str, list[str]] = {rid: [] for rid in records}
    for rid, record in records.items():
        for parent_id in record.parents:
            if parent_id in children:
                children[parent_id].append(rid)

    cycles: list[list[str]] = []
    visited: set[str] = set()
    in_stack: set[str] = set()

    def dfs(node: str, path: list[str]) -> None:
        if node in in_stack:
            cycle_start = path.index(node)
            cycles.append(path[cycle_start:] + [node])
            return
        if node in visited:
            return

        visited.add(node)
        in_stack.add(node)
        path.append(node)

        for child in children.get(node, []):
            dfs(child, path)

        path.pop()
        in_stack.remove(node)

    for node in records:
        if node not in visited:
            dfs(node, [])

    return cycles


def validate_timeline(
    timeline_dir: Path,
    files: list[Path] | None = None,
) -> ValidationResult:
    """Validate all decision records in the timeline directory."""
    result = ValidationResult()

    if files:
        yaml_files = sorted(f for f in files if f.suffix in (".yaml", ".yml"))
    else:
        if not timeline_dir.exists():
            result.issues.append(
                Issue(
                    file=str(timeline_dir),
                    message="Timeline directory does not exist",
                )
            )
            return result
        yaml_files = sorted(timeline_dir.glob("*.yaml"))

    result.total_count = len(yaml_files)

    if not yaml_files:
        result.issues.append(
            Issue(
                file=str(timeline_dir),
                message="No decision records found",
                severity="warning",
            )
        )
        return result

    records: dict[str, DecisionRecord] = {}

    # Pass 1: load and validate individual records
    for path in yaml_files:
        record, issues = load_record(path)
        result.issues.extend(issues)
        if record:
            records[record.id] = record
            result.valid_count += 1

    all_ids = set(records.keys())

    # Pass 2: cross-reference validation
    for rid, record in records.items():
        filename = f"{rid}.yaml"

        for parent_id in record.parents:
            if parent_id not in all_ids:
                result.issues.append(
                    Issue(
                        file=filename,
                        message=f"Parent '{parent_id}' does not exist",
                        field="parents",
                    )
                )

        if record.resolves and record.resolves.from_id not in all_ids:
            result.issues.append(
                Issue(
                    file=filename,
                    message=f"Resolves references non-existent decision '{record.resolves.from_id}'",
                    field="resolves → from",
                )
            )

        if record.status.value == "superseded":
            has_child = any(rid in r.parents for r in records.values())
            if not has_child:
                result.issues.append(
                    Issue(
                        file=filename,
                        message="Superseded decision has no children referencing it",
                        field="status",
                        severity="warning",
                    )
                )

    # Pass 3: cycle detection
    cycles = _detect_cycles(records)
    for cycle in cycles:
        cycle_str = " → ".join(cycle)
        result.issues.append(
            Issue(
                file=f"{cycle[0]}.yaml",
                message=f"Cycle detected: {cycle_str}",
            )
        )

    return result
