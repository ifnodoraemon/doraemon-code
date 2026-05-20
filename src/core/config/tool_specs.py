"""
Tool Specifications
"""

from dataclasses import dataclass

@dataclass
class ToolSpec:
    """Declarative specification for a tool to register."""
    module: str
    func_name: str
    name: str | None = None
    sensitive: bool = False
    timeout: float = 60.0
    critical: bool = False

BUILTIN_TOOL_SPECS: list[ToolSpec] = [
    ToolSpec("src.servers.filesystem", "read",          sensitive=False, timeout=60.0,  critical=True),
    ToolSpec("src.servers.filesystem", "write",         sensitive=True,  timeout=120.0, critical=True),
    ToolSpec("src.servers.filesystem", "search",        sensitive=False, timeout=120.0, critical=True),
    ToolSpec("src.servers.filesystem", "notebook_read", sensitive=False, timeout=60.0,  critical=True),
    ToolSpec("src.servers.filesystem", "notebook_edit", sensitive=True,  timeout=60.0,  critical=True),
    ToolSpec("src.servers.filesystem", "multi_edit",    sensitive=True,  timeout=120.0, critical=True),
    ToolSpec("src.servers.run", "run", sensitive=True, timeout=300.0),
    ToolSpec("src.servers.memory", "memory_get",    sensitive=False, timeout=60.0),
    ToolSpec("src.servers.memory", "memory_put",    sensitive=True,  timeout=60.0),
    ToolSpec("src.servers.memory", "memory_search", sensitive=False, timeout=60.0),
    ToolSpec("src.servers.memory", "memory_list",   sensitive=False, timeout=30.0),
    ToolSpec("src.servers.memory", "memory_delete", sensitive=True,  timeout=30.0),
    ToolSpec("src.servers.web", "web_fetch",  sensitive=False, timeout=30.0),
    ToolSpec("src.servers.web", "web_search", sensitive=False, timeout=30.0),
    ToolSpec("src.servers.task", "task", sensitive=False, timeout=60.0),
    ToolSpec("src.core.scheduler_tool", "schedule_task", sensitive=True, timeout=30.0),
    ToolSpec("src.core.scheduler_tool", "list_schedules", sensitive=False, timeout=30.0),
    ToolSpec("src.core.scheduler_tool", "cancel_schedule", sensitive=True, timeout=30.0),
    ToolSpec("src.servers.lsp", "lsp_diagnostics", sensitive=False, timeout=120.0),
    ToolSpec("src.servers.lsp", "lsp_completions", sensitive=False, timeout=30.0),
    ToolSpec("src.servers.lsp", "lsp_hover",       sensitive=False, timeout=30.0),
    ToolSpec("src.servers.lsp", "lsp_references",  sensitive=False, timeout=60.0),
    ToolSpec("src.servers.lsp", "lsp_rename",      sensitive=True,  timeout=60.0),
    ToolSpec("src.servers.lsp", "lsp_definition",  sensitive=False, timeout=30.0),
    ToolSpec("src.servers.ask_user", "ask_user",      sensitive=False, timeout=300.0),
]

EXTENSION_TOOL_SPECS: list[ToolSpec] = [
    ToolSpec("src.servers.browser", "browse_page",        sensitive=False, timeout=60.0),
    ToolSpec("src.servers.browser", "take_screenshot",    sensitive=False, timeout=60.0),
    ToolSpec("src.servers.browser", "browser_click",      sensitive=False, timeout=30.0),
    ToolSpec("src.servers.browser", "browser_fill",       sensitive=False, timeout=30.0),
    ToolSpec("src.servers.browser", "browser_evaluate",   sensitive=True, timeout=30.0),
    ToolSpec("src.servers.browser", "browser_wait",       sensitive=False, timeout=60.0),
    ToolSpec("src.servers.browser", "browser_pdf",        sensitive=False, timeout=30.0),
    ToolSpec("src.servers.browser", "browser_get_html",   sensitive=False, timeout=30.0),
    ToolSpec("src.servers.browser", "browser_close_page", sensitive=False, timeout=10.0),
    ToolSpec("src.servers.browser", "browser_list_pages", sensitive=False, timeout=10.0),
    ToolSpec("src.servers.database", "db_read_query",     sensitive=False, timeout=60.0),
    ToolSpec("src.servers.database", "db_write_query",    sensitive=True,  timeout=60.0),
    ToolSpec("src.servers.database", "db_list_tables",    sensitive=False, timeout=30.0),
    ToolSpec("src.servers.database", "db_describe_table", sensitive=False, timeout=30.0),
]

WRITE_LIKE_TOOLS = {
    "write",
    "multi_edit",
    "notebook_edit",
    "lsp_rename",
    "memory_put",
    "memory_delete",
    "db_write_query",
    "run",
}

INTERACTIVE_TOOLS = {"ask_user"}
