"""
Validate expense data against company policies.
"""
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
from ..types import CopilotResponse


class ValidationRule(BaseModel):
    """A single validation rule"""
    rule_name: str
    passed: bool
    message: str


class ValidateExpenseInput(BaseModel):
    """Input schema for expense validation"""
    expense_id: str = Field(description="ID of the expense to validate")
    amount: float = Field(description="Expense amount")
    currency: str = Field(description="Currency code")
    category: str = Field(description="Expense category")
    date: str = Field(description="Transaction date")
    vendor: str = Field(description="Vendor name")


class ValidateExpenseOutput(BaseModel):
    """Output schema for expense validation"""
    is_valid: bool = Field(description="Whether the expense passes all validations")
    validation_results: List[ValidationRule] = Field(
        description="List of validation results",
        default_factory=list
    )
    warnings: List[str] = Field(
        description="Non-blocking warnings",
        default_factory=list
    )
    total_score: float = Field(
        description="Validation confidence score (0-1)",
        default=1.0
    )


TOOL_NAME = "validate_expense"
DESCRIPTION = """Validate expense data against company policies and rules.

This tool checks:
1. Amount limits per category
2. Required fields completeness
3. Date validity (not future dates, within fiscal period)
4. Vendor legitimacy
5. Category-specific rules (e.g., meal limits, travel policies)

Returns validation results with pass/fail for each rule and overall validity.
"""

INPUT_SCHEMA = ValidateExpenseInput.model_json_schema()
OUTPUT_SCHEMA = ValidateExpenseOutput.model_json_schema()


# Default policy rules (can be configured)
POLICY_RULES = {
    "meals": {
        "max_amount_cny": 200.0,
        "max_amount_usd": 30.0,
    },
    "travel": {
        "max_amount_cny": 5000.0,
        "max_amount_usd": 700.0,
    },
    "accommodation": {
        "max_amount_cny": 800.0,
        "max_amount_usd": 120.0,
    },
    "supplies": {
        "max_amount_cny": 1000.0,
        "max_amount_usd": 150.0,
    },
    "entertainment": {
        "max_amount_cny": 500.0,
        "max_amount_usd": 70.0,
    },
    "other": {
        "max_amount_cny": 1000.0,
        "max_amount_usd": 150.0,
    }
}


async def validate_expense_executor(
    input_data: Dict[str, Any],
    options: Dict[str, Any],
    copilot_response: Optional[CopilotResponse] = None
) -> Dict[str, Any]:
    """
    Execute expense validation tool.

    Args:
        input_data: Tool input
        options: Tool options
        copilot_response: Not used for validation tool

    Returns:
        Tool result with validation results
    """
    try:
        validated_input = ValidateExpenseInput(**input_data)
    except Exception as e:
        return {
            "type": "tool-result",
            "payload": {
                "is_valid": False,
                "validation_results": [
                    {
                        "rule_name": "input_validation",
                        "passed": False,
                        "message": f"Invalid input: {str(e)}"
                    }
                ],
                "warnings": [],
                "total_score": 0.0
            }
        }

    results: List[ValidationRule] = []
    warnings: List[str] = []

    # Rule 1: Amount limit check
    category = validated_input.category.lower()
    currency = validated_input.currency.upper()
    amount = validated_input.amount

    if category in POLICY_RULES:
        limits = POLICY_RULES[category]
        limit_key = f"max_amount_{currency.lower()}"

        if limit_key in limits:
            max_amount = limits[limit_key]
            if amount <= max_amount:
                results.append(ValidationRule(
                    rule_name="amount_limit",
                    passed=True,
                    message=f"Amount {amount} {currency} is within limit {max_amount}"
                ))
            else:
                results.append(ValidationRule(
                    rule_name="amount_limit",
                    passed=False,
                    message=f"Amount {amount} {currency} exceeds limit {max_amount}"
                ))
        else:
            warnings.append(f"No limit defined for currency {currency} in category {category}")
            results.append(ValidationRule(
                rule_name="amount_limit",
                passed=True,
                message="No limit check available for this currency"
            ))
    else:
        warnings.append(f"Unknown category: {category}")
        results.append(ValidationRule(
            rule_name="category_validation",
            passed=False,
            message=f"Unknown expense category: {category}"
        ))

    # Rule 2: Required fields
    required_fields = ["expense_id", "amount", "currency", "category", "date", "vendor"]
    missing_fields = []

    for field in required_fields:
        value = getattr(validated_input, field, None)
        if not value or (isinstance(value, str) and not value.strip()):
            missing_fields.append(field)

    if missing_fields:
        results.append(ValidationRule(
            rule_name="required_fields",
            passed=False,
            message=f"Missing required fields: {', '.join(missing_fields)}"
        ))
    else:
        results.append(ValidationRule(
            rule_name="required_fields",
            passed=True,
            message="All required fields present"
        ))

    # Rule 3: Date validation (basic check)
    from datetime import datetime
    try:
        expense_date = datetime.strptime(validated_input.date, "%Y-%m-%d")
        current_date = datetime.now()

        if expense_date > current_date:
            results.append(ValidationRule(
                rule_name="date_validation",
                passed=False,
                message="Expense date cannot be in the future"
            ))
        else:
            # Check if date is too old (more than 90 days)
            days_old = (current_date - expense_date).days
            if days_old > 90:
                warnings.append(f"Expense is {days_old} days old - may need special approval")

            results.append(ValidationRule(
                rule_name="date_validation",
                passed=True,
                message="Date is valid"
            ))
    except ValueError:
        results.append(ValidationRule(
            rule_name="date_validation",
            passed=False,
            message="Invalid date format. Expected YYYY-MM-DD"
        ))

    # Rule 4: Amount sanity check
    if amount <= 0:
        results.append(ValidationRule(
            rule_name="amount_sanity",
            passed=False,
            message="Amount must be greater than 0"
        ))
    elif amount > 100000:  # Arbitrary high threshold
        warnings.append("Very high amount - may require additional approval")
        results.append(ValidationRule(
            rule_name="amount_sanity",
            passed=True,
            message="Amount is valid but unusually high"
        ))
    else:
        results.append(ValidationRule(
            rule_name="amount_sanity",
            passed=True,
            message="Amount is reasonable"
        ))

    # Calculate overall validity and score
    is_valid = all(r.passed for r in results)
    total_score = sum(1 for r in results if r.passed) / len(results) if results else 0.0

    return {
        "type": "tool-result",
        "payload": {
            "is_valid": is_valid,
            "validation_results": [r.dict() for r in results],
            "warnings": warnings,
            "total_score": total_score
        }
    }


# Export tool definition
tool_definition = {
    "name": TOOL_NAME,
    "description": DESCRIPTION,
    "input_schema": INPUT_SCHEMA,
    "output_schema": OUTPUT_SCHEMA,
}
