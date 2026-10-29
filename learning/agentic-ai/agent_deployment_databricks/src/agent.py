import json
import mlflow
from databricks.sdk import WorkspaceClient
from .config import Settings
from .tools import TOOL_DEFINITIONS, execute_tool

SYSTEM_PROMPT = """You are a governed enterprise assistant running in a Databricks App.
Be accurate and concise. Use tools only when needed. Never fabricate tool results.
If required information is unavailable, state the limitation."""

class Agent:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = WorkspaceClient().serving_endpoints.get_open_ai_client()
        mlflow.set_tracking_uri("databricks")
        if settings.mlflow_experiment_id:
            mlflow.set_experiment(experiment_id=settings.mlflow_experiment_id)

    @mlflow.trace(name="agent_request", span_type="AGENT")
    def respond(self, user_message: str, conversation: list[dict] | None = None) -> str:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(conversation or [])
        messages.append({"role": "user", "content": user_message})

        first = self.client.chat.completions.create(
            model=self.settings.serving_endpoint,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            temperature=0.1,
            max_tokens=800,
        )
        assistant = first.choices[0].message
        if not assistant.tool_calls:
            return assistant.content or ""

        messages.append(assistant.model_dump(exclude_none=True))
        for call in assistant.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            result = execute_tool(call.function.name, args)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result),
            })

        final = self.client.chat.completions.create(
            model=self.settings.serving_endpoint,
            messages=messages,
            temperature=0.1,
            max_tokens=800,
        )
        return final.choices[0].message.content or ""
