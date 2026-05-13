from sqlalchemy import Column, ForeignKey, Table, column

from app.db.base import Base


user_trip_associations = Table(
    "user_trips",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("trip_id", ForeignKey("trips.id"), primary_key=True),
)
