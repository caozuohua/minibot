# AGENTS.md

MiniBot — lightweight autonomous agent for Lark (飞书), designed for small VPS deployment.

## Quick Start

```bash
# Install dependencies (use --break-system-packages on Ubuntu 25.10+)
pip install -r requirements.txt --break-system-packages

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys

# Validate config
python main.py --validate

# Run
python main.py
```

## Architecture

```
main.py                    → Entry point, wires all components
src/config.py              → YAML → dataclass, ${VAR} env resolution
src/gateway/lark_gateway.py → Lark WebSocket, message receive + card push
src/agent/core.py          → Agent orchestrator (ReAct + Reflection + ToT)
src/agent/react.py         → ReAct reasoning engine
src/agent/reflection.py    → Reflection/critique engine
src/agent/tot.py           → Tree of Thoughts (3 branches × 3 depth)
src/models/router.py       → Multi-provider fallback (OpenAI → Gemini → NVIDIA)
src/memory/manager.py      → SQLite memory with cosine similarity search
src/tools/registry.py      → 6 built-in tools (shell, search, read/write/edit, browser)
src/skills/registry.py     → YAML skill loader + trigger matching
```

## Environment Variables

All secrets go in `.env` (gitignored). Key variables:
- `OPENAI_API_KEY`, `OPENAI_BASE_URL` — primary model
- `GEMINI_API_KEY` — fallback model
- `NVIDIA_API_KEY` — embed-only provider
- `LARK_APP_ID`, `LARK_APP_SECRET` — Lark gateway auth
- `TAVILY_API_KEY` — search backend
- `MINIBOT_WORK_DIR` — file operations sandbox (default: `./workspace`)

## Configuration

`config.yaml` uses `${VAR}` placeholders resolved from `.env` at runtime. Config validation: `python main.py --validate`.

Key settings:
- `models.providers` — ordered by fallback priority
- `agent.max_iterations: 20` — ReAct loop cap
- `tools.shell_timeout: 30` — seconds
- `tools.work_dir` — sandboxed file ops root
- `memory.db_path: ./data/memory.db` — SQLite store

## Model Providers

Three providers with automatic fallback:
1. **OpenAI** — chat + embeddings (primary)
2. **Gemini** — chat + embeddings (fallback)
3. **NVIDIA NIM** — embeddings only

Provider initialization in `src/models/router.py`. Each provider must implement `chat()` and `embed()`.

## Tools

All tools in `src/tools/`. Registry auto-registers at startup:
- `ShellTool` — command execution with blacklist + timeout + output truncation
- `SearchTool` — Tavily/SearXNG/Google backends
- `ReadFileTool`, `WriteFileTool`, `EditFileTool` — sandboxed to `work_dir`
- `BrowserTool` — curl-based HTML → text

## Skills

YAML-based skills in `skills/` directory. Loader: `src/skills/loader.py`. Example: `skills/check_system.yaml`.

## Memory

SQLite-backed with embedding search (cosine similarity). Memory types: episodic, semantic, procedural. Auto-decay and archival based on `config.yaml` thresholds.

## Gotchas

- Ubuntu 25.10 uses PEP 668 — pip needs `--break-system-packages` or use `uv`
- Lark WebSocket connection requires valid `LARK_APP_ID` + `LARK_APP_SECRET`
- `skills/` directory must exist for skill loader (create manually if missing)
- Memory DB auto-created at `config.memory.db_path` on first run
- Shell tool has output truncation at `tools.output_max_bytes` (default 10KB)
- Search backend requires `TAVILY_API_KEY` or alternative configured

## Testing

No test suite exists yet. To add tests:

```bash
# Install test dependencies
pip install pytest pytest-asyncio --break-system-packages

# Run tests (after creating them)
pytest tests/ -v

# Run a single test file
pytest tests/test_config.py -v
```

Suggested test structure:
```
tests/
├── test_config.py        # Config loading, ${VAR} resolution
├── test_models.py        # Provider fallback logic
├── test_memory.py        # SQLite store, embedding search
├── test_tools.py         # Tool registry, sandbox enforcement
└── test_agent.py         # ReAct loop, mode selection
```

## File Operations

File tools are sandboxed to `tools.work_dir` from config. Never hardcode paths outside this directory in tool calls.

## Adding New Tools

1. Create class in `src/tools/` inheriting from `Tool` (see `base_tool.py`)
2. Implement `name`, `description`, `parameters`, `execute()`
3. Register in `src/tools/registry.py` `_register_defaults()`

## Adding New Providers

1. Create class in `src/models/` inheriting from `ModelProvider`
2. Implement `chat()` and/or `embed()`
3. Add to `src/models/router.py` `_build_providers()`
4. Add config section in `config.yaml`
