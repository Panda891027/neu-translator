"""
System prompt for memory extraction.
"""


def get_memory_extraction_prompt() -> str:
    """
    Get prompt for extracting learnings from copilot feedback.

    Returns:
        Memory extraction prompt
    """
    return """# Extract Learning from Expense Processing Feedback

You are analyzing feedback from a human reviewer on expense data extraction.

Given:
- Original extracted data from an invoice
- Human reviewer's corrections or rejections
- Reason for the correction

Extract key learnings that can improve future expense processing.

## What to Extract

1. **Vendor Name Corrections**
   - Common OCR errors for specific vendors
   - Correct spelling vs common misreadings
   - Vendor aliases and variations

2. **Category Patterns**
   - Vendor-to-category mappings
   - Keywords that indicate specific categories
   - Ambiguous cases and their resolutions

3. **Amount Extraction Issues**
   - Common mistakes (tip vs total, tax handling)
   - Currency symbol confusions
   - Number format variations

4. **Date Format Patterns**
   - Regional date format preferences
   - Date extraction from different invoice layouts

5. **Policy Clarifications**
   - Edge cases in policy application
   - Exceptions that were approved
   - Common validation issues

## Output Format

Return a JSON object with:
```json
{
  "learning": "Brief description of what was learned",
  "tags": ["tag1", "tag2", "tag3"],
  "category": "vendor|category|amount|date|policy",
  "details": {
    "original": "What the AI extracted",
    "corrected": "What the human corrected to",
    "reason": "Why the correction was made"
  },
  "apply_to": "Description of when to apply this learning"
}
```

## Example

Input:
- Extracted: vendor="Starbuck", amount=45.00
- Corrected: vendor="Starbucks", amount=43.50
- Reason: "Vendor name misspelled, amount included tip which shouldn't be in expense"

Output:
```json
{
  "learning": "Starbucks is often misread as 'Starbuck', and tips should be excluded from meal expenses",
  "tags": ["starbucks", "vendor_spelling", "tip_exclusion", "meals"],
  "category": "vendor",
  "details": {
    "original": "Starbuck, 45.00",
    "corrected": "Starbucks, 43.50",
    "reason": "Vendor spelling and tip exclusion"
  },
  "apply_to": "When processing Starbucks receipts, verify spelling and exclude tip line"
}
```

Focus on actionable learnings that can prevent similar errors in the future.
"""
