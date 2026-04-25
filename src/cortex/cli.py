"""Cortex CLI — context-aware decision tracking."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from cortex import __version__

app = typer.Typer(
    name="cortex",
    help="Context-aware decision tracking system.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
err_console = Console(stderr=True)
out_console = Console()


def _find_context_dir() -> Path:
    """Find the .cortex directory, walking up from cwd."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".cortex" / "timeline").is_dir():
            return current / ".cortex"
        current = current.parent
    return Path(".cortex")


@app.command()
def init(
    path: Annotated[
        Path,
        typer.Argument(help="Project root directory to initialize."),
    ] = Path("."),
    ai: Annotated[
        Optional[str],
        typer.Option(
            "--ai",
            help="AI platforms to configure, comma-separated (copilot, claude).",
        ),
    ] = None,
) -> None:
    """Initialize Cortex in a project directory."""
    from cortex.init_project import SUPPORTED_AI_PLATFORMS, init_cortex

    ai_platforms: list[str] = []
    if ai:
        ai_platforms = [p.strip() for p in ai.split(",") if p.strip()]
        invalid = [p for p in ai_platforms if p not in SUPPORTED_AI_PLATFORMS]
        if invalid:
            err_console.print(
                f"[red]✗[/red] Unknown AI platform(s): {', '.join(invalid)}. "
                f"Supported: {', '.join(SUPPORTED_AI_PLATFORMS)}"
            )
            raise typer.Exit(1)

    actions = init_cortex(path, ai_platforms=ai_platforms or None)
    for action in actions:
        err_console.print(f"  {action}")
    err_console.print(
        f"\n[green]✓[/green] Cortex initialized in {path.resolve()}"
    )
    if ai_platforms:
        err_console.print(f"  AI platforms: [bold]{', '.join(ai_platforms)}[/bold]")
    err_console.print(
        "  Next: [bold]cortex new --domain <domain>[/bold] to create your first decision"
    )


@app.command()
def new(
    domain: Annotated[
        str, typer.Option("--domain", "-d", help="Domain for this decision.")
    ],
    parent: Annotated[
        Optional[str],
        typer.Option("--parent", "-p", help="Parent decision ID."),
    ] = None,
    author: Annotated[
        str,
        typer.Option("--author", "-a", help="Author type: human or ai."),
    ] = "human",
) -> None:
    """Create a new decision record skeleton."""
    ctx_dir = _find_context_dir()
    timeline_dir = ctx_dir / "timeline"

    if not timeline_dir.exists():
        err_console.print(
            "[red]✗[/red] No .cortex/timeline/ directory found. "
            "Run [bold]cortex init[/bold] first."
        )
        raise typer.Exit(1)

    today = date.today()
    date_str = today.isoformat()

    # Find next available ID for today
    existing = sorted(timeline_dir.glob(f"{date_str}-*.yaml"))
    if existing:
        last_num = max(int(f.stem.rsplit("-", 1)[-1]) for f in existing)
        next_num = last_num + 1
    else:
        next_num = 1

    decision_id = f"{date_str}-{next_num:03d}"

    # Build skeleton YAML
    parents_yaml = f'\n  - "{parent}"' if parent else " []"

    skeleton = (
        f'id: "{decision_id}"\n'
        f"status: active\n"
        f'date: "{date_str}"\n'
        f"author: {author}\n"
        f"domains:\n"
        f"  - {domain}\n"
        f"\n"
        f"decision: >\n"
        f"  TODO: What was decided. One paragraph. Concrete and specific.\n"
        f"\n"
        f"context: >\n"
        f"  TODO: Why this was needed. What problem forced this decision.\n"
        f"\n"
        f"parents:{parents_yaml}\n"
        f"\n"
        f"alternatives_rejected: []\n"
        f"\n"
        f"assumptions: []\n"
        f"\n"
        f"tensions: []\n"
        f"\n"
        f"tags: []\n"
    )

    filepath = timeline_dir / f"{decision_id}.yaml"
    filepath.write_text(skeleton, encoding="utf-8")

    err_console.print(f"[green]✓[/green] Created {filepath}")
    err_console.print("  Edit the file and fill in the decision details.")


@app.command()
def validate() -> None:
    """Validate all decision records against the schema."""
    from cortex.validate import validate_timeline

    ctx_dir = _find_context_dir()
    timeline_dir = ctx_dir / "timeline"

    result = validate_timeline(timeline_dir)

    for issue in result.errors:
        field_str = f" [{issue.field}]" if issue.field else ""
        err_console.print(
            f"[red]✗[/red] {issue.file}{field_str}: {issue.message}"
        )

    for issue in result.warnings:
        field_str = f" [{issue.field}]" if issue.field else ""
        err_console.print(
            f"[yellow]⚠[/yellow] {issue.file}{field_str}: {issue.message}"
        )

    if result.is_valid:
        err_console.print(
            f"[green]✓[/green] {result.valid_count}/{result.total_count} "
            f"decision record(s) valid"
        )
    else:
        err_console.print(
            f"\n[red]✗[/red] Validation failed: "
            f"{len(result.errors)} error(s), {len(result.warnings)} warning(s)"
        )
        raise typer.Exit(1)


@app.command()
def schema() -> None:
    """Export the decision record JSON Schema to stdout."""
    from cortex.models import DecisionRecord

    schema_dict = DecisionRecord.model_json_schema(by_alias=True)
    out_console.print_json(json.dumps(schema_dict, indent=2))


@app.command()
def show(
    domain: Annotated[
        str, typer.Argument(help="Domain name to show decisions for.")
    ],
    all_: Annotated[
        bool,
        typer.Option("--all", "-a", help="Include superseded decisions."),
    ] = False,
) -> None:
    """Show active decisions for a domain."""
    from cortex.validate import load_all_records

    ctx_dir = _find_context_dir()
    timeline_dir = ctx_dir / "timeline"

    if not timeline_dir.exists():
        err_console.print(
            "[red]✗[/red] No .cortex/timeline/ directory found. "
            "Run [bold]cortex init[/bold] first."
        )
        raise typer.Exit(1)

    records = load_all_records(timeline_dir)
    matched = [
        r for r in records.values()
        if domain in r.domains and (all_ or r.status.value == "active")
    ]

    if not matched:
        status_label = "any" if all_ else "active"
        err_console.print(
            f"[yellow]⚠[/yellow] No {status_label} decisions found for domain '{domain}'"
        )
        return

    matched.sort(key=lambda r: r.id)
    err_console.print(f"\n[bold]Domain: {domain}[/bold]")
    err_console.print(f"{'─' * 60}")

    for r in matched:
        status_style = "green" if r.status.value == "active" else "dim"
        err_console.print(
            f"  [{status_style}]{r.status.value:>10}[/{status_style}]  "
            f"[bold]{r.id}[/bold]  {r.decision[:70]}"
        )
        if r.tensions:
            for t in r.tensions:
                err_console.print(f"             [yellow]⚡ {t}[/yellow]")

    err_console.print(f"\n  {len(matched)} decision(s)")


@app.command()
def status() -> None:
    """Show a summary dashboard of the Cortex context system."""
    from cortex.validate import load_all_records

    ctx_dir = _find_context_dir()
    timeline_dir = ctx_dir / "timeline"

    if not timeline_dir.exists():
        err_console.print(
            "[red]✗[/red] No .cortex/timeline/ directory found. "
            "Run [bold]cortex init[/bold] first."
        )
        raise typer.Exit(1)

    records = load_all_records(timeline_dir)

    if not records:
        err_console.print("[yellow]⚠[/yellow] No decision records found.")
        return

    active = [r for r in records.values() if r.status.value == "active"]
    superseded = [r for r in records.values() if r.status.value == "superseded"]

    # Collect domains
    domains: dict[str, list[str]] = {}
    for r in records.values():
        for d in r.domains:
            domains.setdefault(d, []).append(r.id)

    # Unreviewed AI decisions
    unreviewed_ai = [
        r for r in active
        if r.author.value == "ai" and r.reviewed_by is None
    ]

    err_console.print("\n[bold]Cortex Status[/bold]")
    err_console.print(f"{'─' * 40}")
    err_console.print(f"  Total decisions:    {len(records)}")
    err_console.print(f"  Active:             [green]{len(active)}[/green]")
    err_console.print(f"  Superseded:         [dim]{len(superseded)}[/dim]")
    err_console.print(f"  Domains:            {len(domains)}")
    if unreviewed_ai:
        err_console.print(
            f"  Unreviewed AI:      [yellow]{len(unreviewed_ai)}[/yellow]"
        )

    err_console.print(f"\n[bold]Domains[/bold]")
    for d_name in sorted(domains):
        d_ids = domains[d_name]
        active_count = sum(
            1 for rid in d_ids
            if records[rid].status.value == "active"
        )
        err_console.print(
            f"  {d_name}: {active_count} active / {len(d_ids)} total"
        )

    # Drift register summary
    drift_register = ctx_dir / "drift-register.jsonl"
    if drift_register.exists():
        lines = [
            l for l in drift_register.read_text(encoding="utf-8").splitlines()
            if l.strip()
        ]
        if lines:
            err_console.print(
                f"\n  [yellow]⚠ {len(lines)} drift entries pending review[/yellow]"
            )

    err_console.print()


@app.command()
def supersede(
    decision_id: Annotated[
        str, typer.Argument(help="ID of the decision to supersede.")
    ],
    domain: Annotated[
        Optional[str],
        typer.Option("--domain", "-d", help="Domain for the new decision (defaults to parent's domain)."),
    ] = None,
    author: Annotated[
        str,
        typer.Option("--author", "-a", help="Author type: human or ai."),
    ] = "human",
) -> None:
    """Supersede an existing decision: mark it superseded and create a child."""
    import yaml

    ctx_dir = _find_context_dir()
    timeline_dir = ctx_dir / "timeline"

    if not timeline_dir.exists():
        err_console.print(
            "[red]✗[/red] No .cortex/timeline/ directory found. "
            "Run [bold]cortex init[/bold] first."
        )
        raise typer.Exit(1)

    parent_path = timeline_dir / f"{decision_id}.yaml"
    if not parent_path.exists():
        err_console.print(
            f"[red]✗[/red] Decision '{decision_id}' not found at {parent_path}"
        )
        raise typer.Exit(1)

    # Load parent
    raw = parent_path.read_text(encoding="utf-8")
    parent_data = yaml.safe_load(raw)

    if parent_data.get("status") == "superseded":
        err_console.print(
            f"[yellow]⚠[/yellow] Decision '{decision_id}' is already superseded."
        )
        raise typer.Exit(1)

    # Mark parent as superseded
    parent_data["status"] = "superseded"
    parent_path.write_text(
        yaml.dump(parent_data, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    err_console.print(
        f"[dim]  Marked {decision_id} as superseded[/dim]"
    )

    # Create child decision
    child_domain = domain or parent_data.get("domains", ["unknown"])[0]
    today = date.today()
    date_str = today.isoformat()

    existing = sorted(timeline_dir.glob(f"{date_str}-*.yaml"))
    if existing:
        last_num = max(int(f.stem.rsplit("-", 1)[-1]) for f in existing)
        next_num = last_num + 1
    else:
        next_num = 1

    child_id = f"{date_str}-{next_num:03d}"

    skeleton = (
        f'id: "{child_id}"\n'
        f"status: active\n"
        f'date: "{date_str}"\n'
        f"author: {author}\n"
        f"domains:\n"
        f"  - {child_domain}\n"
        f"\n"
        f"decision: >\n"
        f"  TODO: What replaces {decision_id}. Be specific about what changed.\n"
        f"\n"
        f"context: >\n"
        f"  TODO: Why {decision_id} needed to be superseded.\n"
        f"\n"
        f"parents:\n"
        f'  - "{decision_id}"\n'
        f"\n"
        f"alternatives_rejected: []\n"
        f"\n"
        f"assumptions: []\n"
        f"\n"
        f"tensions: []\n"
        f"\n"
        f"tags: []\n"
    )

    child_path = timeline_dir / f"{child_id}.yaml"
    child_path.write_text(skeleton, encoding="utf-8")

    err_console.print(f"[green]✓[/green] Created {child_path}")
    err_console.print(
        f"  Supersedes [bold]{decision_id}[/bold]. "
        f"Edit the new decision and fill in the details."
    )


# --- Hook subcommand group ---
hook_app = typer.Typer(
    name="hook",
    help="Manage git hooks for Cortex.",
    no_args_is_help=True,
)
app.add_typer(hook_app)


@hook_app.command("install")
def hook_install(
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite existing pre-commit hook."),
    ] = False,
) -> None:
    """Install a git pre-commit hook that runs cortex validate."""
    ctx_dir = _find_context_dir()
    project_root = ctx_dir.parent

    git_dir = project_root / ".git"
    if not git_dir.is_dir():
        err_console.print(
            "[red]✗[/red] No .git/ directory found. "
            "Initialize a git repository first."
        )
        raise typer.Exit(1)

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    hook_path = hooks_dir / "pre-commit"

    hook_script = (
        "#!/usr/bin/env sh\n"
        '# Cortex pre-commit hook — validates decision records\n'
        "\n"
        "# Check if any decision records are staged\n"
        'STAGED_YAML=$(git diff --cached --name-only --diff-filter=ACM '
        '| grep -E "^\\.cortex/timeline/.*\\.yaml$" || true)\n'
        "\n"
        'if [ -n "$STAGED_YAML" ]; then\n'
        '    echo "Cortex: validating decision records..."\n'
        "    cortex validate\n"
        '    if [ $? -ne 0 ]; then\n'
        '        echo "Cortex: validation failed. Fix errors or commit with --no-verify"\n'
        "        exit 1\n"
        "    fi\n"
        "fi\n"
    )

    if hook_path.exists() and not force:
        existing = hook_path.read_text(encoding="utf-8")
        if "cortex validate" in existing:
            err_console.print(
                "[yellow]⚠[/yellow] Pre-commit hook already contains cortex validate."
            )
            return

        # Append to existing hook
        with hook_path.open("a", encoding="utf-8") as f:
            f.write(
                "\n# --- Cortex validation (appended) ---\n"
                + hook_script.split("\n", 2)[2]  # skip shebang and comment
            )
        err_console.print(
            "[green]✓[/green] Appended cortex validate to existing pre-commit hook."
        )
    else:
        hook_path.write_text(hook_script, encoding="utf-8")
        hook_path.chmod(0o755)
        err_console.print(
            "[green]✓[/green] Installed pre-commit hook at .git/hooks/pre-commit"
        )


@hook_app.command("uninstall")
def hook_uninstall() -> None:
    """Remove the Cortex pre-commit hook."""
    ctx_dir = _find_context_dir()
    project_root = ctx_dir.parent

    hook_path = project_root / ".git" / "hooks" / "pre-commit"
    if not hook_path.exists():
        err_console.print("[yellow]⚠[/yellow] No pre-commit hook found.")
        return

    content = hook_path.read_text(encoding="utf-8")
    if "cortex validate" not in content:
        err_console.print(
            "[yellow]⚠[/yellow] Pre-commit hook does not contain cortex validate."
        )
        return

    # If it's purely our hook, remove the file. If mixed, warn.
    if "Cortex pre-commit hook" in content and content.count("cortex") <= 3:
        hook_path.unlink()
        err_console.print(
            "[green]✓[/green] Removed pre-commit hook."
        )
    else:
        err_console.print(
            "[yellow]⚠[/yellow] Pre-commit hook contains other commands. "
            "Please remove the cortex section manually from .git/hooks/pre-commit"
        )


@app.command()
def version() -> None:
    """Show Cortex version."""
    err_console.print(f"cortex {__version__}")


# --- Skill subcommand group ---
skill_app = typer.Typer(
    name="skill",
    help="Manage Cortex skills.",
    no_args_is_help=True,
)
app.add_typer(skill_app)


@skill_app.command("add")
def skill_add(
    name: Annotated[
        str, typer.Argument(help="Skill name.")
    ],
    path: Annotated[
        str, typer.Argument(help="Path to the skill file (relative or absolute).")
    ],
    description: Annotated[
        str,
        typer.Option("--description", "-d", help="Short description of the skill."),
    ] = "",
) -> None:
    """Register a new skill in the skills.json registry."""
    from cortex.init_project import add_skill

    ctx_dir = _find_context_dir()
    project_root = ctx_dir.parent

    if not ctx_dir.exists():
        err_console.print(
            "[red]✗[/red] No .cortex/ directory found. "
            "Run [bold]cortex init[/bold] first."
        )
        raise typer.Exit(1)

    result = add_skill(project_root, name, path, description)
    err_console.print(f"[green]✓[/green] {result}")


@skill_app.command("list")
def skill_list() -> None:
    """List all registered skills from skills.json."""
    ctx_dir = _find_context_dir()
    skills_json = ctx_dir / "skills.json"

    if not skills_json.exists():
        err_console.print(
            "[yellow]⚠[/yellow] No skills.json found. "
            "Run [bold]cortex init[/bold] first."
        )
        raise typer.Exit(1)

    data = json.loads(skills_json.read_text(encoding="utf-8"))
    skills = data.get("skills", [])

    if not skills:
        err_console.print("No skills registered.")
        return

    for skill in skills:
        desc = f" — {skill['description']}" if skill.get("description") else ""
        err_console.print(f"  [bold]{skill['name']}[/bold] ({skill['path']}){desc}")


def main() -> None:
    app()
