import uuid
from sqlalchemy import UUID, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.itinerary import Itinerary


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    itinerary_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("itineraries.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    itinerary: Mapped[Itinerary] = relationship(
        "Itinerary", back_populates="activities"
    )
