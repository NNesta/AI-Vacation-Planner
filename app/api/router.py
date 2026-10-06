from fastapi import APIRouter

from .v1 import agent_router, auth_router, itinerary_router, trip_router, user_router

api_router_v1 = APIRouter(prefix="/api/v1")


api_router_v1.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router_v1.include_router(trip_router, prefix="/trips", tags=["Trip"])
api_router_v1.include_router(user_router, prefix="/users", tags=["User"])
api_router_v1.include_router(itinerary_router, prefix="/itineraries", tags=["Itinerary"])
api_router_v1.include_router(agent_router, prefix="/agent", tags=["AI Agent"])
