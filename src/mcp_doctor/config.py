from __future__ import annotations

import json
import os
from pathlib import Path

from .models import ConfigSource


def _home() -> Path:
    return Path.home()


def default_config_locations() -> list[tuple[str, Path]]:
    """Known MCP config paths across popular AI clients."""
    home = _home()
    candidates: list[tuple[str, Path]] = [
        ("Cursor", home / ".cursor" / "mcp.json"),
        ("Cursor (project)", Path.cwd() / ".cursor" / "mcp.json"),
        (
            "Claude Desktop (macOS)",
            home
            / "Library"
            / "Application Support"
            / "Claude"
            / "claude_desktop_config.json",
        ),
        (
            "Claude Desktop (Linux)",
            home / ".config" / "Claude" / "claude_desktop_config.json",
        ),
        (
            "Claude Desktop (Windows)",
            Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json",
        ),
        ("Windsurf", home / ".codeium" / "windsurf" / "mcp_config.json"),
        ("Generic", home / ".config" / "mcp" / "servers.json"),
    ]
    return candidates


def discover_config_files(extra_paths: list[Path] | None = None) -> list[ConfigSource]:
    seen: set[Path] = set()
    sources: list[ConfigSource] = []

    for app, path in default_config_locations():
        resolved = path.expanduser().resolve()
        if resolved in seen or not resolved.is_file():
            continue
        seen.add(resolved)
        sources.append(ConfigSource(path=resolved, app=app))

    for path in extra_paths or []:
        resolved = path.expanduser().resolve()
        if resolved in seen or not resolved.is_file():
            continue
        seen.add(resolved)
        sources.append(ConfigSource(path=resolved, app="Custom"))

    return sources


def load_mcp_servers(config_path: Path) -> dict[str, dict]:
    """Parse MCP server entries from a config file."""
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Config root must be a JSON object")

    if "mcpServers" in raw:
        servers = raw["mcpServers"]
    elif "servers" in raw:
        servers = raw["servers"]
    else:
        raise ValueError("No 'mcpServers' or 'servers' key found")

    if not isinstance(servers, dict):
        raise ValueError("Server list must be a JSON object")

    normalized: dict[str, dict] = {}
    for name, entry in servers.items():
        if not isinstance(entry, dict):
            raise ValueError(f"Server '{name}' must be an object")
        normalized[str(name)] = entry
    return normalized
