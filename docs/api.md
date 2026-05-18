# API

本文档只描述当前仍在主链里的运行面。

## Config

项目配置文件：

- `.agent/config.json`

关键字段：

- `model`
- `openai_api_key`
- `openai_api_base`
- `anthropic_api_key`
- `anthropic_api_base`
- `google_api_key`
- `mcp_extensions`
- `mcp_servers`
- `sensitive_tools`

`mcp_servers` 当前支持：

- `name`
- `transport`
- `url`
- `command`
- `args`
- `env`
- `cwd`
- `headers`
- `timeout_seconds`
- `tool_prefix`
- `enabled`

## Modes

产品 mode：

- `plan`
- `review`
- `build`

Mode 只决定默认 built-in capability groups，不决定 provider 或 MCP 行为。

`review` 是只读审查模式，可通过 CLI `/review [--base REF] [paths...]` 临时进入；它不暴露 `write`、`run` 或 `memory_put`。

CLI 还提供两个只读可观测性命令：

- `/tools [all]`：显示当前 registry 的工具策略、审批和 sandbox 分类。
- `/audit [limit]`：显示最近工具策略检查和执行审计。

## Built-in Tools

默认 capability groups：

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

`task` 是统一接口，使用 `task(operation=...)`。

当前支持的 `operation`：

- `create`
- `list`
- `get`
- `update`
- `ready`
- `claim`
- `release`
- `delete`
- `clear`

## Skills

Skills 是 prompt-layer augmentation，不是 tools。

来源：

- `.agent/skills/*/SKILL.md`

当前支持的 metadata：

- `name`
- `description`
- `triggers`
- `priority`
- `requires`
- `files`
- `mode`
- `tools`
- `constraints`

Skills 会按上下文和 mode 激活，并注入 system prompt。

## MCP

MCP 是扩展能力层，不属于默认 built-in 主链。

当前 runtime 支持：

- `streamable_http`
- `stdio`

当前行为：

- 单个 remote MCP server 失败不会拖垮整个 registry
- 支持网络重试
- 支持失败冷却
- `streamable_http` 支持 `mcp-session-id`
- trace 会记录 remote tool source

## Providers

当前 provider 主链：

- OpenAI 官方 SDK
- Anthropic 官方 SDK
- Google 官方 SDK

OpenAI 路径：

- session 级协议锁定
- first successful protocol wins
- provider capability cache

Anthropic 路径：

- 走 `messages`
- 用户可以填 `/v1`
- runtime 自动归一化 base URL

Google 路径：

- 走官方 `google-genai`

## Trace

当前 trace 重点字段：

- `mode`
- `capability_groups`
- `active_tools`
- `active_skills`
- `active_mcp_extensions`

tool call 还会记录来源：

- `built_in`
- `mcp_extension`
- `mcp_remote`

remote MCP tool call 还会带：

- `mcp_server`
- `mcp_transport`
- `remote_tool_name`
