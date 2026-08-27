from fastapi import FastAPI
from app.api.router import api_router_v1
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.utils.vector_store import get_collection, load_embedding_function

origins = ["*"]

@asynccontextmanager
async def lifespan(app: FastAPI):
    embedding_fn = load_embedding_function()
    get_collection(embedding_fn)

    yield

app = FastAPI(title="AI Vacation Planner API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=[],
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
app.include_router(api_router_v1)
