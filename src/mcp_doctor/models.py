from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ServerType(str, Enum):
    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"
    UNKNOWN = "unknown"


class CheckStatus(str, Enum):
    OK = "ok"
    WARN = "warn"
    ERROR = "error"
    SKIP = "skip"


@dataclass
class ConfigSource:
    path: Path
    app: str


@dataclass
class CheckResult:
    name: str
    status: CheckStatus
    message: str
    detail: str | None = None


@dataclass
class ServerReport:
    name: str
    source: ConfigSource
    server_type: ServerType
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def worst_status(self) -> CheckStatus:
        order = {
            CheckStatus.ERROR: 0,
            CheckStatus.WARN: 1,
            CheckStatus.SKIP: 2,
            CheckStatus.OK: 3,
        }
        if not self.checks:
            return CheckStatus.SKIP
        return min(self.checks, key=lambda c: order[c.status]).status


@dataclass
class ScanReport:
    sources: list[ConfigSource] = field(default_factory=list)
    servers: list[ServerReport] = field(default_factory=list)
    parse_errors: list[tuple[Path, str]] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for s in self.servers if s.worst_status == CheckStatus.ERROR)

    @property
    def warn_count(self) -> int:
        return sum(1 for s in self.servers if s.worst_status == CheckStatus.WARN)

    @property
    def ok_count(self) -> int:
        return sum(1 for s in self.servers if s.worst_status == CheckStatus.OK)
