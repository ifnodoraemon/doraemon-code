"""
Bridge between the Commands system and the Tool registry.

Enables custom commands defined in .agent/commands/*.md to be used
as first-class tools by the agent.
"""

import logging
from typing import Any
from pathlib import Path

from src.core.commands import CommandManager, CommandDefinition
from src.host.tools import ToolRegistry

logger = logging.getLogger(__name__)

class CommandToolRegistry:
    """Registry that converts custom commands into agent tools."""

    def __init__(self, project_dir: Path | None = None):
        self.manager = CommandManager(project_dir)
        self.project_dir = project_dir or Path.cwd()

    def attach_to_registry(self, registry: ToolRegistry) -> None:
        """Load all custom commands and register them as tools."""
        commands = self.manager.loader.load_all_commands()
        for name, cmd in commands.items():
            self._register_command_as_tool(registry, name, cmd)

    def _register_command_as_tool(self, registry: ToolRegistry, name: str, cmd: CommandDefinition) -> None:
        """Register a single command as a tool."""
        
        # Create a wrapper function for the command
        async def command_wrapper(**kwargs) -> str:
            result = await self.manager.run_command(name, kwargs)
            if result.success:
                return "\n".join(result.outputs)
            else:
                return f"Command failed: {'; '.join(result.errors)}"

        # Set docstring from command description
        command_wrapper.__doc__ = cmd.description
        command_wrapper.__name__ = name

        # Define parameters based on command arguments
        properties = {}
        required = []
        for arg in cmd.arguments:
            arg_schema = {"type": "string", "description": arg.description or f"Argument: {arg.name}"}
            if arg.default is not None:
                arg_schema["default"] = arg.default
            
            properties[arg.name] = arg_schema
            if arg.required:
                required.append(arg.name)

        parameters = {
            "type": "object",
            "properties": properties,
            "required": required,
        }

        registry.register(
            command_wrapper,
            name=name,
            description=cmd.description,
            sensitive=True,  # Custom commands are sensitive by default as they run scripts
            source="custom_command",
            metadata={
                "command_path": str(cmd.path) if cmd.path else None,
                "capability_group": "custom",
            }
        )
        
        # Manually override the parameters since registry.register usually extracts them from signature
        registry._tools[name].parameters = parameters

        logger.info("Registered custom command as tool: %s", name)

def get_command_tool_registry(project_dir: Path | None = None) -> CommandToolRegistry:
    """Get a CommandToolRegistry instance."""
    return CommandToolRegistry(project_dir)
