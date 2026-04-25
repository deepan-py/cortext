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
    """Find the context directory, walking up from cwd."""
    current = Path.cwd()
    while current != current.parent:
        if (current / "context" / "timeline").is_dir():
            return current / "context"
        current = current.parent
    return Path("context")


@app.command()
def init(
    path: Annotated[
        Path,
        typer.Argument(help="Project root directory to initialize."),
    ] = Path("."),
) -> None:
    """Initialize Cortex in a project directory."""
    from cortex.init_project import init_cortex

    actions = init_cortex(path)
    for action in actions:
        err_console.print(f"  {action}")
    err_console.print(
        f"\n[green]✓[/green] Cortex initialized in {path.resolve()}"
    )
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
            "[red]✗[/red] No context/timeline/ directory found. "
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
def version() -> None:
    """Show Cortex version."""
    err_console.print(f"cortex {__version__}")


def main() -> None:
    app()
