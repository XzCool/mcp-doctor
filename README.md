# MCP Doctor

**Health checker and diagnostics CLI for [Model Context Protocol (MCP)](https://modelcontextprotocol.io) servers.**

As AI coding assistants (Cursor, Claude Desktop, Windsurf) adopt MCP as the standard plugin layer, developers accumulate dozens of MCP servers — each with its own command, env vars, and network endpoint. When something breaks, you get a silent failure in the IDE with no clear signal about *which* server is misconfigured.

**MCP Doctor** scans your local MCP configs, validates each server entry, and produces an actionable health report in seconds.

## Why MCP tooling is the next hotspot

| Trend | What it means |
|-------|---------------|
| **MCP as the "USB-C for AI"** | Every major AI client is standardizing on MCP for tools, resources, and context |
| **Config sprawl** | Power users run 5–20 MCP servers across multiple apps |
| **Silent failures** | A missing binary or unset env var often shows up only as "tool unavailable" |
| **CI/CD gap** | Teams need to validate MCP configs before shipping to engineers |

MCP Doctor sits in the **observability & diagnostics** layer — the same niche `docker doctor` and `kubectl cluster-info` filled for their ecosystems.

## Features

- **Auto-discovery** — scans Cursor, Claude Desktop, Windsurf, and generic config paths
- **Transport detection** — stdio, SSE, and HTTP servers
- **Actionable checks**
  - Config schema validation
  - Command availability in `$PATH`
  - Missing file paths in args
  - Unset environment variables
  - Network reachability for remote servers
- **Beautiful terminal UI** — powered by [Rich](https://github.com/Textualize/rich)
- **JSON output** — pipe into CI pipelines (`--json`)
- **Zero config** — run once, get a full report

## Install

```bash
pip install mcp-doctor
```

Or from source:

```bash
git clone https://github.com/XzCool/mcp-doctor.git
cd mcp-doctor
pip install -e ".[dev]"
```

## Usage

```bash
# Scan all known MCP config locations
mcp-doctor

# Scan a specific config file
mcp-doctor --config ~/.cursor/mcp.json

# JSON output for CI
mcp-doctor --json

# Skip network probes (faster, offline-friendly)
mcp-doctor --no-probe

# List known config paths
mcp-doctor list-configs

# Validate one file
mcp-doctor validate path/to/mcp.json
```

### Example output

```
╭──────────────────── MCP Doctor v0.1.0 ────────────────────╮
│ Config sources    2                                       │
│ Servers scanned   5                                       │
│ Healthy           3                                       │
│ Warnings          1                                       │
│ Errors            1                                       │
╰───────────────────────────────────────────────────────────╯
```

## Supported config formats

MCP Doctor reads the standard `mcpServers` object used by:

- **Cursor** — `~/.cursor/mcp.json`
- **Claude Desktop** — `claude_desktop_config.json`
- **Windsurf** — `~/.codeium/windsurf/mcp_config.json`
- **Project-level** — `.cursor/mcp.json`

Both **stdio** (`command` + `args`) and **remote** (`url`) transports are supported.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check src tests
```

## License

MIT — see [LICENSE](LICENSE).
