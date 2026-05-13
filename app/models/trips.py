import uuid
from sqlalchemy import UUID, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .user_trips import user_trip_associations
from .users import User

from ..db.base import Base
import enum
from typing import List


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
    destination: Mapped[str] = mapped_column(String(120), nullable=False)
    days: Mapped[int] = mapped_column(Integer, nullable=True)
    budget: Mapped[float] = mapped_column(Float, nullable=True)
    trip_style: Mapped[TripStyle] = mapped_column(
        Enum(TripStyle, name="trip_style_enum"), default=TripStyle.BUDGET
    )

    users: Mapped[List[User]] = relationship(
        "User", secondary=user_trip_associations, back_populates="trips"
    )
    creator: Mapped[User] = relationship("User", back_populates="created_trips")
