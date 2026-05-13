from fastapi import APIRouter
from .v1 import auth_router, trip_router, user_router

api_router_v1 = APIRouter(prefix="/api/v1")


api_router_v1.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
api_router_v1.include_router(trip_router, prefix="/api/trips", tags=["Trip"])
api_router_v1.include_router(user_router, prefix="/api/users", tags=["User"])
