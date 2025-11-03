"""
Tools package for expense agent.
Exports all available tools and their executors.
"""
from .extract_invoice_tool import (
    tool_definition as extract_invoice_tool,
    extract_invoice_executor,
    TOOL_NAME as EXTRACT_INVOICE_NAME,
)
from .validate_expense_tool import (
    tool_definition as validate_expense_tool,
    validate_expense_executor,
    TOOL_NAME as VALIDATE_EXPENSE_NAME,
)
from .read_tool import (
    tool_definition as read_tool,
    read_executor,
    TOOL_NAME as READ_NAME,
)
from .thinking_tool import (
    tool_definition as thinking_tool,
    thinking_executor,
    TOOL_NAME as THINKING_NAME,
)

# Export all tools and executors
__all__ = [
    # Tool definitions
    "extract_invoice_tool",
    "validate_expense_tool",
    "read_tool",
    "thinking_tool",
    # Executors
    "extract_invoice_executor",
    "validate_expense_executor",
    "read_executor",
    "thinking_executor",
    # Tool names
    "EXTRACT_INVOICE_NAME",
    "VALIDATE_EXPENSE_NAME",
    "READ_NAME",
    "THINKING_NAME",
]

# Tool registry for easy access
TOOLS = {
    EXTRACT_INVOICE_NAME: {
        "definition": extract_invoice_tool,
        "executor": extract_invoice_executor,
    },
    VALIDATE_EXPENSE_NAME: {
        "definition": validate_expense_tool,
        "executor": validate_expense_executor,
    },
    READ_NAME: {
        "definition": read_tool,
        "executor": read_executor,
    },
    THINKING_NAME: {
        "definition": thinking_tool,
        "executor": thinking_executor,
    },
}


def get_tool_definitions():
    """Get all tool definitions for LLM"""
    return {name: tool["definition"] for name, tool in TOOLS.items()}


def get_tool_executor(tool_name: str):
    """Get executor for a specific tool"""
    if tool_name in TOOLS:
        return TOOLS[tool_name]["executor"]
    raise ValueError(f"Unknown tool: {tool_name}")
