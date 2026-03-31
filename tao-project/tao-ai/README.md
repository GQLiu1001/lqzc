# Tao Harness

`Tao Harness` is a study-first project that follows the same idea as
`learn-claude-code`: the model is the agent, and our code is the harness.

This skeleton intentionally avoids heavy orchestration frameworks.
It focuses on the minimal pieces you need to understand:

- one agent loop
- one model adapter
- one tool registry
- one lightweight knowledge loader
- one SQLite state store
- one FastAPI entrypoint

## What this project is for

This project is designed for your `lqzc` business domain:

- connect a local Ollama model
- wrap Java business APIs as atomic tools
- load domain skills and local manuals on demand
- persist sessions and tool traces to SQLite
- expose a simple chat API for future UI or MCP integration

## Project layout

```text
tao-harness/
  tao_harness/
    api/           # FastAPI entrypoint
    core/          # Agent loop and orchestration glue
    knowledge/     # Manual search and skill loading
    model/         # Ollama adapter
    state/         # SQLite persistence
    tools/         # Tool schema + tool registry + lqzc tools
  prompts/
    system.md
  skills/
    customer_service/SKILL.md
  data/
    .gitkeep
```

## Quick start

1. Start Ollama locally

```bash
ollama serve
ollama pull qwen3:8b
```

2. Create a virtual environment and install dependencies

```bash
cd /Users/rabbittank1001/IdeaProjects/lqzc/tao-ai/tao-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

3. Configure environment variables

```bash
cp .env.example .env
```

4. Start the API

```bash
./.venv/bin/python3 -m uvicorn tao_harness.api.main:app --reload --host 0.0.0.0 --port 8000
```

5. Test the chat endpoint

```bash
 curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Show me the top selling products"}'
```

6. Upload text files for RAG context (saved under workspace `doc/`)

```bash
curl -X POST http://localhost:8000/files/upload \
  -F "session_id=demo-session-001" \
  -F "file=@/absolute/path/to/your.txt"
```

## Current learning scope

This skeleton is intentionally small. It already includes:

- a custom agent loop built around Ollama tool calling
- tool dispatch without LangChain or LangGraph
- session persistence
- lqzc API tool wrappers
- MCP-backed Java tool access for top sales and inventory lookup
- local manual search
- on-demand skill loading

It does **not** yet include:

- multi-agent mailboxes
- context compression
- background jobs
- advanced permissions

Those can be layered on top later, after the base loop feels natural.

## Java MCP server

The Python harness calls the Java MCP endpoint directly (default: `http://localhost:8001/mcp`) for:

- `get_top_sales` -> Java MCP `getTopSales`
- `get_inventory_by_model` -> Java MCP `getInventoryByModel`

Environment switches:

```bash
LQZC_MCP_ENABLED=true
LQZC_MCP_URL=http://localhost:8001/mcp
```
