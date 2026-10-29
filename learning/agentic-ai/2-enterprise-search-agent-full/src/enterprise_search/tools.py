"""MCP-style tool contracts.

The contract is deliberately the same shape MCP uses - ``name``,
``description``, ``inputSchema`` (JSON Schema) - so these tools can be exposed
over a real MCP server without changing the handlers. The point of the contract
is that the agent reasons about *what* a tool does while the handler owns *how*:
auth, transport, retries, and legacy response shapes stay behind the boundary.
"""

from dataclasses import dataclass, field
from typing import Any, Callable

JSON_TYPES: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "array": list,
    "object": dict,
}


class ToolError(Exception):
    """Raised for an unknown tool or arguments that fail the schema.

    A distinct exception type so the API layer can answer 400 (the caller sent
    something wrong) instead of 500 (we are broken).
    """


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[..., dict[str, Any]]
    # Idempotent tools are safe to retry after a timeout. Non-idempotent ones are
    # not: a retried "create refund" charges twice. The agent needs this flag to
    # choose between retry and resume, so it belongs in the contract.
    idempotent: bool = True

    def validate(self, arguments: dict[str, Any]) -> None:
        properties = self.input_schema.get("properties", {})
        required = self.input_schema.get("required", [])

        missing = [name for name in required if name not in arguments]
        if missing:
            raise ToolError(f"{self.name}: missing required argument(s) {missing}")

        unexpected = [name for name in arguments if name not in properties]
        if unexpected:
            raise ToolError(f"{self.name}: unexpected argument(s) {unexpected}")

        for name, value in arguments.items():
            expected = JSON_TYPES.get(properties[name].get("type", "string"), object)
            if not isinstance(value, expected):
                raise ToolError(
                    f"{self.name}: argument '{name}' must be "
                    f"{properties[name].get('type')}, got {type(value).__name__}"
                )


@dataclass
class ToolRegistry:
    tools: dict[str, Tool] = field(default_factory=dict)

    def register(self, tool: Tool) -> None:
        self.tools[tool.name] = tool

    def invoke(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        tool = self.tools.get(name)
        if tool is None:
            raise ToolError(f"unknown tool '{name}'")
        tool.validate(arguments)  # validate before calling, never inside the handler
        return tool.handler(**arguments)

    def describe(self) -> list[dict[str, Any]]:
        """Advertise the catalogue. This is what an agent reads to plan a call."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
                "idempotent": tool.idempotent,
            }
            for tool in self.tools.values()
        ]


# --------------------------------------------------------------------------- #
# Handlers. In production each of these wraps a real HTTP/gRPC client; here they
# return canned data so the demo runs with no external dependency. Each returns a
# "summary" field so the agent can answer without knowing the payload shape.
# --------------------------------------------------------------------------- #

def get_order(order_id: str) -> dict[str, Any]:
    return {
        "order_id": order_id,
        "status": "READY_FOR_PICKUP",
        "store": "Makro Demo Store",
        "total": 1840.50,
        "currency": "THB",
        "source": "legacy-order-api-demo",
        "summary": (
            f"Order {order_id} has status READY_FOR_PICKUP at Makro Demo Store. "
            f"Total 1840.5 THB."
        ),
    }


def get_product(sku: str) -> dict[str, Any]:
    return {
        "sku": sku,
        "name": "Bulk Palm Cooking Oil 10L",
        "price": 620.00,
        "currency": "THB",
        "in_stock": True,
        "source": "product-api-demo",
        "summary": (
            f"SKU {sku} is Bulk Palm Cooking Oil 10L at 620.0 THB and is currently in stock."
        ),
    }


ORDER_TOOL = Tool(
    name="get_order",
    description="Look up one order by its exact order identifier.",
    input_schema={
        "type": "object",
        "properties": {"order_id": {"type": "string", "description": "e.g. ORDER-123456"}},
        "required": ["order_id"],
    },
    handler=get_order,
    idempotent=True,
)

PRODUCT_TOOL = Tool(
    name="get_product",
    description="Look up one product by its exact SKU.",
    input_schema={
        "type": "object",
        "properties": {"sku": {"type": "string", "description": "e.g. SKU-99881"}},
        "required": ["sku"],
    },
    handler=get_product,
    idempotent=True,
)


def default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(ORDER_TOOL)
    registry.register(PRODUCT_TOOL)
    return registry
