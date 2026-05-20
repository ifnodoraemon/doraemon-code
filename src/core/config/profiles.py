"""
Worker Profile Definitions
"""

WORKER_PROFILES = {
    "inspect": {
        "tools": ["read", "search", "web_search", "web_fetch", "lsp_hover", "lsp_definition", "lsp_references", "memory_get", "memory_search", "memory_list", "task"],
        "groups": ["read", "memory", "research", "task"],
        "instruction": "Inspect the codebase, gather concrete facts, and avoid speculative edits.",
        "keywords": ("analyze", "inspect", "research", "explore", "read", "investigate", "design")
    },
    "validate": {
        "tools": ["read", "search", "run", "lsp_diagnostics", "lsp_hover", "lsp_definition", "memory_get", "memory_search", "memory_list", "task"],
        "groups": ["read", "edit", "memory", "task"],
        "instruction": "Validate behavior, run checks when useful, and return concrete evidence.",
        "keywords": ("verify", "validation", "test", "check", "diagnostic", "integration")
    },
    "change": {
        "tools": ["read", "search", "write", "multi_edit", "notebook_edit", "run", "lsp_diagnostics", "lsp_completions", "lsp_hover", "lsp_definition", "lsp_references", "lsp_rename", "memory_get", "memory_put", "memory_search", "memory_list", "task"],
        "groups": ["read", "edit", "memory", "research", "task"],
        "instruction": "Make the necessary code changes, then verify the subtask before returning.",
        "keywords": () # Default fallback
    }
}
