# AI Vacation Planner

An intelligent travel planning application that helps users create, manage, and organize vacation trips with AI-generated itineraries.

---

# Features

- **Voice (phase 6):** create a trip by speaking, or talk to the agent and get
  the answer back as speech — Whisper speech-to-text, Edge neural text-to-speech
- **Image understanding (phase 6):** send a photo and the agent works out what
  and where it is, then plans around it
- **MCP tools (phase 6):** weather, maps and pricing are served by an MCP server
  that the agent connects to as an MCP client — and that Claude Desktop or any
  other MCP client can use too
- **Tool-using AI agent (phase 5):** a LangGraph agent that decides which tools a
  request needs — travel knowledge base, weather, place lookup, distances, cost
  estimates, trip records — runs them, and answers from the results
- **Agentic itinerary generation:** a LangGraph workflow that researches with
  tools, drafts a schema-validated itinerary, reviews it against the trip's real
  dates and budget, and re-drafts until it passes
- **Travel knowledge base (RAG):** Chroma vector store over destination guides
- User Authentication: JWT-based authentication with secure password hashing
- Trip Management: Create, read, update, and delete travel trips
- Itinerary Planning: Generate day-by-day itineraries with activities
- User Roles: Admin, Manager, and User role-based access
- Database: PostgreSQL with async SQLAlchemy ORM
- API Documentation: Auto-generated OpenAPI/Swagger docs

---

# Tech Stack

- **Framework:** FastAPI 0.136+
- **Agent orchestration:** LangGraph 1.x + LangChain Core 1.x
- **LLM:** Anthropic Claude (`claude-haiku-4-5`) via `langchain-anthropic`
- **Tool protocol:** MCP — `mcp` Python SDK (FastMCP) + `langchain-mcp-adapters`
- **Speech-to-text:** Whisper (`openai/whisper-base`) via `transformers`, decoded with ffmpeg
- **Text-to-speech:** Microsoft Edge neural voices via `edge-tts`
- **Vector store:** ChromaDB with `sentence-transformers` embeddings
- **Database:** PostgreSQL with psycopg3
- **ORM:** SQLAlchemy 2.0+ (async)
- **Authentication:** JWT (PyJWT) with pwdlib (Argon2)
- **Migrations:** Alembic
- **Validation:** Pydantic v2
- **Python:** 3.12+

---

# Project Structure

```bash
ai-vacation-planner/
├── app/
│   ├── api/                 # API endpoints
│   │   ├── v1/              # API version 1
│   │   │   ├── auth.py      # Authentication endpoints
│   │   │   ├── trips.py     # Trip CRUD endpoints
│   │   │   ├── itineraries.py # Itinerary + AI generation endpoints
│   │   │   ├── agent.py     # PHASE 5: agent chat endpoint
│   │   │   ├── multimodal.py # PHASE 6: voice + image endpoints
│   │   │   └── users.py     # User endpoints
│   │   └── router.py        # Main router configuration
│   ├── mcp/                 # PHASE 6: Model Context Protocol
│   │   ├── server.py        # MCP server exposing the travel tools
│   │   └── client.py        # MCP client: connects at startup, loads tools for the agent
│   ├── agents/              # PHASE 5: LangChain + LangGraph orchestration
│   │   ├── graph.py         # ReAct agent graph (agent <-> tools loop)
│   │   ├── itinerary_graph.py # Itinerary workflow graph
│   │   ├── llm.py           # ChatAnthropic factory
│   │   ├── prompts.py       # System prompts
│   │   ├── state.py         # TypedDict graph states
│   │   └── tools/           # The agent's tools
│   │       ├── trips.py     #   trip record lookup (database)
│   │       ├── knowledge.py #   travel knowledge base (RAG / Chroma)
│   │       ├── weather.py   #   Open-Meteo forecast + climate normals
│   │       ├── maps.py      #   OpenStreetMap place search + distances
│   │       ├── pricing.py   #   trip cost estimator
│   │       ├── geocoding.py #   shared place -> coordinates helper
│   │       └── http.py      #   shared HTTP client + error normalisation
│   ├── ai/                  # PHASE 2-3 raw Anthropic SDK path; only the RAG
│   │                        #   system prompt is still live (used by /ask)
│   ├── utils/               # RAG plumbing: chunking, embeddings, vector store
│   │   └── speech.py        # PHASE 6: speech-to-text + text-to-speech
│   ├── core/                # Core configuration
│   │   ├── config.py        # Settings and environment variables
│   │   └── dependancies.py  # Dependency injection
│   ├── db/                  # Database configuration
│   │   ├── base.py          # SQLAlchemy base
│   │   └── session.py       # Async session management
│   ├── enums/               # Enumerations
│   │   ├── trip_budget_enum.py
│   │   └── user_role_enum.py
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py          # User model
│   │   ├── trip.py          # Trip model
│   │   ├── itinerary.py # Itinerary day model
│   │   ├── activity.py      # Activity model
│   │   └── user_trips.py    # Many-to-many association
│   ├── schemas/             # Pydantic schemas
│   │   ├── auth/            # Auth request/response schemas
│   │   ├── trip/            # Trip schemas
│   │   ├── itinerary/       # Itinerary schemas
│   │   ├── multimodal/      # PHASE 6: spoken-trip extraction + voice responses
│   │   └── user/            # User schemas
│   ├── services/            # Business logic
│   │   ├── auth.py          # Authentication service
│   │   ├── trip.py          # Trip service
│   │   ├── itinerary.py     # Itinerary service
│   │   ├── multimodal.py    # PHASE 6: speech -> trip, speech -> agent -> speech
│   │   └── user.py          # User service
│   └── main.py              # FastAPI application entry point
├── alembic/                 # Database migrations
├── .env                     # Environment variables
├── pyproject.toml           # Project dependencies
└── README.md                # This file
```

---

# How It Works

## 1. Authentication Flow

The application uses JWT-based authentication:
The application uses JWT-based authentication. When a user registers, the system:

1. Validates the uniqueness of the username and email.
2. Hashes the password using Argon2.
3. Adds a **Background Task** to send a welcome email, ensuring the user registration response remains fast and non-blocking.

## 2. Trip Management

Trips are created with destination, budget, days, and style:
Trips are created with destination, budget, days, and style.

## 3. Itinerary Generation

## 3. Email & Background Tasks

To improve performance, long-running operations like sending emails are handled as background tasks. The `app/services/auth.py` service leverages FastAPI's `BackgroundTasks` to trigger `send_welcome_email` without delaying the HTTP response to the client. The email utility uses `fastapi-mail` and Jinja2 templates for HTML content.

## 4. Itinerary Generation

Itineraries are structured with days and activities:

## 5. Database Models

The application uses SQLAlchemy 2.0 with async support.

## 6. API Endpoints

The API is organized with versioning.

---

# Phase 5 — Frameworks & Orchestration

## What changed

Phase 4 ran one fixed chain. Every request retrieved from the knowledge base,
whether or not retrieval was the right move, and nothing else was ever consulted:

```
Trip details  ->  Retrieve travel knowledge  ->  LLM response
```

Phase 5 replaces that with an agent that chooses:

```
User request -> Agent decides -> Tool(s) run -> LLM combines results -> Response
                     ^                |
                     +----------------+   (loops until it can answer)
```

The model sees every tool's description and picks. "What's the weather in Kigali
in April?" calls weather only. "Plan my Paris trip with weather-friendly
activities and keep it under $1,500" calls the trip record, weather, place
search and the cost estimator, then writes a plan from all four.

## The graphs

Both live in `app/agents/` and are built with **LangGraph**.

### 1. Conversational agent — `app/agents/graph.py`

A ReAct loop. `tools_condition` sends control to the tool node whenever the
model emitted tool calls, and to `END` when it answers in text.

```
START -> agent -> (tools -> agent)* -> END
```

Conversation state is checkpointed with `InMemorySaver`, keyed by `thread_id`,
so follow-up turns remember the earlier ones. (Swap in
`AsyncPostgresSaver` to survive restarts or run more than one worker.)

Exposed as **`POST /api/v1/agent/chat`**.

### 2. Itinerary workflow — `app/agents/itinerary_graph.py`

Generation is not a single prompt any more. It is a graph with a research agent
inside it and a validation loop around it:

```
START -> load_trip -> research -> draft -> review -+-> persist -> END
                         ^                         |
                         |   (agent <-> tools)     |
                         +--------- redraft <------+
```

| Node | What it does |
|------|--------------|
| `load_trip` | Reads the trip from Postgres. Short-circuits to `END` on a bad id. |
| `research` | A **ReAct sub-agent** with the fact-gathering tools. It decides what to look up and returns a research brief. |
| `draft` | Turns the brief into an itinerary using **structured output** (`with_structured_output(LLMItineraryResponse)`), so the result is Pydantic-validated by construction. |
| `review` | Checks what the schema cannot: right number of days, dates matching the trip, days not empty, activities not ending before they start. |
| `persist` | Replaces the trip's stored itinerary in one transaction. |

`review` routes back to `draft` with the specific complaints attached, up to
`ITINERARY_MAX_REVISIONS` times. When the revision budget runs out the best
draft is still returned, with the outstanding problems reported in `issues`
rather than failing the request.

Exposed as **`POST /api/v1/itineraries/generate/{trip_id}`**.

## The tools

Each is a `@tool`-decorated async function in `app/agents/tools/`, with a
Pydantic `args_schema`. The docstring is what the model reads to decide whether
to call it, so it states when to use the tool and how to interpret the result.

| Tool | Backed by | What the agent uses it for |
|------|-----------|----------------------------|
| `get_trip_details` | PostgreSQL | Destination, dates, length, budget, style of a saved trip |
| `get_saved_itinerary` | PostgreSQL | The plan already stored, before changing it |
| `search_travel_knowledge` | **Chroma + sentence-transformers (the phase 4 RAG)** | Guides, permits, hours, local tips, hidden gems |
| `get_weather_forecast` | Open-Meteo | Per-day conditions, with wet days flagged |
| `find_places` | OpenStreetMap Nominatim | Real places with addresses and coordinates |
| `get_distance_between` | Open-Meteo geocoding + haversine | Whether two activities can share a day |
| `estimate_trip_cost` | Local cost model | Category breakdown and a budget feasibility check |

All external APIs are **keyless** — no maps or weather key is needed to run this.

### Honesty rules built into the tools

The tools are written so the agent cannot accidentally overclaim:

- Open-Meteo only forecasts ~16 days out. Beyond that, `get_weather_forecast`
  falls back to the same calendar dates averaged over the last three years and
  returns `source: "historical_average"`. The prompt forbids calling that a
  forecast.
- `estimate_trip_cost` is a **model**, not a price feed — there is no free
  live-pricing API. Every response carries a `disclaimer`, a `confidence` and an
  `excludes` list, and says so.
- `get_distance_between` returns straight-line distance with a road factor, and
  labels itself as not a routed itinerary.
- An empty `find_places` result says OpenStreetMap has no match — explicitly not
  that the place does not exist.
- Tools never raise on an expected failure. They return `{"error": ...}` so the
  agent can say what it could not verify and carry on.

## LLM integration details

| Setting | Value | Where |
|---------|-------|-------|
| Model | `claude-haiku-4-5` | `settings.LLM_MODEL` |
| Client | `ChatAnthropic` (`langchain-anthropic`) | `app/agents/llm.py` |
| Temperature | `0.3` | `settings.LLM_TEMPERATURE` |
| Max tokens | `4096` | `settings.LLM_MAX_TOKENS` |
| Tool binding | `.bind_tools(TRAVEL_TOOLS)` | `app/agents/graph.py` |
| Structured output | `.with_structured_output(LLMItineraryResponse)` | `app/agents/itinerary_graph.py` |
| Loop ceiling | `18` agent/tool round trips | `settings.AGENT_RECURSION_LIMIT` |
| Re-draft budget | `2` | `settings.ITINERARY_MAX_REVISIONS` |

`app/agents/llm.py` is the only place the model is configured; nothing else
hardcodes a model id.

## Example

```bash
curl -X POST "http://localhost:8000/api/v1/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Plan my Paris trip and include weather-friendly activities.",
       "trip_id": "<trip-uuid>"}'
```

```json
{
  "thread_id": "3f2b...",
  "answer": "Your trip runs 12-16 October...",
  "tools_used": [
    "get_trip_details",
    "get_weather_forecast",
    "search_travel_knowledge",
    "find_places",
    "estimate_trip_cost"
  ]
}
```

`tools_used` is returned on purpose: it shows which tools the agent chose for
that request, which is the whole point of this phase.

Continue the conversation by passing the `thread_id` back:

```bash
curl -X POST "http://localhost:8000/api/v1/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Make day 2 cheaper.", "thread_id": "3f2b..."}'
```

---

# Phase 6 — Multimodal AI & MCP

## What changed

Phase 5 took text in and gave text back, and every tool was a Python function
imported straight into the agent. Phase 6 adds two things:

1. **MCP (Model Context Protocol).** The tools that call outside travel
   services — weather, maps, pricing — now live behind an MCP server. The agent
   is an MCP client: it discovers those tools over the protocol at startup and
   calls them through it.
2. **Voice and images.** A traveller can create a trip by speaking, talk to the
   agent and hear the answer, or send a photo and plan around it.

```
 speech ──► Whisper (STT) ──► transcript ──┐
 photo  ───────────────────────────────────┼──► LangGraph agent (Claude) ──► answer ──► Edge TTS ──► MP3
 text   ───────────────────────────────────┘           │
                                                       ├── local tools: trip records (Postgres),
                                                       │                knowledge base (Chroma)
                                                       └── MCP client ══ stdio ══► MCP server (app/mcp/server.py)
                                                                                   weather · places · distances · cost
```

## MCP

### The server — `app/mcp/server.py`

A FastMCP server (official `mcp` Python SDK) named `vacation-planner-travel`,
exposing the tools that talk to external services:

| MCP tool | Backed by |
|----------|-----------|
| `get_weather_forecast` | Open-Meteo forecast + archive |
| `find_places` | OpenStreetMap Nominatim |
| `get_distance_between` | Open-Meteo geocoding + haversine |
| `estimate_trip_cost` | Local cost model |

Each tool still has a single definition: the phase 5 LangChain tools are
converted with `langchain_mcp_adapters.tools.to_fastmcp`, so the name,
description and JSON schema an MCP client sees are exactly what the agent saw
before.

The tools that read the app's own data — `get_trip_details`,
`get_saved_itinerary` and `search_travel_knowledge` — stay in-process. They need
the database and the 90 MB embedding model, which belong to the API process.

### The client — `app/mcp/client.py`

`MCP_SERVERS` lists the servers the agent connects to. At startup the FastAPI
`lifespan` opens one persistent session per server
(`MultiServerMCPClient.session` + `load_mcp_tools`), so tool calls go over an
open pipe instead of starting the server for every call. The MCP tools are bound
next to the local ones in both graphs:

```python
tools = [*TRAVEL_TOOLS, *get_mcp_tools()]    # app/agents/graph.py
tools = [*RESEARCH_TOOLS, *get_mcp_tools()]  # app/agents/itinerary_graph.py (research step)
```

Stopping the API closes the session and the server process with it.

Connecting another MCP server — a calendar, a booking service, a hosted maps
server — is one more entry in `MCP_SERVERS`; every tool it exposes reaches the
agent without touching the graphs.

### Using the travel tools from other MCP clients

It is a standard MCP server, so any MCP client can use it. For example, in
Claude Desktop's `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "vacation-planner-travel": {
      "command": "uv",
      "args": [
        "--directory", "/absolute/path/to/AI-Vacation-Planner",
        "run", "python", "-m", "app.mcp.server"
      ]
    }
  }
}
```

The server reads the same `.env` as the API, which is why it is started from
the project directory.

## Voice

### Speech-to-text

- **Whisper** (`openai/whisper-base`, set by `STT_MODEL`) runs locally through
  Hugging Face `transformers` — no API key, and the audio never leaves the
  server.
- Uploads are decoded by **ffmpeg** into 16 kHz mono audio, so WAV, MP3, M4A
  (phone voice memos), OGG/Opus and WebM recordings all work.
- Transcription runs in a worker thread (`anyio.to_thread.run_sync`), like the
  other blocking ML code. The model loads on the first voice request (about
  290 MB is downloaded the first time).

### Text-to-speech

- **Microsoft Edge neural voices** through `edge-tts` — keyless, like the other
  external services — returning MP3. The voice is set by `TTS_VOICE` (default
  `en-US-AriaNeural`).
- Voice questions reach the agent with `SPOKEN_REPLY_PROMPT` attached: the reply
  will be read aloud, so it must be plain sentences with no markdown, lists or
  links, under about 250 words.

### Create a trip by voice — `POST /api/v1/multimodal/voice/trips`

```
audio ─► Whisper ─► transcript ─► Claude structured output (SpokenTripDetails) ─► CreateTripRequest ─► trips table
```

1. The transcript goes to Claude with
   `with_structured_output(SpokenTripDetails)`, which also resolves relative
   dates ("next Friday", "five days from 12 March") against today.
2. Destination, start date and end date are required. When the recording does
   not give them, the endpoint returns **422** with the transcript and the
   `missing` fields instead of guessing.
3. The result goes through the same `CreateTripRequest` validation as the
   manual endpoint (future dates, end after start) and is saved for the
   logged-in user.

### Talk to the agent — `POST /api/v1/multimodal/voice/chat`

Speech in, speech out. The transcript is sent to the same agent as
`/agent/chat` — so it can read trips, search the knowledge base and call the MCP
tools — and the answer comes back as an MP3 file. The rest is in the headers:

| Header | Meaning |
|--------|---------|
| `X-Thread-Id` | Pass back as `thread_id` to continue the conversation, by voice or text |
| `X-Transcript` | What Whisper heard (URL-encoded) |
| `X-Tools-Used` | Tools the agent called this turn |

## Image understanding — `POST /api/v1/multimodal/image/chat`

Upload a photo (JPEG, PNG, GIF or WebP, up to 5 MB) with an optional question.
The photo joins the agent's turn as an image content block, which
`ChatAnthropic` sends to Claude as a base64 image. Claude works out what and
where it shows, then the agent uses its tools on that — for a photo of Belém
Tower: Lisbon's weather, nearby places, the cost of a short stay. The photo
stays in the conversation thread, so follow-up questions can refer to it.

## LLM integration details (phase 6)

| Capability | Model / service | Where |
|------------|-----------------|-------|
| Agent reasoning, tool choice, image understanding | Claude (`settings.LLM_MODEL`) via `ChatAnthropic` | `app/agents/graph.py` |
| Trip extraction from speech | Claude, `temperature=0`, `.with_structured_output(SpokenTripDetails)` | `app/services/multimodal.py` |
| Speech-to-text | Whisper `openai/whisper-base`, local, via `transformers` | `app/utils/speech.py` |
| Text-to-speech | Microsoft Edge neural TTS via `edge-tts` | `app/utils/speech.py` |
| Tool protocol | MCP over stdio — `mcp` (FastMCP) + `langchain-mcp-adapters` | `app/mcp/` |

The Claude API neither accepts nor produces audio, so speech is handled by
Whisper and Edge TTS on either side of the agent.

## Examples

Create a trip by speaking:

```bash
curl -X POST "http://localhost:8000/api/v1/multimodal/voice/trips" \
  -H "Authorization: Bearer <your-token>" \
  -F "audio=@trip-request.m4a"
```

```json
{
  "transcript": "I want to plan a trip to Lisbon from the 12th to the 16th of November with a budget of $1,500. I love food markets and old neighborhoods.",
  "trip": {
    "id": "807a2aaf-...",
    "title": "Lisbon food and neighborhoods",
    "description": "A food-focused trip to Lisbon exploring markets and historic neighborhoods.",
    "destination": "Lisbon",
    "budget": "1500.0",
    "start_datetime": "2026-11-12T09:00:00Z",
    "end_datetime": "2026-11-16T18:00:00Z",
    "message": "Trip created successfully"
  }
}
```

Ask a question out loud and save the spoken answer:

```bash
curl -X POST "http://localhost:8000/api/v1/multimodal/voice/chat" \
  -F "audio=@question.m4a" \
  -D headers.txt -o answer.mp3
```

Ask about a photo:

```bash
curl -X POST "http://localhost:8000/api/v1/multimodal/image/chat" \
  -F "image=@belem.jpg" \
  -F "message=Where is this? I have 2 days there next week on a tight budget."
```

```json
{
  "thread_id": "2a7f8ca3-...",
  "answer": "... Belém Tower, in Lisbon's Belém district ...",
  "tools_used": ["search_travel_knowledge", "estimate_trip_cost", "get_weather_forecast"]
}
```

---

# Setup Instructions

## Prerequisites

- Python 3.12+
- PostgreSQL 14+
- uv package manager
- ffmpeg, for the voice endpoints (`brew install ffmpeg` / `apt install ffmpeg`)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/NNesta/AI-Vacation-Planner.git
cd ai-vacation-planner
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration.

### 4. Run database migrations

```bash
uv run alembic upgrade head
```

### 5. Build the travel knowledge base

The RAG tool returns nothing until the knowledge base is ingested:

```bash
uv run python scripts/build_source_pdfs.py   # generate the sample guides
uv run python scripts/ingest.py              # chunk, embed and store in Chroma
```

### 6. Start the development server

```bash
uv run fastapi dev app/main.py
```

First start downloads the sentence-transformers embedding model (~90 MB) and
compiles both LangGraph graphs, so it takes a few seconds. Startup also launches
the MCP travel server as a subprocess; it stops with the API. The Whisper model
(~290 MB) is downloaded on the first voice request.

---

# Environment Variables

Create a `.env` file with the following variables:

```env
# --- Auth ---
secret_key=your-secret-key-here
algorithm=HS256
access_token_expires_minutes=30

# --- Database ---
database_url=postgresql+psycopg://user:password@localhost:5432/ai-vacation-db

# --- Email (welcome mail background task) ---
MAIL_USERNAME=you@example.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=you@example.com

# --- LLM / agent (phase 5) ---
ANTHROPIC_API_KEY=sk-ant-...
LLM_MODEL=claude-haiku-4-5
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=4096
AGENT_RECURSION_LIMIT=18
ITINERARY_MAX_REVISIONS=2

# --- RAG ---
EMBEDDING_MODEL=all-MiniLM-L6-v2

# --- Multimodal (phase 6) ---
STT_MODEL=openai/whisper-base
TTS_VOICE=en-US-AriaNeural
MAX_AUDIO_MB=10
MAX_IMAGE_MB=5
```

`ANTHROPIC_API_KEY` is the only credential the AI features need — the weather,
maps and pricing tools use keyless APIs, speech-to-text runs locally and the
text-to-speech voices are keyless.

---

# API Endpoints

## Authentication

| Method | Endpoint                | Description                |
| ------ | ----------------------- | -------------------------- |
| POST   | `/api/v1/auth/register` | Register a new user        |
| POST   | `/api/v1/auth/login`    | Login and get access token |
| GET    | `/api/v1/auth/me`       | Get current user info      |

---

## Trips

| Method | Endpoint                  | Description         |
| ------ | ------------------------- | ------------------- |
| POST   | `/api/v1/trips/`          | Create a new trip   |
| GET    | `/api/v1/trips/`          | Get all trips       |
| GET    | `/api/v1/trips/{trip_id}` | Get a specific trip |
| PUT    | `/api/v1/trips/{trip_id}` | Update a trip       |
| DELETE | `/api/v1/trips/{trip_id}` | Delete a trip       |

---

## Itineraries

| Method | Endpoint                                | Description                                    |
| ------ | --------------------------------------- | ---------------------------------------------- |
| POST   | `/api/v1/itineraries/`                  | Create an itinerary manually                    |
| POST   | `/api/v1/itineraries/generate/{trip_id}`| **Generate an itinerary with the AI workflow**  |
| GET    | `/api/v1/itineraries/`                  | Get all itineraries                             |
| GET    | `/api/v1/itineraries/{trip_id}`         | Get one trip's itinerary                        |
| POST   | `/api/v1/itineraries/ask`               | Phase 4 RAG Q&A (superseded by `/agent/chat`)   |

---

## AI Agent (phase 5)

| Method | Endpoint              | Description                                      |
| ------ | --------------------- | ------------------------------------------------ |
| POST   | `/api/v1/agent/chat`  | Ask the tool-using agent; returns `tools_used`    |

---

## Multimodal (phase 6)

| Method | Endpoint                             | Description                                        |
| ------ | ------------------------------------ | -------------------------------------------------- |
| POST   | `/api/v1/multimodal/voice/trips`     | Create a trip from a voice recording (auth)        |
| POST   | `/api/v1/multimodal/voice/chat`      | Spoken question in, spoken MP3 answer out          |
| POST   | `/api/v1/multimodal/image/chat`      | Ask the agent about a photo                        |

---

## Users

| Method | Endpoint         | Description   |
| ------ | ---------------- | ------------- |
| GET    | `/api/v1/users/` | Get all users |

---

# API Documentation

Once the server is running, visit:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

# Example Usage

## Register a User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "firstname": "John",
    "lastname": "Doe",
    "password": "securepassword123"
  }'
```

---

## Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john@example.com&password=securepassword123"
```

---

## Create a Trip

```bash
curl -X POST "http://localhost:8000/api/v1/trips/" \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Paris in autumn",
    "description": "Museums, food and a lot of walking",
    "destination": "Paris, France",
    "start_datetime": "2026-10-12T09:00:00Z",
    "end_datetime": "2026-10-16T18:00:00Z",
    "budget": 2000.00,
    "trip_style": "BUDGET"
  }'
```

---

## Create an Itinerary

```bash
curl -X POST "http://localhost:8000/api/v1/itineraries/" \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "trip_id": "<trip-uuid>",
    "itineraries": [
      {
        "day": 1,
        "activities": [
          {"title": "Visit Eiffel Tower"},
          {"title": "Louvre Museum Tour"}
        ]
      }
    ]
  }'
```

---

## Generate an Itinerary with the Agent

```bash
curl -X POST "http://localhost:8000/api/v1/itineraries/generate/<trip-uuid>" \
  -H "Content-Type: application/json" \
  -d '{"user_request": "keep it weather-friendly and low cost", "save": true}'
```

```json
{
  "trip_id": "<trip-uuid>",
  "itinerary": [
    {
      "day": 1,
      "date": "2026-10-12",
      "title": "Left Bank on foot",
      "summary": "An easy first day close to the hotel.",
      "activities": [
        {
          "title": "Musee d'Orsay",
          "description": "Impressionist collection in a converted railway station.",
          "start_time": "10:00:00",
          "end_time": "13:00:00",
          "duration_minutes": 180,
          "location": {"name": "Musee d'Orsay", "address": "Esplanade Valery Giscard d'Estaing, 75007 Paris"},
          "tips": ["Book a timed slot online", "Free on the first Sunday of the month"]
        }
      ]
    }
  ],
  "tools_used": ["search_travel_knowledge", "get_weather_forecast", "find_places", "estimate_trip_cost"],
  "research": "WEATHER: ...\nPLACES: ...\nBUDGET: ...",
  "issues": [],
  "saved": true,
  "error": null
}
```

---

# Database Schema

## Users Table

- `id` (UUID, Primary Key)
- `username` (String, Unique)
- `email` (String, Unique)
- `firstname` (String)
- `lastname` (String)
- `password_hash` (String)
- `role` (Enum: ADMIN, MANAGER, USER)

---

## Trips Table

- `id` (UUID, Primary Key)
- `creator_id` (UUID, Foreign Key to users)
- `title` (String)
- `description` (String, nullable)
- `destination` (String)
- `start_datetime` (Timestamptz)
- `end_datetime` (Timestamptz)
- `budget` (Float, nullable)
- `trip_style` (Enum: BUDGET)

Trip length is derived from the dates — there is no `days` column.

---

## Itineraries Table

- `id` (UUID, Primary Key)
- `trip_id` (UUID, Foreign Key to trips)
- `day` (Integer)
- `details` (JSONB, nullable) — the full structured day produced by the AI
  workflow: date, title, summary, and per-activity times, location and tips.
  Added in phase 5 so the agent's richer output is not discarded on save.

---

## Activities Table

- `id` (UUID, Primary Key)
- `itinerary_id` (UUID, Foreign Key to itineraries)
- `title` (String)
- `description` (Text, nullable)

---

## Creating Migrations

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```
