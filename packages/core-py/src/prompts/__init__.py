"""
Prompts package.
Exports system prompts for the agent.
"""
from .system_workflow import get_system_workflow
from .system_memory import get_memory_extraction_prompt

__all__ = [
    "get_system_workflow",
    "get_memory_extraction_prompt",
]
