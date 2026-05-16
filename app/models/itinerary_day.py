from typing import List, TYPE_CHECKING
import uuid
from sqlalchemy import UUID, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.db.base import Base
from app.models.trip import Trip


if TYPE_CHECKING:
    from app.models.activity import Activity


class ItineraryDay(Base):
    __tablename__ = "itinerary_days"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4()
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trips.id"), nullable=False
    )
    day_number: Mapped[int]
    activities: Mapped[List["Activity"]] = relationship(
        "Activity", back_populates="itinerary_day", cascade="all, delete-orphan"
    )
    trip: Mapped[Trip] = relationship("Trip", back_populates="itinerary_days")
