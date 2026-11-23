import json
from datetime import datetime
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool
from mcp.types import ToolAnnotations
from pydantic import ValidationError

from scenarios.structured_data_json.schemas import Invoice

TOLERANCE = 0.01


def check_invoice(raw: str) -> list[str]:
    """Schema + business-rule checks. Returns a list of problems (empty = valid)."""
    try:
        invoice = Invoice.model_validate_json(raw)
    except ValidationError as e:
        return [f"schema: {'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors()]

    errors: list[str] = []
    if invoice.invoice_date:
        try:
            datetime.strptime(invoice.invoice_date, "%Y-%m-%d")
        except ValueError:
            errors.append(f"invoice_date '{invoice.invoice_date}' is not YYYY-MM-DD")
    if invoice.currency and not (len(invoice.currency) == 3 and invoice.currency.isupper()):
        errors.append(f"currency '{invoice.currency}' is not a 3-letter ISO code")

    for i, item in enumerate(invoice.line_items, 1):
        if abs(item.quantity * item.unit_price - item.amount) > TOLERANCE:
            errors.append(f"line {i}: quantity x unit_price != amount")
    if invoice.line_items and invoice.subtotal is not None:
        items_sum = sum(i.amount for i in invoice.line_items)
        if abs(items_sum - invoice.subtotal) > TOLERANCE:
            errors.append(f"line items sum {items_sum:.2f} != subtotal {invoice.subtotal:.2f}")
    if invoice.subtotal is not None and invoice.total is not None:
        expected = invoice.subtotal + (invoice.tax or 0)
        if abs(expected - invoice.total) > TOLERANCE:
            errors.append(f"subtotal + tax {expected:.2f} != total {invoice.total:.2f}")
    return errors


@tool(
    name="validate_extraction",
    description=(
        "Validate an extracted invoice JSON against the schema and arithmetic rules "
        "(line items, subtotal, tax, total, date and currency formats). "
        "Call this before giving the final answer."
    ),
    input_schema={"invoice_json": str},
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    ),
)
async def validate_extraction(args: dict[str, Any]) -> dict[str, Any]:
    errors = check_invoice(args["invoice_json"])
    result = {"valid": not errors, "errors": errors}
    return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}


extraction_mcp_server = create_sdk_mcp_server(
    name="extraction", version="1.0.0", tools=[validate_extraction]
)
