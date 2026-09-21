# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this project is

**AI Vacation Planner** — a FastAPI backend that plans trips end-to-end with an
LLM. It is a capstone built in phases; each phase layers onto the previous one.

| Phase | Theme | What landed |
|-------|-------|-------------|
| 1 | Python & FastAPI | Users / Trips / Itineraries CRUD, JWT auth, Alembic, background email |
| 2 | LLM foundations | Prompt-driven itinerary generation via the Anthropic SDK |
| 3 | Designing AI systems | Pydantic-validated structured output + retry-on-invalid |
| 4 | RAG | Chroma vector store over travel PDFs, `/itineraries/ask` |
| 5 | Frameworks & orchestration | **LangChain + LangGraph tool-using agent** (`app/agents/`) |

## Commands

```bash
uv sync                                  # install deps (Python 3.12)
uv run fastapi dev app/main.py           # run the API at http://127.0.0.1:8000
uv run alembic upgrade head              # apply migrations
uv run alembic revision --autogenerate -m "msg"
uv run python scripts/build_source_pdfs.py   # generate sample knowledge-base PDFs
uv run python scripts/ingest.py              # embed PDFs into Chroma
```

Swagger lives at `/docs`.

## Architecture

```
app/
├── api/v1/          # HTTP layer only — parse, delegate, serialize
├── services/        # business logic, DB orchestration
├── agents/          # PHASE 5: LangGraph graphs, tools, prompts, LLM factory
│   ├── graph.py             # ReAct agent: agent ⇄ tools loop
│   ├── itinerary_graph.py   # itinerary workflow: load → research → draft → review → persist
│   ├── tools/               # one module per tool, all registered in tools/__init__.py
│   ├── llm.py               # ChatAnthropic factory (single place the model is configured)
│   ├── prompts.py           # system prompts
│   └── state.py             # TypedDict graph states
├── ai/              # PHASE 2–3 raw-SDK path. Superseded by agents/; only
│                    #   RAG_SYSTEM_PROMPT is still imported (by utils/rag.py).
│                    #   chat/messages.py and get_prompts() are now unused.
├── models/          # SQLAlchemy 2.0 declarative models
├── schemas/         # Pydantic v2 request/response models
├── utils/           # RAG plumbing: chunking, embeddings, vector_store, pdf_loader
├── core/            # settings (pydantic-settings) + auth dependencies
└── db/              # async engine + session
```

**Request path:** `api/v1/*.py` → `services/*.py` → (`agents/` for AI work) → `models/`.
Endpoints must not build prompts or talk to Chroma directly.

## Conventions

- **Async everywhere.** The DB engine is async (`psycopg3`), so services and
  route handlers are `async def`. Blocking libraries (Chroma, SentenceTransformers)
  must be wrapped in `anyio.to_thread.run_sync`, never called inline.
- **UUID primary keys** on every table.
- **Settings** come from `app/core/config.py` (`settings`). Do not read
  `os.getenv` in new code — `app/utils/config.py` is legacy RAG config kept for
  the ingest scripts.
- **Model id** is `settings.LLM_MODEL`, default `claude-haiku-4-5`. Do not
  hardcode model strings anywhere else.
- Pydantic v2 only (`model_validate`, `model_dump`, `ConfigDict`).

## Adding an agent tool

1. Create `app/agents/tools/<name>.py` with a `@tool`-decorated `async def`.
2. Give it an `args_schema` (Pydantic) and a docstring — the docstring *is* the
   prompt the model reads to decide when to call it, so state when to use it and
   what it returns.
3. Return JSON-serializable dicts. Never raise on an expected failure; return
   `{"error": "..."}` so the agent can recover in the loop.
4. Register it in `app/agents/tools/__init__.py::TRAVEL_TOOLS`.

External tool APIs in use are keyless (Open-Meteo, OpenStreetMap Nominatim);
keep it that way unless the user supplies a key.

## Gotchas

- `app/core/dependancies.py` is spelled that way. Leave it.
- `Trip` has `start_datetime`/`end_datetime`, not a `days` column — trip length
  is derived. `app/services/trip.py::create_trip` still references `days`; it is
  a known bug, unrelated to phase 5.
- The Chroma collection is built once in the `lifespan` handler and lives on
  `app.state.collection`. Rebuilding it per request reloads a 90 MB model.
- `scripts/ingest.py` must be run before `/itineraries/ask` or the knowledge
  tool returns empty results.
