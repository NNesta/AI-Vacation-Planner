# AI Vacation Planner

An intelligent travel planning application that helps users create, manage, and organize vacation trips with AI-generated itineraries.

---

# Features

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
│   │   │   └── users.py     # User endpoints
│   │   └── router.py        # Main router configuration
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
│   │   └── user/            # User schemas
│   ├── services/            # Business logic
│   │   ├── auth.py          # Authentication service
│   │   ├── trip.py          # Trip service
│   │   ├── itinerary.py     # Itinerary service
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

# Setup Instructions

## Prerequisites

- Python 3.12+
- PostgreSQL 14+
- uv package manager

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
compiles both LangGraph graphs, so it takes a few seconds.

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
```

`ANTHROPIC_API_KEY` is the only credential the AI features need — the weather,
maps and pricing tools use keyless APIs.

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
