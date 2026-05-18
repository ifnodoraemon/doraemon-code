# Doraemon Code

本项目是一个本地运行的 coding agent，主入口是 CLI，运行模式包括：

- `plan`
- `review`
- `build`

当前主链已经支持：

- OpenAI / Anthropic / Google 官方 SDK 直连
- OpenAI-compatible 上游
- built-in tools
- skills
- 本地扩展组和远端 MCP servers

## System Overview

```text
                    +------------------+
                    |   User / CLI     |
                    +---------+--------+
                              |
                              v
                    +------------------+
                    | Mode: plan/review|
                    |       /build     |
                    +---------+--------+
                              |
          +-------------------+-------------------+
          |                                       |
          v                                       v
 +--------------------+                 +--------------------+
 | Built-in Tools     |                 | Skills            |
 | read/edit/memory   |                 | prompt activation |
 | research/task      |                 +--------------------+
 +----------+---------+
            |
            v
 +--------------------+        +-----------------------------+
 | Agent Runtime      |<------>| MCP Extensions             |
 | state/trace/loops  |        | local groups + remote MCP  |
 +----------+---------+        +-----------------------------+
            |
            v
 +--------------------+
 | Model Providers    |
 | OpenAI/Anthropic   |
 | Google             |
 +--------------------+
```

## Quick Start

```bash
git clone https://github.com/ifnodoraemon/dora-code.git
cd dora-code
pip install -e .
cp .env.example .env
mkdir -p .agent
```

最小配置示例：

```json
{
  "model": "gpt-5.4",
  "openai_api_key": "YOUR_KEY",
  "openai_api_base": "https://www.packyapi.com/v1"
}
```

启动：

```bash
doraemon
```

## Runtime Model

产品层 mode：

- `plan`
- `review`
- `build`

默认 built-in capability groups：

- `plan`
  - `read`
  - `memory`
  - `research`
  - `task`

- `review`
  - `read`
  - `research`
  - `task`

- `build`
  - `read`
  - `edit`
  - `memory`
  - `research`
  - `task`

对应工具名：

- `read`
  - `read`
  - `search`
  - `ask_user`
- `edit`
  - `write`
  - `run`
- `memory`
  - `memory_get`
  - `memory_put`
  - `memory_search`
  - `memory_list`
- `research`
  - `web_search`
  - `web_fetch`
- `task`
  - `task`

Browser / database 不在默认主链里，只能通过 MCP 扩展接入。

## CLI Review And Policy Commands

- `/review [--base REF] [paths...]`：临时进入只读 review 模式，对工作区变更或指定路径做代码审查。
- `/tools [all]`：查看当前 mode 下工具可见性、审批要求和 sandbox 分类。
- `/audit [limit]`：查看最近工具策略检查和执行审计。

## Provider Config

OpenAI-compatible：

```json
{
  "model": "gpt-5.4",
  "openai_api_key": "YOUR_KEY",
  "openai_api_base": "https://provider.example.com/v1"
}
```

Anthropic-compatible：

```json
{
  "model": "claude-sonnet-4-6",
  "anthropic_api_key": "YOUR_KEY",
  "anthropic_api_base": "https://provider.example.com/v1"
}
```

Anthropic 的 base URL 用户仍然填到 `/v1`，运行时会自动归一化，避免 SDK 拼成重复路径。

Google：

```json
{
  "model": "gemini-3.1-pro-preview",
  "google_api_key": "YOUR_KEY"
}
```

## MCP Config

远端 MCP server 配在 `.agent/config.json` 的 `mcp_servers`。

Context7：

```json
{
  "mcp_servers": [
    {
      "name": "context7",
      "transport": "streamable_http",
      "url": "https://mcp.context7.com/mcp",
      "headers": {
        "CONTEXT7_API_KEY": "YOUR_CONTEXT7_API_KEY"
      },
      "tool_prefix": "context7",
      "enabled": true
    }
  ]
}
```

GitHub：

```json
{
  "mcp_servers": [
    {
      "name": "github",
      "transport": "streamable_http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {
        "Authorization": "Bearer YOUR_GITHUB_TOKEN"
      },
      "tool_prefix": "github",
      "enabled": true
    }
  ]
}
```

建议总是设置 `tool_prefix`。

当前远端 MCP runtime 支持：

- `streamable_http`
- `stdio`

并具备：

- fail-open
- 重试
- 会话复用
- 失败冷却
- trace source 标记

## Real Validation

当前已真实验证过：

- Packy `gpt-5.4`
- GitHub MCP
- Context7 MCP

最小真实回归命令：

```bash
REAL_API_BASE='https://www.packyapi.com/v1' \
REAL_API_KEY='YOUR_KEY' \
REAL_MODEL='gpt-5.4' \
python3 scripts/run_evals.py --category basic
```

真实 benchmark：

```bash
REAL_API_BASE='https://www.packyapi.com/v1' \
REAL_API_KEY='YOUR_KEY' \
REAL_MODEL='gpt-5.4' \
python3 scripts/run_benchmark.py --suite real_repo --limit 5
```

## Runtime Flow

```text
user input
   |
   v
select mode
   |
   v
resolve built-in capability groups
   |
   +--> activate relevant skills
   |
   +--> attach enabled MCP extensions / servers
   |
   v
build model-visible tool list
   |
   v
LLM call
   |
   +--> text response
   |
   +--> tool call
           |
           v
      execute built-in or MCP tool
           |
           v
      append tool result
           |
           v
        next LLM turn
```

## Documentation

- [Architecture](docs/architecture.md)
- [API](docs/api.md)
- [Development](docs/development.md)
- [Contributing](CONTRIBUTING.md)
