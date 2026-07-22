from __future__ import annotations

import json
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import __version__
from .models import CheckStatus, ScanReport
from .scanner import exit_code_for_report, report_to_dict, scan


STATUS_STYLE = {
    CheckStatus.OK: "green",
    CheckStatus.WARN: "yellow",
    CheckStatus.ERROR: "red",
    CheckStatus.SKIP: "dim",
}

STATUS_ICON = {
    CheckStatus.OK: "✓",
    CheckStatus.WARN: "⚠",
    CheckStatus.ERROR: "✗",
    CheckStatus.SKIP: "·",
}


def render_report(console: Console, report: ScanReport) -> None:
    if not report.sources and not report.parse_errors:
        console.print(
            Panel(
                "[yellow]No MCP config files found.[/yellow]\n\n"
                "Expected locations include:\n"
                "  • ~/.cursor/mcp.json\n"
                "  • ~/Library/Application Support/Claude/claude_desktop_config.json\n\n"
                "Pass [bold]--config path/to/mcp.json[/bold] to scan a specific file.",
                title="MCP Doctor",
                border_style="blue",
            )
        )
        return

    summary = Table.grid(padding=(0, 2))
    summary.add_row("Config sources", str(len(report.sources)))
    summary.add_row("Servers scanned", str(len(report.servers)))
    summary.add_row("[green]Healthy[/green]", str(report.ok_count))
    summary.add_row("[yellow]Warnings[/yellow]", str(report.warn_count))
    summary.add_row("[red]Errors[/red]", str(report.error_count))
    console.print(Panel(summary, title=f"MCP Doctor v{__version__}", border_style="blue"))

    if report.parse_errors:
        console.print("\n[bold red]Parse errors[/bold red]")
        for path, error in report.parse_errors:
            console.print(f"  [red]✗[/red] {path}: {error}")

    if report.sources:
        console.print("\n[bold]Config sources[/bold]")
        for source in report.sources:
            console.print(f"  • [cyan]{source.app}[/cyan] → {source.path}")

    if report.servers:
        table = Table(title="\nServer health", show_lines=True)
        table.add_column("Server", style="bold")
        table.add_column("Client")
        table.add_column("Type")
        table.add_column("Status")
        table.add_column("Details")

        for server in report.servers:
            status = server.worst_status
            style = STATUS_STYLE[status]
            icon = STATUS_ICON[status]
            issues = [c for c in server.checks if c.status != CheckStatus.OK]
            if issues:
                detail = "\n".join(
                    f"{STATUS_ICON[c.status]} {c.message}" + (f" ({c.detail})" if c.detail else "")
                    for c in issues
                )
            else:
                detail = "All checks passed"

            table.add_row(
                server.name,
                server.source.app,
                server.server_type.value,
                Text(f"{icon} {status.value}", style=style),
                detail,
            )
        console.print(table)


@click.group(invoke_without_command=True)
@click.option("--config", "configs", multiple=True, type=click.Path(path_type=Path), help="Extra MCP config file")
@click.option("--no-probe", is_flag=True, help="Skip network connectivity checks")
@click.option("--json", "as_json", is_flag=True, help="Output machine-readable JSON")
@click.option("--strict", is_flag=True, help="Exit 1 on warnings as well as errors")
@click.pass_context
def main(ctx: click.Context, configs: tuple[Path, ...], no_probe: bool, as_json: bool, strict: bool) -> None:
    """Diagnose MCP server configs for Cursor, Claude Desktop, and more."""
    if ctx.invoked_subcommand is not None:
        return

    report = scan(extra_paths=list(configs), probe_network=not no_probe)
    if as_json:
        click.echo(json.dumps(report_to_dict(report), indent=2))
    else:
        render_report(Console(), report)

    code = exit_code_for_report(report)
    if strict and report.warn_count:
        code = 1
    raise SystemExit(code)


@main.command("list-configs")
def list_configs() -> None:
    """Show known MCP config locations and whether they exist."""
    from .config import default_config_locations

    table = Table(title="Known MCP config locations")
    table.add_column("Client")
    table.add_column("Path")
    table.add_column("Exists")

    for app, path in default_config_locations():
        exists = path.expanduser().is_file()
        table.add_row(
            app,
            str(path.expanduser()),
            Text("yes", style="green") if exists else Text("no", style="dim"),
        )
    Console().print(table)


@main.command()
@click.argument("config", type=click.Path(exists=True, path_type=Path))
def validate(config: Path) -> None:
    """Validate a single MCP config file and print JSON results."""
    report = scan(extra_paths=[config])
    click.echo(json.dumps(report_to_dict(report), indent=2))
    raise SystemExit(exit_code_for_report(report))


if __name__ == "__main__":
    main()
