from typing import List, TYPE_CHECKING
import uuid
from sqlalchemy import UUID, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.db.base import Base
from app.models.trip import Trip


if TYPE_CHECKING:
    from app.models.activity import Activity


class Itinerary(Base):
    __tablename__ = "itineraries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4()
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trips.id"), nullable=False
    )
    day: Mapped[int]
    activities: Mapped[List["Activity"]] = relationship(
        "Activity",
        back_populates="itinerary",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    trip: Mapped[Trip] = relationship("Trip", back_populates="itineraries")
