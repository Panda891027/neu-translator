"""
Extract invoice information from images using multimodal LLM.
This is the core tool for the expense agent.
"""
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from ..types import ToolExecutor, CopilotResponse
import base64


class ExtractInvoiceInput(BaseModel):
    """Input schema for invoice extraction"""
    image_path: str = Field(description="Path to the invoice/receipt image file")
    expense_id: str = Field(description="Unique ID for this expense item")


class ExtractInvoiceOutput(BaseModel):
    """Output schema for invoice extraction"""
    vendor: str = Field(description="Vendor/merchant name")
    date: str = Field(description="Transaction date (YYYY-MM-DD)")
    amount: float = Field(description="Total amount")
    currency: str = Field(description="Currency code (e.g., CNY, USD)")
    category: str = Field(description="Expense category (e.g., meals, travel, supplies)")
    items: list[Dict[str, Any]] = Field(
        description="List of line items with name, quantity, price",
        default_factory=list
    )
    tax_amount: Optional[float] = Field(description="Tax amount if available", default=None)
    status: str = Field(description="Extraction status: 'approve', 'reject', or 'refined'")
    confidence: float = Field(description="Confidence score (0-1)", default=0.0)
    reason: str = Field(description="Reason for status or any issues", default="")


# Tool definition
TOOL_NAME = "extract_invoice"
DESCRIPTION = """Extract expense information from invoice or receipt images.

This tool uses multimodal vision capabilities to:
1. Read invoice/receipt images (supports JPG, PNG, PDF)
2. Extract key information: vendor, date, amount, currency, items
3. Categorize the expense automatically
4. Return structured data for human review

The extracted data will be sent to a human copilot for approval before being finalized.
If the image quality is poor or information is unclear, the tool will indicate low confidence.

Usage:
- Provide the path to the invoice image file
- Assign a unique expense_id for tracking
- The tool returns structured expense data
- Human copilot can approve, reject, or refine the data
"""

INPUT_SCHEMA = ExtractInvoiceInput.model_json_schema()
OUTPUT_SCHEMA = ExtractInvoiceOutput.model_json_schema()


def read_image_as_base64(image_path: str) -> str:
    """
    Read image file and encode as base64.

    Args:
        image_path: Path to image file

    Returns:
        Base64 encoded image string
    """
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
            return base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        raise ValueError(f"Failed to read image: {str(e)}")


async def extract_invoice_executor(
    input_data: Dict[str, Any],
    options: Dict[str, Any],
    copilot_response: Optional[CopilotResponse] = None
) -> Dict[str, Any]:
    """
    Execute invoice extraction tool.

    Args:
        input_data: Tool input containing image_path and expense_id
        options: Tool execution options (name, call_id, memory, etc.)
        copilot_response: Optional human copilot response

    Returns:
        Tool result or copilot request
    """
    # Validate input
    try:
        validated_input = ExtractInvoiceInput(**input_data)
    except Exception as e:
        return {
            "type": "tool-result",
            "payload": {
                "vendor": "",
                "date": "",
                "amount": 0.0,
                "currency": "",
                "category": "",
                "items": [],
                "status": "reject",
                "confidence": 0.0,
                "reason": f"Invalid input: {str(e)}"
            }
        }

    # Read image
    try:
        image_base64 = read_image_as_base64(validated_input.image_path)
    except Exception as e:
        return {
            "type": "tool-result",
            "payload": {
                "vendor": "",
                "date": "",
                "amount": 0.0,
                "currency": "",
                "category": "",
                "items": [],
                "status": "reject",
                "confidence": 0.0,
                "reason": str(e)
            }
        }

    # If no copilot response yet, extract data and request human review
    if not copilot_response:
        # Use LLM to extract invoice data
        from ..llm import get_qwen_client

        client = get_qwen_client()

        # Prepare prompt for invoice extraction
        extraction_prompt = """Please extract the following information from this invoice/receipt image:

1. Vendor/Merchant name
2. Transaction date (format: YYYY-MM-DD)
3. Total amount
4. Currency
5. Expense category (meals, travel, accommodation, supplies, entertainment, other)
6. Line items (if visible): name, quantity, unit price
7. Tax amount (if shown)

Return the data in JSON format. Also provide a confidence score (0-1) indicating how confident you are in the extraction."""

        try:
            # Call Qwen VL model with image
            result = await client.generate(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": extraction_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                        ]
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )

            # Parse LLM response
            import json
            extracted_data = json.loads(result["content"])

            # Prepare copilot request
            copilot_request = {
                "tool": {
                    "name": options.get("name", TOOL_NAME),
                    "call_id": options.get("call_id", "")
                },
                "invoice_image": image_base64,
                "extracted_data": extracted_data
            }

            return {
                "type": "copilot-request",
                "payload": copilot_request
            }

        except Exception as e:
            return {
                "type": "tool-result",
                "payload": {
                    "vendor": "",
                    "date": "",
                    "amount": 0.0,
                    "currency": "",
                    "category": "",
                    "items": [],
                    "status": "reject",
                    "confidence": 0.0,
                    "reason": f"Extraction failed: {str(e)}"
                }
            }

    # Process copilot response
    approved_data = copilot_response.approved_data
    status = copilot_response.status.value

    # Store in memory if rejected or refined
    if status != "approve" and options.get("memory"):
        memory = options["memory"]
        await memory.extract_memory({
            "req": {
                "tool": copilot_response.tool,
                "invoice_image": image_base64,
                "extracted_data": approved_data
            },
            "res": copilot_response
        })

    # Return final result
    return {
        "type": "tool-result",
        "payload": {
            **approved_data,
            "status": status,
            "reason": copilot_response.reason
        }
    }


# Export tool definition
tool_definition = {
    "name": TOOL_NAME,
    "description": DESCRIPTION,
    "input_schema": INPUT_SCHEMA,
    "output_schema": OUTPUT_SCHEMA,
}
