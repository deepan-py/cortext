"""Tests for Cortex init command."""

from pathlib import Path

from cortex.init_project import init_cortex, add_skill


class TestInitCortex:
    def test_creates_directory_structure(self, tmp_path: Path) -> None:
        actions = init_cortex(tmp_path)
        assert (tmp_path / ".cortex" / "timeline").is_dir()
        assert (tmp_path / ".cortex" / "current").is_dir()
        assert (tmp_path / ".cortex" / "skills").is_dir()
        assert len(actions) > 0

    def test_creates_template_files(self, tmp_path: Path) -> None:
        init_cortex(tmp_path)
        assert (tmp_path / ".cortex" / "agent-rules.md").is_file()
        assert (tmp_path / ".cortex" / "review-config.yaml").is_file()
        assert (tmp_path / ".cortex" / "drift-config.yaml").is_file()
        assert (tmp_path / ".cortex" / "skills" / "_index.md").is_file()
        assert (tmp_path / ".cortex" / "skills" / "reviewer.md").is_file()
        assert (tmp_path / ".cortex" / "skills" / "context-owner.md").is_file()

    def test_creates_skills_json(self, tmp_path: Path) -> None:
        init_cortex(tmp_path)
        import json

        skills_json = tmp_path / ".cortex" / "skills.json"
        assert skills_json.is_file()
        data = json.loads(skills_json.read_text())
        assert "skills" in data
        assert len(data["skills"]) == 2
        names = [s["name"] for s in data["skills"]]
        assert "reviewer" in names
        assert "context-owner" in names

    def test_creates_empty_drift_register(self, tmp_path: Path) -> None:
        init_cortex(tmp_path)
        dr = tmp_path / ".cortex" / "drift-register.jsonl"
        assert dr.is_file()
        assert dr.read_text() == ""

    def test_creates_gitignore(self, tmp_path: Path) -> None:
        init_cortex(tmp_path)
        gitignore = tmp_path / ".gitignore"
        assert gitignore.is_file()
        content = gitignore.read_text()
        assert "Cortex generated files" in content
        assert ".cortex/graph.json" in content

    def test_updates_existing_gitignore(self, tmp_path: Path) -> None:
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("node_modules/\n")
        init_cortex(tmp_path)
        content = gitignore.read_text()
        assert "node_modules/" in content
        assert "Cortex generated files" in content

    def test_idempotent(self, tmp_path: Path) -> None:
        init_cortex(tmp_path)
        actions1_count = len(list((tmp_path / ".cortex").rglob("*")))
        init_cortex(tmp_path)
        actions2_count = len(list((tmp_path / ".cortex").rglob("*")))
        assert actions1_count == actions2_count

    def test_skips_existing_files(self, tmp_path: Path) -> None:
        init_cortex(tmp_path)
        # Modify a file
        rules = tmp_path / ".cortex" / "agent-rules.md"
        rules.write_text("custom content")
        # Re-init should not overwrite
        init_cortex(tmp_path)
        assert rules.read_text() == "custom content"


class TestInitWithAI:
    def test_copilot_creates_instructions(self, tmp_path: Path) -> None:
        actions = init_cortex(tmp_path, ai_platforms=["copilot"])
        dest = tmp_path / ".github" / "copilot-instructions.md"
        assert dest.is_file()
        content = dest.read_text()
        assert "Cortex" in content
        assert any("copilot-instructions.md" in a for a in actions)

    def test_claude_creates_instructions(self, tmp_path: Path) -> None:
        actions = init_cortex(tmp_path, ai_platforms=["claude"])
        dest = tmp_path / "CLAUDE.md"
        assert dest.is_file()
        content = dest.read_text()
        assert "Cortex" in content
        assert any("CLAUDE.md" in a for a in actions)

    def test_no_ai_skips_platform_files(self, tmp_path: Path) -> None:
        init_cortex(tmp_path)
        assert not (tmp_path / ".github" / "copilot-instructions.md").exists()
        assert not (tmp_path / "CLAUDE.md").exists()

    def test_ai_files_not_overwritten(self, tmp_path: Path) -> None:
        init_cortex(tmp_path, ai_platforms=["copilot"])
        dest = tmp_path / ".github" / "copilot-instructions.md"
        dest.write_text("custom")
        init_cortex(tmp_path, ai_platforms=["copilot"])
        assert dest.read_text() == "custom"

    def test_multiple_ai_platforms(self, tmp_path: Path) -> None:
        actions = init_cortex(tmp_path, ai_platforms=["copilot", "claude"])
        assert (tmp_path / ".github" / "copilot-instructions.md").is_file()
        assert (tmp_path / "CLAUDE.md").is_file()
        assert any("copilot-instructions.md" in a for a in actions)
        assert any("CLAUDE.md" in a for a in actions)

    def test_multiple_ai_idempotent(self, tmp_path: Path) -> None:
        init_cortex(tmp_path, ai_platforms=["copilot", "claude"])
        actions = init_cortex(tmp_path, ai_platforms=["copilot", "claude"])
        skipped = [a for a in actions if "Skipped" in a]
        assert any("copilot-instructions.md" in a for a in skipped)
        assert any("CLAUDE.md" in a for a in skipped)


class TestAddSkill:
    def test_add_skill_to_registry(self, tmp_path: Path) -> None:
        import json

        init_cortex(tmp_path)
        result = add_skill(tmp_path, "my-skill", ".cortex/skills/my-skill.md", "A custom skill")
        assert "Registered" in result

        data = json.loads((tmp_path / ".cortex" / "skills.json").read_text())
        names = [s["name"] for s in data["skills"]]
        assert "my-skill" in names

    def test_add_duplicate_skill(self, tmp_path: Path) -> None:
        init_cortex(tmp_path)
        add_skill(tmp_path, "reviewer", ".cortex/skills/reviewer.md")
        result = add_skill(tmp_path, "reviewer", ".cortex/skills/reviewer.md")
        assert "already registered" in result

    def test_add_skill_without_init(self, tmp_path: Path) -> None:
        import json

        result = add_skill(tmp_path, "my-skill", "skills/my-skill.md", "desc")
        assert "Registered" in result
        data = json.loads((tmp_path / ".cortex" / "skills.json").read_text())
        assert len(data["skills"]) == 1
