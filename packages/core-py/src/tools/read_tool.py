"""
Read file contents tool.
Similar to the TypeScript read-tool.
"""
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from ..types import CopilotResponse
import os


class ReadInput(BaseModel):
    """Input schema for read tool"""
    file_path: str = Field(description="Path to the file to read")
    file_id: str = Field(description="Unique ID for this file")


class ReadOutput(BaseModel):
    """Output schema for read tool"""
    content: str = Field(description="File contents")
    file_path: str = Field(description="Path to the file")
    file_id: str = Field(description="File ID")
    error: Optional[str] = Field(description="Error message if read failed", default=None)


TOOL_NAME = "read"
DESCRIPTION = """Read contents of a file from the filesystem.

This tool reads text files and returns their contents.
Useful for:
- Reading previous expense reports
- Loading configuration files
- Accessing stored data

The file_id helps track which file was read in the conversation context.
"""

INPUT_SCHEMA = ReadInput.model_json_schema()
OUTPUT_SCHEMA = ReadOutput.model_json_schema()


async def read_executor(
    input_data: Dict[str, Any],
    options: Dict[str, Any],
    copilot_response: Optional[CopilotResponse] = None
) -> Dict[str, Any]:
    """
    Execute read tool.

    Args:
        input_data: Tool input
        options: Tool options
        copilot_response: Not used for read tool

    Returns:
        Tool result
    """
    try:
        validated_input = ReadInput(**input_data)
    except Exception as e:
        return {
            "type": "tool-result",
            "payload": {
                "content": "",
                "file_path": input_data.get("file_path", ""),
                "file_id": input_data.get("file_id", ""),
                "error": f"Invalid input: {str(e)}"
            }
        }

    try:
        # Check if file exists
        if not os.path.exists(validated_input.file_path):
            return {
                "type": "tool-result",
                "payload": {
                    "content": "",
                    "file_path": validated_input.file_path,
                    "file_id": validated_input.file_id,
                    "error": f"File not found: {validated_input.file_path}"
                }
            }

        # Read file contents
        with open(validated_input.file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return {
            "type": "tool-result",
            "payload": {
                "content": content,
                "file_path": validated_input.file_path,
                "file_id": validated_input.file_id,
                "error": None
            }
        }

    except Exception as e:
        return {
            "type": "tool-result",
            "payload": {
                "content": "",
                "file_path": validated_input.file_path,
                "file_id": validated_input.file_id,
                "error": f"Failed to read file: {str(e)}"
            }
        }


# Export tool definition
tool_definition = {
    "name": TOOL_NAME,
    "description": DESCRIPTION,
    "input_schema": INPUT_SCHEMA,
    "output_schema": OUTPUT_SCHEMA,
}
