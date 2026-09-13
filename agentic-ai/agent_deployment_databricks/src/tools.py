from datetime import datetime, timezone

TOOL_DEFINITIONS = [{
    "type": "function",
    "function": {
        "name": "get_utc_time",
        "description": "Return the current UTC timestamp. Use only when the user asks for current time.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
}]

def execute_tool(name: str, arguments: dict) -> dict:
    if name == "get_utc_time":
        return {"utc_time": datetime.now(timezone.utc).isoformat()}
    raise ValueError(f"Unknown tool: {name}")
