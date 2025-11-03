"""
Thinking tool for step-by-step reasoning.
Helps the agent plan and reason about complex tasks.
"""
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from ..types import CopilotResponse


class ThinkingInput(BaseModel):
    """Input schema for thinking tool"""
    thought: str = Field(description="The agent's current thought or reasoning step")


class ThinkingOutput(BaseModel):
    """Output schema for thinking tool"""
    acknowledged: bool = Field(description="Whether the thought was acknowledged", default=True)


TOOL_NAME = "thinking"
DESCRIPTION = """Express step-by-step reasoning and planning.

Use this tool to:
- Break down complex expense processing tasks
- Plan which invoices to process and in what order
- Reason about edge cases or ambiguous information
- Explain your decision-making process

This helps provide transparency and allows for better debugging.
The thinking process is logged but doesn't require human approval.
"""

INPUT_SCHEMA = ThinkingInput.model_json_schema()
OUTPUT_SCHEMA = ThinkingOutput.model_json_schema()


async def thinking_executor(
    input_data: Dict[str, Any],
    options: Dict[str, Any],
    copilot_response: Optional[CopilotResponse] = None
) -> Dict[str, Any]:
    """
    Execute thinking tool.

    Args:
        input_data: Tool input
        options: Tool options
        copilot_response: Not used for thinking tool

    Returns:
        Tool result
    """
    try:
        validated_input = ThinkingInput(**input_data)
    except Exception as e:
        return {
            "type": "tool-result",
            "payload": {
                "acknowledged": False
            }
        }

    # Simply acknowledge the thought
    # In a production system, this could log to a structured format
    return {
        "type": "tool-result",
        "payload": {
            "acknowledged": True
        }
    }


# Export tool definition
tool_definition = {
    "name": TOOL_NAME,
    "description": DESCRIPTION,
    "input_schema": INPUT_SCHEMA,
    "output_schema": OUTPUT_SCHEMA,
}
