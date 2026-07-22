from __future__ import annotations

import shutil
import socket
from pathlib import Path
from urllib.parse import urlparse

import httpx

from .models import CheckResult, CheckStatus, ServerType


def detect_server_type(entry: dict) -> ServerType:
    if entry.get("command"):
        return ServerType.STDIO
    url = entry.get("url") or entry.get("serverUrl") or entry.get("endpoint")
    if not url:
        return ServerType.UNKNOWN
    parsed = urlparse(str(url))
    path = (parsed.path or "").lower()
    if path.endswith("/sse") or "sse" in path:
        return ServerType.SSE
    return ServerType.HTTP


def check_required_fields(name: str, entry: dict) -> list[CheckResult]:
    results: list[CheckResult] = []
    server_type = detect_server_type(entry)

    if server_type == ServerType.STDIO:
        command = entry.get("command")
        if not command:
            results.append(
                CheckResult(
                    name="config",
                    status=CheckStatus.ERROR,
                    message="Missing 'command' for stdio server",
                )
            )
        else:
            results.append(
                CheckResult(
                    name="config",
                    status=CheckStatus.OK,
                    message=f"stdio server via `{command}`",
                )
            )
    elif server_type in (ServerType.SSE, ServerType.HTTP):
        url = entry.get("url") or entry.get("serverUrl") or entry.get("endpoint")
        results.append(
            CheckResult(
                name="config",
                status=CheckStatus.OK,
                message=f"{server_type.value} server at {url}",
            )
        )
    else:
        results.append(
            CheckResult(
                name="config",
                status=CheckStatus.ERROR,
                message="Unrecognized server transport (need command or url)",
            )
        )
    return results


def check_command_exists(entry: dict) -> CheckResult:
    command = entry.get("command")
    if not command:
        return CheckResult(
            name="command",
            status=CheckStatus.SKIP,
            message="Not a stdio server",
        )

    cmd_path = shutil.which(str(command))
    if cmd_path:
        return CheckResult(
            name="command",
            status=CheckStatus.OK,
            message=f"Command found: {cmd_path}",
        )

    return CheckResult(
        name="command",
        status=CheckStatus.ERROR,
        message=f"Command not found in PATH: {command}",
        detail="Install the runtime or add it to your PATH",
    )


def check_args_paths(entry: dict) -> list[CheckResult]:
    results: list[CheckResult] = []
    args = entry.get("args") or []
    if not isinstance(args, list):
        return [
            CheckResult(
                name="args",
                status=CheckStatus.ERROR,
                message="'args' must be a list",
            )
        ]

    for arg in args:
        if not isinstance(arg, str):
            continue
        candidate = Path(arg).expanduser()
        if candidate.is_absolute() and not candidate.exists():
            results.append(
                CheckResult(
                    name="path",
                    status=CheckStatus.WARN,
                    message=f"Referenced path does not exist: {arg}",
                )
            )
    return results


def check_env_vars(entry: dict) -> list[CheckResult]:
    results: list[CheckResult] = []
    env = entry.get("env") or {}
    if not isinstance(env, dict):
        return [
            CheckResult(
                name="env",
                status=CheckStatus.ERROR,
                message="'env' must be an object",
            )
        ]

    for key, value in env.items():
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            var_name = value[2:-1]
            if var_name not in __import__("os").environ:
                results.append(
                    CheckResult(
                        name="env",
                        status=CheckStatus.WARN,
                        message=f"Environment variable not set: {var_name}",
                        detail=f"Referenced as {key}={value}",
                    )
                )
    return results


def check_remote_url(entry: dict, timeout: float = 5.0) -> CheckResult:
    url = entry.get("url") or entry.get("serverUrl") or entry.get("endpoint")
    if not url:
        return CheckResult(
            name="connectivity",
            status=CheckStatus.SKIP,
            message="Not a remote server",
        )

    parsed = urlparse(str(url))
    if not parsed.scheme or not parsed.hostname:
        return CheckResult(
            name="connectivity",
            status=CheckStatus.ERROR,
            message=f"Invalid URL: {url}",
        )

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((parsed.hostname, port), timeout=timeout):
            pass
    except OSError as exc:
        return CheckResult(
            name="connectivity",
            status=CheckStatus.ERROR,
            message=f"Cannot reach {parsed.hostname}:{port}",
            detail=str(exc),
        )

    try:
        response = httpx.get(str(url), timeout=timeout, follow_redirects=True)
        if response.status_code >= 500:
            return CheckResult(
                name="connectivity",
                status=CheckStatus.WARN,
                message=f"Server reachable but returned HTTP {response.status_code}",
            )
        return CheckResult(
            name="connectivity",
            status=CheckStatus.OK,
            message=f"Reachable (HTTP {response.status_code})",
        )
    except httpx.HTTPError as exc:
        # TCP works but HTTP handshake may fail for SSE-only endpoints — still useful signal.
        return CheckResult(
            name="connectivity",
            status=CheckStatus.WARN,
            message="Host reachable; HTTP probe inconclusive",
            detail=str(exc),
        )
