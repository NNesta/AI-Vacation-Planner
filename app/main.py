from fastapi import FastAPI
from app.api.router import api_router_v1


app = FastAPI()

app.include_router(api_router_v1)
