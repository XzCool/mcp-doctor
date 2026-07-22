from __future__ import annotations

from pathlib import Path

from .checks import (
    check_args_paths,
    check_command_exists,
    check_env_vars,
    check_remote_url,
    check_required_fields,
    detect_server_type,
)
from .config import discover_config_files, load_mcp_servers
from .models import CheckStatus, ConfigSource, ScanReport, ServerReport


def scan(
    extra_paths: list[Path] | None = None,
    probe_network: bool = True,
    discover: bool = True,
) -> ScanReport:
    report = ScanReport()
    sources = discover_config_files(extra_paths) if discover else []
    if not discover and extra_paths:
        seen: set[Path] = set()
        for path in extra_paths:
            resolved = path.expanduser().resolve()
            if resolved in seen or not resolved.is_file():
                continue
            seen.add(resolved)
            sources.append(ConfigSource(path=resolved, app="Custom"))
    report.sources = sources

    for source in sources:
        try:
            servers = load_mcp_servers(source.path)
        except (OSError, ValueError) as exc:
            report.parse_errors.append((source.path, str(exc)))
            continue

        for name, entry in servers.items():
            server_report = ServerReport(
                name=name,
                source=source,
                server_type=detect_server_type(entry),
            )
            server_report.checks.extend(check_required_fields(name, entry))
            server_report.checks.append(check_command_exists(entry))
            server_report.checks.extend(check_args_paths(entry))
            server_report.checks.extend(check_env_vars(entry))
            if probe_network:
                server_report.checks.append(check_remote_url(entry))
            report.servers.append(server_report)

    return report


def report_to_dict(report: ScanReport) -> dict:
    return {
        "summary": {
            "sources": len(report.sources),
            "servers": len(report.servers),
            "ok": report.ok_count,
            "warnings": report.warn_count,
            "errors": report.error_count,
            "parse_errors": len(report.parse_errors),
        },
        "sources": [{"app": s.app, "path": str(s.path)} for s in report.sources],
        "parse_errors": [{"path": str(p), "error": e} for p, e in report.parse_errors],
        "servers": [
            {
                "name": s.name,
                "app": s.source.app,
                "config": str(s.source.path),
                "type": s.server_type.value,
                "status": s.worst_status.value,
                "checks": [
                    {
                        "name": c.name,
                        "status": c.status.value,
                        "message": c.message,
                        "detail": c.detail,
                    }
                    for c in s.checks
                ],
            }
            for s in report.servers
        ],
    }


def exit_code_for_report(report: ScanReport) -> int:
    if report.parse_errors or report.error_count:
        return 1
    if report.warn_count:
        return 0
    return 0
