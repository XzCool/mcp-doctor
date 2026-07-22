# MCP Doctor

[English](README.md) | **简体中文**

**面向 [Model Context Protocol (MCP)](https://modelcontextprotocol.io) 服务器的健康检查与诊断 CLI 工具。**

随着 Cursor、Claude Desktop、Windsurf 等 AI 编程助手将 MCP 作为标准插件层，开发者往往会配置大量 MCP 服务器——每个都有独立的启动命令、环境变量和网络端点。一旦出问题，IDE 里通常只会静默失败，很难判断**到底是哪个服务器**配置有误。

**MCP Doctor** 会扫描本机 MCP 配置文件，逐项校验每个服务器，并在几秒内生成可操作的诊断报告。

## 为什么 MCP 诊断工具是下一个热点

| 趋势 | 含义 |
|------|------|
| **MCP 成为 AI 的「USB-C」** | 主流 AI 客户端都在用 MCP 统一接入工具、资源和上下文 |
| **配置膨胀** | 重度用户往往在多个应用中运行 5–20 个 MCP 服务器 |
| **静默失败** | 缺少二进制文件或未设置环境变量，常常只表现为「工具不可用」 |
| **CI/CD 空白** | 团队需要在分发给工程师之前，先验证 MCP 配置是否正确 |

MCP Doctor 定位于 **可观测性与诊断层**——就像 `docker doctor` 和 `kubectl cluster-info` 在各自生态中扮演的角色。

## 功能特性

- **自动发现** — 扫描 Cursor、Claude Desktop、Windsurf 及通用配置路径
- **传输协议识别** — 支持 stdio、SSE、HTTP 服务器
- **可操作的检查项**
  - 配置结构校验
  - 启动命令是否在 `$PATH` 中
  - args 中引用的文件路径是否存在
  - 环境变量是否已设置
  - 远程服务器的网络连通性
- **美观的终端界面** — 基于 [Rich](https://github.com/Textualize/rich)
- **JSON 输出** — 可接入 CI 流水线（`--json`）
- **零配置** — 运行一次，即可获得完整报告

## 安装

```bash
pip install mcp-doctor
```

或从源码安装：

```bash
git clone https://github.com/XzCool/mcp-doctor.git
cd mcp-doctor
pip install -e ".[dev]"
```

## 使用方法

```bash
# 扫描所有已知的 MCP 配置位置
mcp-doctor

# 扫描指定配置文件
mcp-doctor --config ~/.cursor/mcp.json

# JSON 格式输出（适合 CI）
mcp-doctor --json

# 跳过网络探测（更快，适合离线环境）
mcp-doctor --no-probe

# 列出已知的配置路径
mcp-doctor list-configs

# 校验单个配置文件
mcp-doctor validate path/to/mcp.json
```

### 输出示例

```
╭──────────────────── MCP Doctor v0.1.0 ────────────────────╮
│ Config sources    2                                       │
│ Servers scanned   5                                       │
│ Healthy           3                                       │
│ Warnings          1                                       │
│ Errors            1                                       │
╰───────────────────────────────────────────────────────────╯
```

## 支持的配置格式

MCP Doctor 读取标准的 `mcpServers` 配置对象，支持以下客户端：

- **Cursor** — `~/.cursor/mcp.json`
- **Claude Desktop** — `claude_desktop_config.json`
- **Windsurf** — `~/.codeium/windsurf/mcp_config.json`
- **项目级配置** — `.cursor/mcp.json`

同时支持 **stdio**（`command` + `args`）和 **远程**（`url`）两种传输方式。

## 开发

```bash
pip install -e ".[dev]"
pytest
ruff check src tests
```

## 许可证

MIT — 详见 [LICENSE](LICENSE)。
