"""
Context class for managing conversation history.
Similar to the TypeScript Context class.
"""
from typing import List, Optional
from .types import Message, CopilotResponse, ToolCallPart


class Context:
    """Manages conversation context and message history"""

    def __init__(self, messages: Optional[List[Message]] = None):
        """
        Initialize context with optional initial messages.

        Args:
            messages: Initial message history
        """
        self._messages: List[Message] = messages or []
        self._copilot_responses: List[CopilotResponse] = []

    def add_messages(self, messages: List[Message]) -> None:
        """
        Add new messages to the context.

        Args:
            messages: Messages to add
        """
        self._messages.extend(messages)

    def add_copilot_responses(self, responses: List[CopilotResponse]) -> None:
        """
        Add copilot responses to the context.

        Args:
            responses: Copilot responses to add
        """
        self._copilot_responses.extend(responses)

    def get_messages(self) -> List[Message]:
        """
        Get all messages in the context.

        Returns:
            List of all messages
        """
        return self._messages.copy()

    def get_copilot_responses(self, tool_call_ids: List[str]) -> List[CopilotResponse]:
        """
        Get copilot responses for specific tool call IDs.

        Args:
            tool_call_ids: List of tool call IDs to filter by

        Returns:
            Filtered copilot responses
        """
        return [
            resp for resp in self._copilot_responses
            if resp.tool["call_id"] in tool_call_ids
        ]

    def to_model_messages(self) -> List[dict]:
        """
        Convert messages to format expected by LLM.

        Returns:
            List of messages in LLM format
        """
        model_messages = []

        for msg in self._messages:
            if isinstance(msg.content, str):
                model_messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
            else:
                # Handle multipart content
                content_parts = []
                for part in msg.content:
                    if hasattr(part, 'type'):
                        if part.type == "text":
                            content_parts.append({"type": "text", "text": part.text})
                        elif part.type == "image":
                            content_parts.append({"type": "image_url", "image_url": {"url": part.image_url}})
                        elif part.type == "tool-call":
                            content_parts.append({
                                "type": "tool-call",
                                "id": part.tool_call_id,
                                "name": part.tool_name,
                                "args": part.args
                            })
                        elif part.type == "tool-result":
                            content_parts.append({
                                "type": "tool-result",
                                "tool_call_id": part.tool_call_id,
                                "tool_name": part.tool_name,
                                "output": part.output
                            })

                model_messages.append({
                    "role": msg.role.value,
                    "content": content_parts
                })

        return model_messages

    async def compact(self) -> None:
        """
        Compact the message history to save tokens.
        This can be implemented to summarize old messages.
        """
        # TODO: Implement message compaction/summarization
        # For now, keep recent messages and summarize older ones
        if len(self._messages) > 20:
            # Keep system messages and recent messages
            recent_messages = self._messages[-10:]
            # In a real implementation, we would summarize the older messages
            self._messages = recent_messages
