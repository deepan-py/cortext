"""Initialize Cortex in a project directory."""

from __future__ import annotations

import json
from importlib.resources import files as resource_files
from pathlib import Path

CONTEXT_DIR = ".cortex"

DIRS_TO_CREATE = [
    f"{CONTEXT_DIR}/timeline",
    f"{CONTEXT_DIR}/current",
    f"{CONTEXT_DIR}/skills",
]

# template filename → destination path relative to project root
TEMPLATE_MAP = {
    "agent-rules.md": f"{CONTEXT_DIR}/agent-rules.md",
    "review-config.yaml": f"{CONTEXT_DIR}/review-config.yaml",
    "drift-config.yaml": f"{CONTEXT_DIR}/drift-config.yaml",
    "skill-index.md": f"{CONTEXT_DIR}/skills/_index.md",
    "skill-reviewer.md": f"{CONTEXT_DIR}/skills/reviewer.md",
    "skill-context-owner.md": f"{CONTEXT_DIR}/skills/context-owner.md",
}

# AI platform → {template_name: destination_path}
AI_PLATFORM_MAP = {
    "copilot": {
        "copilot-instructions.md": ".github/copilot-instructions.md",
    },
    "claude": {
        "claude-instructions.md": "CLAUDE.md",
    },
}

DEFAULT_SKILLS = [
    {
        "name": "reviewer",
        "path": f"{CONTEXT_DIR}/skills/reviewer.md",
        "description": "PR review criteria for decision records and context quality",
    },
    {
        "name": "context-owner",
        "path": f"{CONTEXT_DIR}/skills/context-owner.md",
        "description": "Drift triage, domain health assessment, weekly review",
    },
]

GITIGNORE_ENTRIES = """
# Cortex generated files
.cortex/tensions/
.cortex/graph.json
.cortex/context-graph.html
"""


def _get_template(name: str) -> str:
    """Read a template file bundled with the cortex package."""
    return (
        resource_files("cortex.templates").joinpath(name).read_text(encoding="utf-8")
    )


SUPPORTED_AI_PLATFORMS = list(AI_PLATFORM_MAP.keys())


def init_cortex(
    project_root: Path,
    ai_platforms: list[str] | None = None,
) -> list[str]:
    """Initialize Cortex directory structure in the given project root.

    Args:
        project_root: Directory to initialize.
        ai_platforms: Optional list of AI platforms (e.g. ['copilot', 'claude']).

    Returns list of actions taken.
    """
    actions: list[str] = []
    root = project_root.resolve()

    # Create directories
    for dir_path in DIRS_TO_CREATE:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            actions.append(f"Created {dir_path}/")
        else:
            actions.append(f"Skipped {dir_path}/ (already exists)")

    # Copy template files
    for template_name, dest_rel in TEMPLATE_MAP.items():
        dest = root / dest_rel
        if dest.exists():
            actions.append(f"Skipped {dest_rel} (already exists)")
            continue
        content = _get_template(template_name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        actions.append(f"Created {dest_rel}")

    # Create skills.json registry
    skills_json = root / CONTEXT_DIR / "skills.json"
    if not skills_json.exists():
        skills_json.write_text(
            json.dumps({"skills": DEFAULT_SKILLS}, indent=2) + "\n",
            encoding="utf-8",
        )
        actions.append(f"Created {CONTEXT_DIR}/skills.json")
    else:
        actions.append(f"Skipped {CONTEXT_DIR}/skills.json (already exists)")

    # Create empty drift register
    drift_register = root / CONTEXT_DIR / "drift-register.jsonl"
    if not drift_register.exists():
        drift_register.touch()
        actions.append(f"Created {CONTEXT_DIR}/drift-register.jsonl")
    else:
        actions.append(f"Skipped {CONTEXT_DIR}/drift-register.jsonl (already exists)")

    # AI platform-specific files
    for platform in (ai_platforms or []):
        if platform not in AI_PLATFORM_MAP:
            continue
        for template_name, dest_rel in AI_PLATFORM_MAP[platform].items():
            dest = root / dest_rel
            if dest.exists():
                actions.append(f"Skipped {dest_rel} (already exists)")
                continue
            content = _get_template(template_name)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
            actions.append(f"Created {dest_rel}")

    # Update .gitignore
    gitignore = root / ".gitignore"
    marker = "# Cortex generated files"

    if gitignore.exists():
        existing = gitignore.read_text(encoding="utf-8")
        if marker not in existing:
            with gitignore.open("a", encoding="utf-8") as f:
                f.write(GITIGNORE_ENTRIES)
            actions.append("Updated .gitignore with Cortex entries")
        else:
            actions.append("Skipped .gitignore (Cortex entries already present)")
    else:
        gitignore.write_text(GITIGNORE_ENTRIES.lstrip(), encoding="utf-8")
        actions.append("Created .gitignore with Cortex entries")

    return actions


def add_skill(
    project_root: Path,
    name: str,
    path: str,
    description: str = "",
) -> str:
    """Register a skill in skills.json.

    Args:
        project_root: Project root directory.
        name: Skill name.
        path: Path to the skill file (relative or absolute).
        description: Short description of the skill.

    Returns action message.
    """
    root = project_root.resolve()
    skills_json = root / CONTEXT_DIR / "skills.json"

    if not skills_json.exists():
        data = {"skills": []}
    else:
        data = json.loads(skills_json.read_text(encoding="utf-8"))

    # Check for duplicate
    for skill in data["skills"]:
        if skill["name"] == name:
            return f"Skill '{name}' already registered in skills.json"

    data["skills"].append({
        "name": name,
        "path": path,
        "description": description,
    })

    skills_json.parent.mkdir(parents=True, exist_ok=True)
    skills_json.write_text(
        json.dumps(data, indent=2) + "\n",
        encoding="utf-8",
    )
    return f"Registered skill '{name}' in {CONTEXT_DIR}/skills.json"
