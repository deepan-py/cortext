"""Initialize Cortex in a project directory."""

from __future__ import annotations

from importlib.resources import files as resource_files
from pathlib import Path

CONTEXT_DIR = "context"

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

GITIGNORE_ENTRIES = """
# Cortex generated files
context/tensions/
context/graph.json
context/context-graph.html
"""


def _get_template(name: str) -> str:
    """Read a template file bundled with the cortex package."""
    return (
        resource_files("cortex.templates").joinpath(name).read_text(encoding="utf-8")
    )


def init_cortex(project_root: Path) -> list[str]:
    """Initialize Cortex directory structure in the given project root.

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

    # Create empty drift register
    drift_register = root / CONTEXT_DIR / "drift-register.jsonl"
    if not drift_register.exists():
        drift_register.touch()
        actions.append(f"Created {CONTEXT_DIR}/drift-register.jsonl")
    else:
        actions.append(f"Skipped {CONTEXT_DIR}/drift-register.jsonl (already exists)")

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
