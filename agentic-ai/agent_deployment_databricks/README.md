# Agent Deployment on Databricks

A lecture-ready FastAPI agent deployed as a Databricks App and packaged with a Declarative Automation Bundle.

## Architecture

`Client -> Databricks App/FastAPI -> Unity Gateway -> Model Serving endpoint`

MLflow tracing wraps the agent request. The app service principal receives least-privilege access through declared app resources.

## Project structure

- `src/agent.py`: LLM orchestration and tool-call loop
- `src/server.py`: `/health` and `/chat` endpoints
- `src/tools.py`: example current-time tool
- `app.yaml`: runtime command and resource injection
- `databricks.yml`: bundle, app, resources, permissions, targets
- `tests/`: smoke test

## Prerequisites

1. Databricks CLI 0.250.0 or newer.
2. A workspace profile with permission to deploy apps.
3. An existing Model Serving endpoint.
4. An existing MLflow experiment.
5. Replace workspace host placeholders in `databricks.yml`.

## Local validation

```bash
uv sync --extra dev
export SERVING_ENDPOINT=<endpoint-name>
export DATABRICKS_HOST=<workspace-url>
export DATABRICKS_TOKEN=<development-token>
uv run pytest
uv run start-server
```

Do not place personal tokens in app configuration. A deployed Databricks App uses its service principal identity and attached resources.

## Configure variables

Create `databricks.yml` target overrides or pass variables on the CLI:

```bash
databricks bundle validate -t dev   --var="serving_endpoint_name=<endpoint-name>,experiment_id=<experiment-id>"
```

## Deploy

```bash
# 1. Validate and deploy resource declarations plus synchronized source
databricks bundle validate -t dev   --var="serving_endpoint_name=<endpoint-name>,experiment_id=<experiment-id>"

databricks bundle deploy -t dev   --var="serving_endpoint_name=<endpoint-name>,experiment_id=<experiment-id>"

# 2. Obtain the synchronized workspace source path from bundle summary/output.
# If your workspace process requires a separate Apps source deployment:
databricks apps deploy agent-deployment-demo-dev   --source-code-path /Workspace/Users/<user>/.bundle/agent-deployment-demo/dev/files
```

Deployment behavior can vary with CLI and Apps releases. Run `databricks bundle validate` against the target workspace schema before deployment.

## Test the API

```bash
curl -X POST "$APP_URL/chat"   -H "Content-Type: application/json"   -d '{"message":"What time is it in UTC?"}'
```

## Production extensions

- Replace the example tool with Unity Catalog functions, MCP tools, or AI Search.
- Add authentication-aware authorization and request-size policies.
- Add retries with bounded exponential backoff around idempotent inference calls.
- Define scorer jobs and evaluation datasets in a separate evaluation pipeline.
- Archive selected traces to governed Delta tables according to retention policy.
- Configure Unity Gateway policies, budgets, rate limits, usage tracking, and request/response logging in the platform.
