from __future__ import annotations
from datetime import datetime
import uuid
from sqlalchemy import UUID, DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base
import enum


class TripStyle(enum.Enum):
    BUDGET = "BUDGET"


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=True)
    destination: Mapped[str] = mapped_column(String(120), nullable=False)
    start_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    budget: Mapped[float] = mapped_column(Float, nullable=True)
    trip_style: Mapped[TripStyle] = mapped_column(
        Enum(TripStyle, name="trip_style_enum"), default=TripStyle.BUDGET
    )

    creator = relationship("User", back_populates="created_trips")
    itinerary_days = relationship(
        "ItineraryDay",
        back_populates="trip",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    user_trips = relationship("UserTrip", back_populates="trip")
