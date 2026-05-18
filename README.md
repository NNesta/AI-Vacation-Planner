# AI Vacation Planner

An intelligent travel planning application that helps users create, manage, and organize vacation trips with AI-generated itineraries.

---

# Features

- User Authentication: JWT-based authentication with secure password hashing
- Trip Management: Create, read, update, and delete travel trips
- Itinerary Planning: Generate day-by-day itineraries with activities
- User Roles: Admin, Manager, and User role-based access
- Database: PostgreSQL with async SQLAlchemy ORM
- API Documentation: Auto-generated OpenAPI/Swagger docs

---

# Tech Stack

- **Framework:** FastAPI 0.136+
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
│   │   │   ├── itineraries.py # Itinerary endpoints
│   │   │   └── users.py     # User endpoints
│   │   └── router.py        # Main router configuration
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
│   │   ├── itinerary_day.py # Itinerary day model
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

## 4. Database Models

## 5. Database Models

The application uses SQLAlchemy 2.0 with async support:

## 5. API Endpoints

## 6. API Endpoints

The API is organized with versioning:

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
alembic upgrade head
```

### 5. Start the development server

```bash
uv run uvicorn app.main:app --reload
```

---

# Environment Variables

Create a `.env` file with the following variables:

```env
secret_key=your-secret-key-here
algorithm=ALGORITHM
access_token_expires_minutes=integer

database_url=postgresql+psycopg://user:password@localhost:5432/ai-vacation-db
```

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

| Method | Endpoint               | Description         |
| ------ | ---------------------- | ------------------- |
| POST   | `/api/v1/itineraries/` | Create an itinerary |
| GET    | `/api/v1/itineraries/` | Get all itineraries |

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
    "destination": "Paris, France",
    "days": 5,
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
    "itinerary_days": [
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
- `destination` (String)
- `days` (Integer)
- `budget` (Float)
- `trip_style` (Enum: BUDGET)

---

## Itinerary Days Table

- `id` (UUID, Primary Key)
- `trip_id` (UUID, Foreign Key to trips)
- `day_number` (Integer)

---

## Activities Table

- `id` (UUID, Primary Key)
- `itinerary_day_id` (UUID, Foreign Key to itinerary_days)
- `title` (String)

---

## Creating Migrations

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```
