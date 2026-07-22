import json
from pathlib import Path

import pytest

from mcp_doctor.checks import check_command_exists, check_required_fields, detect_server_type
from mcp_doctor.config import load_mcp_servers
from mcp_doctor.models import CheckStatus, ServerType
from mcp_doctor.scanner import scan


FIXTURE = Path(__file__).parent / "fixtures" / "sample_mcp.json"


def test_load_mcp_servers():
    servers = load_mcp_servers(FIXTURE)
    assert "filesystem" in servers
    assert "remote-api" in servers


def test_detect_server_types():
    servers = load_mcp_servers(FIXTURE)
    assert detect_server_type(servers["filesystem"]) == ServerType.STDIO
    assert detect_server_type(servers["remote-api"]) == ServerType.SSE


def test_stdio_command_check():
    servers = load_mcp_servers(FIXTURE)
    result = check_command_exists(servers["filesystem"])
    assert result.status in (CheckStatus.OK, CheckStatus.ERROR)


def test_missing_command():
    results = check_required_fields("broken", {})
    assert any(r.status == CheckStatus.ERROR for r in results)


def test_scan_fixture(tmp_path: Path):
    report = scan(extra_paths=[FIXTURE], probe_network=False, discover=False)
    assert len(report.servers) == 3
    assert report.parse_errors == []


def test_scan_invalid_json(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    report = scan(extra_paths=[bad], probe_network=False, discover=False)
    assert len(report.parse_errors) == 1
