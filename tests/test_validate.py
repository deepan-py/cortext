"""Tests for Cortex validation engine."""

from pathlib import Path

import pytest

from cortex.validate import load_record, validate_timeline


class TestLoadRecord:
    def test_valid_record(self, timeline_dir: Path, valid_yaml: str) -> None:
        path = timeline_dir / "2025-04-25-001.yaml"
        path.write_text(valid_yaml)
        record, issues = load_record(path)
        assert record is not None
        assert len(issues) == 0
        assert record.id == "2025-04-25-001"

    def test_id_mismatch(self, timeline_dir: Path) -> None:
        path = timeline_dir / "2025-04-25-001.yaml"
        path.write_text(
            'id: "2025-04-25-999"\n'
            "status: active\n"
            'date: "2025-04-25"\n'
            "author: human\n"
            "domains:\n  - auth\n"
            'decision: "Test."\n'
            'context: "Test."\n'
        )
        record, issues = load_record(path)
        assert any("does not match filename" in i.message for i in issues)

    def test_invalid_yaml(self, timeline_dir: Path) -> None:
        path = timeline_dir / "2025-04-25-001.yaml"
        path.write_text("{{invalid yaml")
        record, issues = load_record(path)
        assert record is None
        assert any("Invalid YAML" in i.message for i in issues)

    def test_empty_file(self, timeline_dir: Path) -> None:
        path = timeline_dir / "2025-04-25-001.yaml"
        path.write_text("")
        record, issues = load_record(path)
        assert record is None
        assert any("YAML mapping" in i.message for i in issues)

    def test_missing_required_field(self, timeline_dir: Path) -> None:
        path = timeline_dir / "2025-04-25-001.yaml"
        path.write_text(
            'id: "2025-04-25-001"\n'
            "status: active\n"
            'date: "2025-04-25"\n'
            "author: human\n"
            "domains:\n  - auth\n"
            # missing decision and context
        )
        record, issues = load_record(path)
        assert record is None
        assert len(issues) > 0


class TestValidateTimeline:
    def test_empty_timeline(self, timeline_dir: Path) -> None:
        result = validate_timeline(timeline_dir)
        assert result.is_valid  # no errors, just warning
        assert len(result.warnings) == 1
        assert "No decision records" in result.warnings[0].message

    def test_nonexistent_directory(self, tmp_path: Path) -> None:
        result = validate_timeline(tmp_path / "nonexistent")
        assert not result.is_valid
        assert "does not exist" in result.errors[0].message

    def test_valid_single_record(
        self, timeline_dir: Path, valid_yaml: str
    ) -> None:
        (timeline_dir / "2025-04-25-001.yaml").write_text(valid_yaml)
        result = validate_timeline(timeline_dir)
        assert result.is_valid
        assert result.valid_count == 1
        assert result.total_count == 1

    def test_missing_parent_reference(self, timeline_dir: Path) -> None:
        (timeline_dir / "2025-04-25-001.yaml").write_text(
            'id: "2025-04-25-001"\n'
            "status: active\n"
            'date: "2025-04-25"\n'
            "author: human\n"
            "domains:\n  - auth\n"
            'decision: "Test."\n'
            'context: "Test."\n'
            "parents:\n"
            '  - "2025-04-20-001"\n'
        )
        result = validate_timeline(timeline_dir)
        assert not result.is_valid
        assert any("does not exist" in i.message for i in result.errors)

    def test_valid_parent_reference(
        self, timeline_dir: Path, valid_yaml: str
    ) -> None:
        (timeline_dir / "2025-04-25-001.yaml").write_text(valid_yaml)
        (timeline_dir / "2025-04-28-001.yaml").write_text(
            'id: "2025-04-28-001"\n'
            "status: active\n"
            'date: "2025-04-28"\n'
            "author: human\n"
            "domains:\n  - auth\n"
            'decision: "Add RBAC."\n'
            'context: "Need role-based access."\n'
            "parents:\n"
            '  - "2025-04-25-001"\n'
        )
        result = validate_timeline(timeline_dir)
        assert result.is_valid
        assert result.valid_count == 2

    def test_superseded_without_child_warns(self, timeline_dir: Path) -> None:
        (timeline_dir / "2025-04-25-001.yaml").write_text(
            'id: "2025-04-25-001"\n'
            "status: superseded\n"
            'date: "2025-04-25"\n'
            "author: human\n"
            "domains:\n  - auth\n"
            'decision: "Old decision."\n'
            'context: "Old context."\n'
        )
        result = validate_timeline(timeline_dir)
        assert result.is_valid  # warning, not error
        assert any(
            "no children" in w.message for w in result.warnings
        )

    def test_resolves_nonexistent_decision(self, timeline_dir: Path) -> None:
        (timeline_dir / "2025-04-25-001.yaml").write_text(
            'id: "2025-04-25-001"\n'
            "status: active\n"
            'date: "2025-04-25"\n'
            "author: human\n"
            "domains:\n  - auth\n"
            'decision: "Test."\n'
            'context: "Test."\n'
            "resolves:\n"
            '  tension: "Some tension"\n'
            '  from: "2025-04-20-001"\n'
        )
        result = validate_timeline(timeline_dir)
        assert not result.is_valid
        assert any("non-existent" in i.message for i in result.errors)

    def test_multiple_valid_records(self, timeline_dir: Path) -> None:
        for i in range(1, 4):
            (timeline_dir / f"2025-04-25-{i:03d}.yaml").write_text(
                f'id: "2025-04-25-{i:03d}"\n'
                "status: active\n"
                'date: "2025-04-25"\n'
                "author: human\n"
                "domains:\n  - auth\n"
                f'decision: "Decision {i}."\n'
                f'context: "Context {i}."\n'
            )
        result = validate_timeline(timeline_dir)
        assert result.is_valid
        assert result.valid_count == 3
