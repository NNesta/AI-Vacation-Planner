import enum
import uuid
from sqlalchemy import UUID, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.trip import Trip
from app.models.user import User


# user_trip_associations = Table(
#     "user_trips",
#     Base.metadata,
#     Column("user_id", ForeignKey("users.id"), primary_key=True),
#     Column("trip_id", ForeignKey("trips.id"), primary_key=True),
# )


class StatusEnum(enum.Enum):
    PENDING = "PENDING"
    REJECTED = "REJECTED"
    APPROVED = "APPROVED"


class UserTrip(Base):
    __tablename__ = "user_trips"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4(), nullable=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trips.id"), nullable=False
    )

    status: Mapped[enum.Enum] = mapped_column(
        Enum(StatusEnum, name="status_enum"), default=StatusEnum.PENDING, nullable=True
    )

    user: Mapped[User] = relationship(back_populates="user_trips")
    trip: Mapped[Trip] = relationship(back_populates="user_users")
