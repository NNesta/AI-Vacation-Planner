from fastapi import FastAPI
from app.api.router import api_router_v1
from fastapi.middleware.cors import CORSMiddleware

origins = ["*"]
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=[],
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
app.include_router(api_router_v1)
