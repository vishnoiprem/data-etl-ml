from dataclasses import dataclass
from typing import Any, Callable

@dataclass
class Tool:
    name: str
    description: str
    required: list[str]
    handler: Callable[..., dict[str, Any]]
    idempotent: bool = True

class ToolRegistry:
    def __init__(self):
        self.tools = {}
    def register(self, tool: Tool):
        self.tools[tool.name] = tool
    def invoke(self, name: str, arguments: dict):
        tool = self.tools[name]
        missing = [x for x in tool.required if x not in arguments]
        if missing:
            raise ValueError(f"Missing fields: {missing}")
        return tool.handler(**arguments)
    def describe(self):
        return [{"name": t.name, "description": t.description, "required": t.required, "idempotent": t.idempotent} for t in self.tools.values()]

def get_order(order_id: str):
    return {"order_id": order_id, "status": "READY_FOR_PICKUP", "store": "Makro Demo Store", "total": 1840.50, "currency": "THB", "source": "legacy-order-api-demo"}
