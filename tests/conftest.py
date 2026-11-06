import os

from dotenv import load_dotenv
from sqlalchemy.engine import make_url

load_dotenv()

for name, value in {
    "secret_key": "test-secret-key-that-is-long-enough-for-hs256",
    "access_token_expires_minutes": "30",
    "database_url": "postgresql+psycopg://postgres:postgres@localhost:5432/ai_vacation",
    "MAIL_USERNAME": "test@example.com",
    "MAIL_PASSWORD": "test",
    "MAIL_FROM": "test@example.com",
    "ANTHROPIC_API_KEY": "test-key",
}.items():
    if not os.environ.get(name):
        os.environ[name] = value

_url = make_url(os.environ["database_url"])
_test_url = _url.set(database=f"{_url.database}_test")
os.environ["database_url"] = _test_url.render_as_string(hide_password=False)

import psycopg  # noqa: E402
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.agents.graph import get_agent_graph  # noqa: E402
from app.agents.itinerary_graph import get_itinerary_graph  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402


def _create_test_database() -> None:
    admin = _url.set(drivername="postgresql", database="postgres")
    with psycopg.connect(admin.render_as_string(hide_password=False), autocommit=True) as conn:
        name = _test_url.database
        if not conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone():
            conn.execute(f'CREATE DATABASE "{name}"')


@pytest_asyncio.fixture(scope="session", autouse=True)
async def schema():
    assert engine.url.database.endswith("_test")
    _create_test_database()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(schema):
    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {tables} CASCADE"))


@pytest.fixture(autouse=True)
def no_email(monkeypatch):
    async def send(*args, **kwargs):
        return None

    monkeypatch.setattr("app.services.auth.send_welcome_email", send)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


async def register_and_login(client, name: str = "alice") -> dict:
    email = f"{name}@example.com"
    password = "correct-horse-battery"
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": name,
            "email": email,
            "firstname": name.title(),
            "lastname": "Tester",
            "password": password,
        },
    )
    assert response.status_code == 201
    response = await client.post(
        "/api/v1/auth/login", data={"username": email, "password": password}
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest_asyncio.fixture
async def auth_headers(client):
    return await register_and_login(client)


def trip_payload(**overrides) -> dict:
    return {
        "title": "Paris in spring",
        "description": "Museums and food",
        "destination": "Paris, France",
        "start_datetime": "2030-05-10T09:00:00Z",
        "end_datetime": "2030-05-12T18:00:00Z",
        "budget": 2000,
        **overrides,
    }


@pytest_asyncio.fixture
async def trip(client, auth_headers):
    response = await client.post("/api/v1/trips/", json=trip_payload(), headers=auth_headers)
    assert response.status_code == 201
    return response.json()


class FakeChatModel:
    """Replays scripted responses in place of Claude and records each prompt."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def bind_tools(self, tools):
        return self

    def with_structured_output(self, schema):
        return self

    async def ainvoke(self, messages, *args, **kwargs):
        self.calls.append(messages)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


@pytest.fixture
def fake_llm(monkeypatch):
    def install(*responses) -> FakeChatModel:
        model = FakeChatModel(responses)
        for target in (
            "app.agents.graph.get_chat_model",
            "app.agents.itinerary_graph.get_chat_model",
            "app.services.multimodal.get_chat_model",
        ):
            monkeypatch.setattr(target, lambda *args, **kwargs: model)
        get_agent_graph.cache_clear()
        get_itinerary_graph.cache_clear()
        return model

    yield install
    get_agent_graph.cache_clear()
    get_itinerary_graph.cache_clear()
