"""
Merge Engine for Multi-Agent Results

Handles the merging of results from multiple workers, detecting conflicts
and producing a unified summary.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

@dataclass
class MergeResult:
    """Unified result after merging worker outputs."""
    summary: str
    outputs: dict[str, str] = field(default_factory=dict)
    conflicts: list[str] = field(default_factory=list)
    success: bool = True

class OrchestrationMergeEngine:
    """Merges outputs and files from multiple worker sessions."""

    def __init__(self):
        self._outputs = {}

    def add_worker_output(self, task_id: str, output: str, files_modified: list[str] | None = None):
        """Add output from a single worker task."""
        self._outputs[task_id] = {
            "content": output,
            "files": files_modified or []
        }

    def merge_results(self) -> MergeResult:
        """Merge all collected worker results."""
        if not self._outputs:
            return MergeResult(summary="No results to merge", success=True)

        unified_summary_parts = []
        all_modified_files = {} # file -> list of task_ids

        for tid, data in self._outputs.items():
            unified_summary_parts.append(f"### Task {tid}\n{data['content']}")
            for f in data["files"]:
                if f not in all_modified_files:
                    all_modified_files[f] = []
                all_modified_files[f].append(tid)

        # Detect conflicts
        conflicts = [f for f, tids in all_modified_files.items() if len(tids) > 1]
        
        summary = "## Merged Execution Summary\n\n" + "\n\n".join(unified_summary_parts)
        if conflicts:
            summary += f"\n\nWARNING: Potential conflicts detected in files: {', '.join(conflicts)}"

        return MergeResult(
            summary=summary,
            outputs={tid: d["content"] for tid, d in self._outputs.items()},
            conflicts=conflicts,
            success=True
        )
