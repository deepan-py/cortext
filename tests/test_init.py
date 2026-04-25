"""Tests for Cortex init command."""

from pathlib import Path

from cortex.init_project import init_cortex


class TestInitCortex:
    def test_creates_directory_structure(self, tmp_path: Path) -> None:
        actions = init_cortex(tmp_path)
        assert (tmp_path / "context" / "timeline").is_dir()
        assert (tmp_path / "context" / "current").is_dir()
        assert (tmp_path / "context" / "skills").is_dir()
        assert len(actions) > 0

    def test_creates_template_files(self, tmp_path: Path) -> None:
        init_cortex(tmp_path)
        assert (tmp_path / "context" / "agent-rules.md").is_file()
        assert (tmp_path / "context" / "review-config.yaml").is_file()
        assert (tmp_path / "context" / "drift-config.yaml").is_file()
        assert (tmp_path / "context" / "skills" / "_index.md").is_file()
        assert (tmp_path / "context" / "skills" / "reviewer.md").is_file()
        assert (tmp_path / "context" / "skills" / "context-owner.md").is_file()

    def test_creates_empty_drift_register(self, tmp_path: Path) -> None:
        init_cortex(tmp_path)
        dr = tmp_path / "context" / "drift-register.jsonl"
        assert dr.is_file()
        assert dr.read_text() == ""

    def test_creates_gitignore(self, tmp_path: Path) -> None:
        init_cortex(tmp_path)
        gitignore = tmp_path / ".gitignore"
        assert gitignore.is_file()
        content = gitignore.read_text()
        assert "Cortex generated files" in content
        assert "context/graph.json" in content

    def test_updates_existing_gitignore(self, tmp_path: Path) -> None:
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("node_modules/\n")
        init_cortex(tmp_path)
        content = gitignore.read_text()
        assert "node_modules/" in content
        assert "Cortex generated files" in content

    def test_idempotent(self, tmp_path: Path) -> None:
        init_cortex(tmp_path)
        actions1_count = len(list((tmp_path / "context").rglob("*")))
        init_cortex(tmp_path)
        actions2_count = len(list((tmp_path / "context").rglob("*")))
        assert actions1_count == actions2_count

    def test_skips_existing_files(self, tmp_path: Path) -> None:
        init_cortex(tmp_path)
        # Modify a file
        rules = tmp_path / "context" / "agent-rules.md"
        rules.write_text("custom content")
        # Re-init should not overwrite
        init_cortex(tmp_path)
        assert rules.read_text() == "custom content"
