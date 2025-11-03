"""
Type definitions for the expense agent.
Maintains similar architecture to the TypeScript version.
"""
from typing import Any, Callable, Literal, Optional, TypedDict, Union
from enum import Enum
from dataclasses import dataclass


class MessageRole(str, Enum):
    """Message roles in the conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"


class ContentType(str, Enum):
    """Content types for messages"""
    TEXT = "text"
    IMAGE = "image"
    TOOL_CALL = "tool-call"
    TOOL_RESULT = "tool-result"


@dataclass
class TextContent:
    """Text content in a message"""
    type: Literal["text"] = "text"
    text: str = ""


@dataclass
class ImageContent:
    """Image content in a message (for multimodal)"""
    type: Literal["image"] = "image"
    image_url: str = ""


@dataclass
class ToolCallPart:
    """Tool call part in assistant message"""
    type: Literal["tool-call"] = "tool-call"
    tool_call_id: str = ""
    tool_name: str = ""
    args: dict[str, Any] = None


@dataclass
class ToolResultPart:
    """Tool result part in tool message"""
    type: Literal["tool-result"] = "tool-result"
    tool_call_id: str = ""
    tool_name: str = ""
    output: Any = None


@dataclass
class Message:
    """Base message structure"""
    role: MessageRole
    content: Union[str, list[Union[TextContent, ImageContent, ToolCallPart, ToolResultPart]]]


class CopilotStatus(str, Enum):
    """Status of copilot review"""
    APPROVE = "approve"
    REJECT = "reject"
    REFINED = "refined"


@dataclass
class CopilotRequest:
    """Request for human copilot review"""
    tool: dict[str, str]  # {"name": str, "call_id": str}
    invoice_image: str  # Base64 encoded image or URL
    extracted_data: dict[str, Any]  # Extracted expense data


@dataclass
class CopilotResponse:
    """Response from human copilot"""
    tool: dict[str, str]  # {"name": str, "call_id": str}
    status: CopilotStatus
    approved_data: dict[str, Any]
    reason: str = ""


class ToolResult(TypedDict):
    """Tool execution result"""
    type: Literal["tool-result"]
    payload: Any


class CopilotRequestResult(TypedDict):
    """Copilot request result"""
    type: Literal["copilot-request"]
    payload: CopilotRequest


# Type alias for tool executor
ToolExecutor = Callable[
    [dict[str, Any], dict[str, Any], Optional[CopilotResponse]],
    Union[ToolResult, CopilotRequestResult]
]


@dataclass
class AgentLoopOptions:
    """Options for agent loop"""
    memory: Optional[Any] = None  # Memory instance
    abort_signal: Optional[Any] = None


@dataclass
class ToolCallOptions:
    """Options for tool call"""
    name: str = ""
    call_id: str = ""


NextActor = Literal["user", "agent"]


@dataclass
class AgentIterationResult:
    """Result of one agent iteration"""
    actor: NextActor
    unprocessed_tool_calls: list[ToolCallPart]
    copilot_requests: list[CopilotRequest]
    messages: list[Message]
    finish_reason: Optional[str] = None
