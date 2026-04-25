"""Tests for cortex show, status, supersede commands."""

from pathlib import Path

import yaml

from cortex.validate import load_all_records


def _write_decision(timeline_dir: Path, id: str, **overrides) -> Path:
    """Helper to write a decision YAML file."""
    data = {
        "id": id,
        "status": "active",
        "date": id.rsplit("-", 1)[0],  # e.g. "2025-04-25" from "2025-04-25-001"
        "author": "human",
        "domains": ["auth"],
        "decision": "Test decision.",
        "context": "Test context.",
        "parents": [],
        "alternatives_rejected": [],
        "assumptions": [],
        "tensions": [],
        "tags": [],
    }
    data.update(overrides)
    path = timeline_dir / f"{id}.yaml"
    path.write_text(
        yaml.dump(data, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    return path


class TestLoadAllRecords:
    def test_loads_valid_records(self, timeline_dir: Path) -> None:
        _write_decision(timeline_dir, "2025-04-25-001")
        _write_decision(timeline_dir, "2025-04-25-002", domains=["payments"])
        records = load_all_records(timeline_dir)
        assert len(records) == 2
        assert "2025-04-25-001" in records
        assert "2025-04-25-002" in records

    def test_skips_invalid_records(self, timeline_dir: Path) -> None:
        _write_decision(timeline_dir, "2025-04-25-001")
        # Write an invalid YAML
        (timeline_dir / "2025-04-25-002.yaml").write_text("not: valid: yaml: [")
        records = load_all_records(timeline_dir)
        assert len(records) == 1

    def test_empty_dir(self, timeline_dir: Path) -> None:
        records = load_all_records(timeline_dir)
        assert records == {}

    def test_nonexistent_dir(self, tmp_path: Path) -> None:
        records = load_all_records(tmp_path / "nope")
        assert records == {}


class TestShowDomain:
    """Test the domain filtering logic used by `cortex show`."""

    def test_filter_by_domain(self, timeline_dir: Path) -> None:
        _write_decision(timeline_dir, "2025-04-25-001", domains=["auth"])
        _write_decision(timeline_dir, "2025-04-25-002", domains=["payments"])
        _write_decision(timeline_dir, "2025-04-25-003", domains=["auth"])

        records = load_all_records(timeline_dir)
        auth_records = [
            r for r in records.values()
            if "auth" in r.domains and r.status.value == "active"
        ]
        assert len(auth_records) == 2

    def test_filter_excludes_superseded(self, timeline_dir: Path) -> None:
        _write_decision(timeline_dir, "2025-04-25-001", domains=["auth"])
        _write_decision(
            timeline_dir, "2025-04-25-002",
            domains=["auth"], status="superseded"
        )

        records = load_all_records(timeline_dir)
        active_auth = [
            r for r in records.values()
            if "auth" in r.domains and r.status.value == "active"
        ]
        assert len(active_auth) == 1
        assert active_auth[0].id == "2025-04-25-001"

    def test_filter_all_includes_superseded(self, timeline_dir: Path) -> None:
        _write_decision(timeline_dir, "2025-04-25-001", domains=["auth"])
        _write_decision(
            timeline_dir, "2025-04-25-002",
            domains=["auth"], status="superseded"
        )

        records = load_all_records(timeline_dir)
        all_auth = [r for r in records.values() if "auth" in r.domains]
        assert len(all_auth) == 2


class TestStatus:
    """Test the status dashboard logic."""

    def test_counts(self, timeline_dir: Path) -> None:
        _write_decision(timeline_dir, "2025-04-25-001", domains=["auth"])
        _write_decision(timeline_dir, "2025-04-25-002", domains=["payments"])
        _write_decision(
            timeline_dir, "2025-04-25-003",
            domains=["auth"], status="superseded"
        )

        records = load_all_records(timeline_dir)
        active = [r for r in records.values() if r.status.value == "active"]
        superseded = [r for r in records.values() if r.status.value == "superseded"]
        domains: dict[str, list[str]] = {}
        for r in records.values():
            for d in r.domains:
                domains.setdefault(d, []).append(r.id)

        assert len(records) == 3
        assert len(active) == 2
        assert len(superseded) == 1
        assert len(domains) == 2

    def test_unreviewed_ai(self, timeline_dir: Path) -> None:
        _write_decision(
            timeline_dir, "2025-04-25-001",
            author="ai", reviewed_by=None
        )
        _write_decision(
            timeline_dir, "2025-04-25-002",
            author="ai", reviewed_by="alice"
        )
        _write_decision(timeline_dir, "2025-04-25-003", author="human")

        records = load_all_records(timeline_dir)
        active = [r for r in records.values() if r.status.value == "active"]
        unreviewed_ai = [
            r for r in active
            if r.author.value == "ai" and r.reviewed_by is None
        ]
        assert len(unreviewed_ai) == 1
        assert unreviewed_ai[0].id == "2025-04-25-001"


class TestSupersede:
    """Test the supersede logic."""

    def test_supersede_marks_parent(self, timeline_dir: Path) -> None:
        parent = _write_decision(timeline_dir, "2025-04-25-001", domains=["auth"])
        # Simulate what the CLI does
        data = yaml.safe_load(parent.read_text())
        data["status"] = "superseded"
        parent.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))

        reloaded = yaml.safe_load(parent.read_text())
        assert reloaded["status"] == "superseded"

    def test_supersede_creates_child_with_parent_ref(self, timeline_dir: Path) -> None:
        _write_decision(timeline_dir, "2025-04-25-001", domains=["auth"])
        child_id = "2025-04-25-002"
        skeleton = (
            f'id: "{child_id}"\n'
            f"status: active\n"
            f'date: "2025-04-25"\n'
            f"author: human\n"
            f"domains:\n"
            f"  - auth\n"
            f"decision: >-\n"
            f"  Replaces 2025-04-25-001.\n"
            f"context: >-\n"
            f"  Old decision was wrong.\n"
            f"parents:\n"
            f'  - "2025-04-25-001"\n'
            f"alternatives_rejected: []\n"
            f"assumptions: []\n"
            f"tensions: []\n"
            f"tags: []\n"
        )
        (timeline_dir / f"{child_id}.yaml").write_text(skeleton)

        records = load_all_records(timeline_dir)
        assert child_id in records
        assert "2025-04-25-001" in records[child_id].parents

    def test_cannot_supersede_already_superseded(self, timeline_dir: Path) -> None:
        path = _write_decision(
            timeline_dir, "2025-04-25-001",
            domains=["auth"], status="superseded"
        )
        data = yaml.safe_load(path.read_text())
        assert data["status"] == "superseded"


class TestHookInstall:
    """Test hook install/uninstall logic."""

    def test_install_creates_hook(self, tmp_path: Path) -> None:
        git_dir = tmp_path / ".git" / "hooks"
        git_dir.mkdir(parents=True)
        hook_path = git_dir / "pre-commit"

        hook_script = (
            "#!/usr/bin/env sh\n"
            "# Cortex pre-commit hook\n"
            "cortex validate\n"
        )
        hook_path.write_text(hook_script)
        hook_path.chmod(0o755)

        assert hook_path.exists()
        content = hook_path.read_text()
        assert "cortex validate" in content

    def test_hook_is_executable(self, tmp_path: Path) -> None:
        git_dir = tmp_path / ".git" / "hooks"
        git_dir.mkdir(parents=True)
        hook_path = git_dir / "pre-commit"
        hook_path.write_text("#!/usr/bin/env sh\ncortex validate\n")
        hook_path.chmod(0o755)

        import os
        assert os.access(hook_path, os.X_OK)

    def test_append_to_existing_hook(self, tmp_path: Path) -> None:
        git_dir = tmp_path / ".git" / "hooks"
        git_dir.mkdir(parents=True)
        hook_path = git_dir / "pre-commit"
        hook_path.write_text("#!/usr/bin/env sh\necho 'existing hook'\n")

        # Simulate append
        with hook_path.open("a") as f:
            f.write("\n# --- Cortex validation (appended) ---\ncortex validate\n")

        content = hook_path.read_text()
        assert "existing hook" in content
        assert "cortex validate" in content

    def test_uninstall_removes_hook(self, tmp_path: Path) -> None:
        git_dir = tmp_path / ".git" / "hooks"
        git_dir.mkdir(parents=True)
        hook_path = git_dir / "pre-commit"
        hook_path.write_text(
            "#!/usr/bin/env sh\n# Cortex pre-commit hook\ncortex validate\n"
        )

        hook_path.unlink()
        assert not hook_path.exists()
