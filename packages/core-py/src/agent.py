"""
Main AgentLoop class for expense processing.
Mirrors the TypeScript AgentLoop architecture.
"""
from typing import Dict, List, Optional, Any
import time
import random
from .types import (
    AgentLoopOptions,
    AgentIterationResult,
    Message,
    MessageRole,
    ToolCallPart,
    ToolResultPart,
    CopilotRequest,
    CopilotResponse,
    NextActor,
)
from .context import Context
from .tools import TOOLS, get_tool_definitions, get_tool_executor
from .prompts.system_workflow import get_system_workflow
from .llm import get_qwen_client
from .memory import Memory


class AgentLoop:
    """
    Main agent loop for expense processing.
    Manages conversation flow, tool execution, and copilot interactions.
    """

    def __init__(
        self,
        options: Optional[AgentLoopOptions] = None,
        messages: Optional[List[Message]] = None
    ):
        """
        Initialize agent loop.

        Args:
            options: Agent configuration options
            messages: Initial message history
        """
        self.options = options or AgentLoopOptions()
        self.context = Context(messages or [])
        self.tool_definitions = get_tool_definitions()

    async def next(self) -> AgentIterationResult:
        """
        Execute one iteration of the agent loop.

        Returns:
            Result containing actor, messages, tool calls, and copilot requests
        """
        result = await self._next()

        # Add messages to context
        self.context.add_messages(result["messages"])

        # Get unprocessed tool calls
        unprocessed_tool_calls = await self.get_unprocessed_tool_calls()

        return AgentIterationResult(
            actor=result["actor"],
            unprocessed_tool_calls=unprocessed_tool_calls,
            copilot_requests=result["copilot_requests"],
            messages=result["messages"],
            finish_reason=result.get("finish_reason"),
        )

    async def user_input(self, messages: List[Message]) -> None:
        """
        Add user input to the context.

        Args:
            messages: User messages to add
        """
        self.context.add_messages(messages)

    async def add_copilot_responses(self, responses: List[CopilotResponse]) -> None:
        """
        Add copilot responses to the context.

        Args:
            responses: Copilot responses
        """
        self.context.add_copilot_responses(responses)

    async def get_messages(self) -> List[Message]:
        """
        Get all messages in the conversation.

        Returns:
            List of messages
        """
        return self.context.get_messages()

    async def compact(self) -> None:
        """Compact the message history to save tokens"""
        await self.context.compact()

    async def _next(self) -> Dict[str, Any]:
        """
        Internal implementation of agent iteration.

        Returns:
            Dictionary with messages, copilot_requests, actor, finish_reason
        """
        actor: NextActor = "agent"

        # Get model messages
        model_messages = self.context.to_model_messages()

        if not model_messages:
            return {
                "messages": [],
                "copilot_requests": [],
                "actor": "user",
            }

        # Check for unprocessed tool calls
        unprocessed_tool_calls = await self.get_unprocessed_tool_calls()

        if unprocessed_tool_calls:
            # Execute tools
            copilot_response_map = self._build_copilot_response_map(unprocessed_tool_calls)

            tool_results = []
            for call in unprocessed_tool_calls:
                result = await self.execute_tool(
                    call,
                    copilot_response_map.get(call.tool_call_id)
                )
                tool_results.append(result)

            # Separate tool results from copilot requests
            tool_result_parts: List[ToolResultPart] = []
            copilot_requests: List[CopilotRequest] = []

            for result in tool_results:
                if result["type"] == "tool-result":
                    tool_result_parts.append(
                        ToolResultPart(
                            type="tool-result",
                            tool_call_id=result.get("tool_call_id", ""),
                            tool_name=result.get("tool_name", ""),
                            output=result["payload"]
                        )
                    )
                else:  # copilot-request
                    copilot_requests.append(result["payload"])

            # If there are copilot requests, return them
            if copilot_requests:
                return {
                    "messages": [],
                    "copilot_requests": copilot_requests,
                    "actor": "agent",
                }

            # Return tool results
            return {
                "messages": [
                    Message(
                        role=MessageRole.TOOL,
                        content=tool_result_parts
                    )
                ],
                "copilot_requests": [],
                "actor": "agent",
            }

        # Call LLM
        try:
            llm_result = await self._call_llm(model_messages)

            messages = llm_result["messages"]
            tool_calls = llm_result["tool_calls"]
            finish_reason = llm_result["finish_reason"]

            if not messages:
                return {
                    "messages": [],
                    "copilot_requests": [],
                    "actor": "user",
                    "finish_reason": finish_reason,
                }

            # Determine next actor
            last_message = messages[-1]
            if last_message.role == MessageRole.ASSISTANT:
                actor = "user"

            if tool_calls:
                actor = "agent"

            return {
                "messages": messages,
                "copilot_requests": [],
                "actor": actor,
                "finish_reason": finish_reason,
            }

        except Exception as e:
            print(f"Error calling LLM: {e}")
            return {
                "messages": [],
                "copilot_requests": [],
                "actor": "user",
                "finish_reason": "error",
            }

    async def _call_llm(self, model_messages: List[Dict]) -> Dict[str, Any]:
        """
        Call the LLM with current messages.

        Args:
            model_messages: Messages in LLM format

        Returns:
            Dictionary with messages, tool_calls, finish_reason
        """
        client = get_qwen_client()

        # Get system prompt with memory
        memory_context = ""
        if self.options.memory:
            memory_context = self.options.memory.provide_memory()

        system_prompt = get_system_workflow(memory_context)

        # Convert tool definitions to LLM format
        tools = [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool_def["description"],
                    "parameters": tool_def["input_schema"],
                }
            }
            for name, tool_def in self.tool_definitions.items()
        ]

        # Call LLM
        result = await client.generate(
            messages=model_messages,
            system=system_prompt,
            tools=tools,
            temperature=0.7,
            max_tokens=2000,
        )

        # Parse response
        messages = []
        tool_calls = []

        content = result.get("content", "")
        llm_tool_calls = result.get("tool_calls", [])

        # Build assistant message
        if content or llm_tool_calls:
            assistant_content = []

            if content:
                from .types import TextContent
                assistant_content.append(TextContent(type="text", text=content))

            # Add tool calls
            for tc in llm_tool_calls:
                tool_call_id = self._generate_tool_call_id()
                tool_call = ToolCallPart(
                    type="tool-call",
                    tool_call_id=tool_call_id,
                    tool_name=tc.get("function", {}).get("name", ""),
                    args=tc.get("function", {}).get("arguments", {}),
                )
                assistant_content.append(tool_call)
                tool_calls.append(tool_call)

            messages.append(
                Message(
                    role=MessageRole.ASSISTANT,
                    content=assistant_content if len(assistant_content) > 1 else content
                )
            )

        return {
            "messages": messages,
            "tool_calls": tool_calls,
            "finish_reason": result.get("finish_reason", "stop"),
        }

    def _build_copilot_response_map(
        self, unprocessed_tool_calls: List[ToolCallPart]
    ) -> Dict[str, CopilotResponse]:
        """
        Build a map of tool call IDs to copilot responses.

        Args:
            unprocessed_tool_calls: List of unprocessed tool calls

        Returns:
            Dictionary mapping tool call IDs to copilot responses
        """
        tool_call_ids = [tc.tool_call_id for tc in unprocessed_tool_calls]
        copilot_responses = self.context.get_copilot_responses(tool_call_ids)

        return {
            resp.tool["call_id"]: resp
            for resp in copilot_responses
        }

    async def get_unprocessed_tool_calls(self) -> List[ToolCallPart]:
        """
        Get tool calls that haven't been executed yet.

        Returns:
            List of unprocessed tool calls
        """
        messages = self.context.get_messages()
        tool_call_parts: Dict[str, ToolCallPart] = {}

        for msg in messages:
            if msg.role == MessageRole.ASSISTANT and isinstance(msg.content, list):
                for part in msg.content:
                    if isinstance(part, ToolCallPart) or (hasattr(part, 'type') and part.type == "tool-call"):
                        tool_call_parts[part.tool_call_id] = part

            if msg.role == MessageRole.TOOL and isinstance(msg.content, list):
                for part in msg.content:
                    if isinstance(part, ToolResultPart) or (hasattr(part, 'type') and part.type == "tool-result"):
                        tool_call_parts.pop(part.tool_call_id, None)

        return list(tool_call_parts.values())

    async def execute_tool(
        self,
        tool_call: ToolCallPart,
        copilot_response: Optional[CopilotResponse] = None,
    ) -> Dict[str, Any]:
        """
        Execute a tool call.

        Args:
            tool_call: Tool call to execute
            copilot_response: Optional copilot response

        Returns:
            Tool result or copilot request
        """
        try:
            executor = get_tool_executor(tool_call.tool_name)

            options = {
                "name": tool_call.tool_name,
                "call_id": tool_call.tool_call_id,
                "memory": self.options.memory,
                "abort_signal": self.options.abort_signal,
            }

            result = await executor(tool_call.args, options, copilot_response)

            # Add tool call ID and name to result
            if result["type"] == "tool-result":
                return {
                    **result,
                    "tool_call_id": tool_call.tool_call_id,
                    "tool_name": tool_call.tool_name,
                }

            return result

        except Exception as e:
            print(f"Error executing tool {tool_call.tool_name}: {e}")
            return {
                "type": "tool-result",
                "tool_call_id": tool_call.tool_call_id,
                "tool_name": tool_call.tool_name,
                "payload": {
                    "error": str(e)
                }
            }

    @staticmethod
    def _generate_tool_call_id() -> str:
        """
        Generate a unique tool call ID.

        Returns:
            Unique ID string
        """
        timestamp = int(time.time() * 1000)
        random_part = ''.join(
            random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8)
        )
        return f"{timestamp}-{random_part}"
