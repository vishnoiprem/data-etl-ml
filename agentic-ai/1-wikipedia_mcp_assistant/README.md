# Wikipedia MCP Research Assistant

A small end-to-end MCP project with:

- **Tools**: fetch an article summary, list sections, and read one section.
- **Prompt**: ask the model to select important sections.
- **Resource**: expose a static topic-suggestion file.
- **Client**: use LangGraph, OpenAI, and MCP over `stdio`.

## Folder structure

```text
wikipedia_mcp_assistant/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── suggested_titles.txt
├── mcp_server.py
└── mcp_client.py
```

## 1. Create and activate a virtual environment

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

## 2. Install packages

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The standard `wikipedia` package already exposes `page.sections` and
`page.section(...)`; this project therefore does not require a separate
`wikipedia_sections` package.

## 3. Configure the API key

Copy the example file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Edit `.env`:

```dotenv
OPENAI_API_KEY=your_real_key_here
OPENAI_MODEL=gpt-4.1-mini
```

Never commit `.env`.

## 4. Run the application

Run only the client. The client launches the MCP server automatically as a
subprocess over `stdio`:

```bash
python mcp_client.py
```

## 5. Try these commands

```text
Tell me about Alan Turing.
List the sections of the carbon cycle article.
Explain the History section of the Coronavirus article.
/prompts
/prompt highlight_sections_prompt "Greenhouse effect"
/resources
/resource suggested_titles
/quit
```

## Execution flow

```text
User
  -> LangGraph chat node
  -> OpenAI model chooses an MCP tool
  -> MCP client sends a structured request over stdio
  -> Python MCP server executes the Wikipedia function
  -> Tool result returns to the model
  -> Final answer returns to the user
```

## Tools, prompts, and resources

- A **tool** executes code and returns a result.
- A **prompt** returns reusable instructions for the model.
- A **resource** returns read-only context identified by a URI.

## Important implementation details

1. Tool docstrings matter because the model uses names, descriptions, and
   argument schemas to select a tool.
2. The server prints its startup message to `stderr`, not `stdout`, because
   `stdout` carries MCP protocol messages in `stdio` mode.
3. The server limits section output to protect the model context window.
4. Ambiguous topics return suggestions instead of silently choosing a page.
5. `sys.executable` ensures the client starts the server with the same Python
   virtual environment.
