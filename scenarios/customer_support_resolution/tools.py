import json
from typing import Any

from claude_agent_sdk import tool, create_sdk_mcp_server
from mcp.types import ToolAnnotations
from claude_agent_sdk.types import McpSdkServerConfig

@tool(
    name="get_customer",
    description=(
        "Retrieve customer information using their customer ID. "
        "Use this tool when the user asks about customer details."
    ),
    input_schema={
        "customer_id": str
    },
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False
    )
)
async def get_customer(args: dict[str, Any]) -> dict[str, Any]:
    """Retrieve customer information using their customer ID."""

    customer_id = args["customer_id"]

    # Simulate fetching customer information from a database or API.
    customer = {
        "customer_id": customer_id,
        "name": "John Doe",
        "email": "john.doe@example.com"
    }

    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(customer, indent=2)
            }
        ]
    }


@tool(
    name="lookup_order",
    description=(
        "Retrieve order information using its order ID. "
        "Use this tool when the user asks about an order's status or items."
    ),
    input_schema={
        "order_id": str
    },
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False
    )
)
async def lookup_order(args: dict[str, Any]) -> dict[str, Any]:
    """Retrieve order information using its order ID."""

    order_id = args["order_id"]

    # Simulate fetching order information from a database or API.
    order = {
        "order_id": order_id,
        "status": "Shipped",
        "items": [
            {"item_id": "123", "name": "Widget A", "quantity": 2},
            {"item_id": "456", "name": "Widget B", "quantity": 1}
        ]
    }

    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(order, indent=2)
            }
        ]
    }


@tool(
    name="process_refund",
    description=(
        "Process a refund for an existing order. "
        "Use this tool when the customer explicitly requests a refund. "
        "Requires an order ID and refund amount."
    ),
    input_schema={
        "order_id": str,
        "amount": float
    },
    annotations=ToolAnnotations(
        read_only_hint=False,
        destructive_hint=True,
        idempotent_hint=False,
        open_world_hint=True
    )
)
async def process_refund(args: dict[str, Any]) -> dict[str, Any]:
    """Process a refund for the specified order ID and amount."""

    order_id = args["order_id"]
    amount = args["amount"]

    # Simulate processing a refund.
    result = {
        "order_id": order_id,
        "refund_amount": amount,
        "status": "Refund processed successfully"
    }

    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(result, indent=2)
            }
        ]
    }


@tool(
    name="escalate_to_human_support",
    description=(
        "Escalate a customer's issue to human support for further assistance. "
        "Use this tool when the issue requires human investigation or cannot "
        "be resolved by the available customer-support tools."
    ),
    input_schema={
        "issue_description": str
    },
    annotations=ToolAnnotations(
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=True
    )
)
async def escalate_to_human_support(args: dict[str, Any]) -> dict[str, Any]:
    """Escalate the customer's issue to human support."""

    issue_description = args["issue_description"]

    # Simulate escalating the issue to human support.
    result = {
        "issue_description": issue_description,
        "status": "Issue escalated to human support"
    }

    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(result, indent=2)
            }
        ]
    }

customer_support_mcp_server: McpSdkServerConfig = create_sdk_mcp_server(
    name = "Customer Support MCP server",
    version="1.0.0",
    tools=[
        get_customer, lookup_order, process_refund, escalate_to_human_support
    ]
)