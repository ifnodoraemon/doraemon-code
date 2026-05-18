# Development

## Setup

```bash
git clone https://github.com/ifnodoraemon/dora-code.git
cd dora-code
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Main Commands

测试：

```bash
pytest tests/ -v
pytest tests/ -k "mcp" -v
```

格式和静态检查：

```bash
ruff check src/ tests/
ruff format src/ tests/
mypy src/
```

运行 CLI：

```bash
doraemon
```

运行 Gateway：

```bash
python -m src.gateway.server
```

## Real Provider Checks

最小真实回归：

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

## Repo Structure

只列当前主链：

- `src/agent`
  - agent runtime
- `src/core`
  - config, llm, trace, skills, selector
- `src/host`
  - CLI host, tool registry, MCP runtime
- `src/servers`
  - built-in tools
- `src/gateway`
  - model gateway
- `tests`
  - unit / integration / eval / benchmark tests

## Documentation Rules

更新文档时遵守：

- 不写历史过程
- 不写已经删除或不再使用的模块
- 不把设计愿景写成当前状态
- 用当前代码路径和当前运行方式描述系统
