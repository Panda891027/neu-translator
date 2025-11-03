"""
Core expense agent package.
Python implementation with Qwen3-VL multimodal capabilities.
"""
from .agent import AgentLoop
from .memory import Memory
from .types import (
    AgentLoopOptions,
    CopilotRequest,
    CopilotResponse,
    CopilotStatus,
    Message,
    MessageRole,
)

__version__ = "0.1.0"

__all__ = [
    "AgentLoop",
    "Memory",
    "AgentLoopOptions",
    "CopilotRequest",
    "CopilotResponse",
    "CopilotStatus",
    "Message",
    "MessageRole",
]
