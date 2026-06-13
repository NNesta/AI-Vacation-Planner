import uuid
from sqlalchemy import UUID, String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base
from typing import List, TYPE_CHECKING
import enum

if TYPE_CHECKING:
    from .trip import Trip
    from .user_trips import UserTrip


class Role(enum.Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    USER = "USER"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(
        String(150), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(150), unique=True, index=True, nullable=False
    )
    firstname: Mapped[str] = mapped_column(String(150), nullable=True)
    lastname: Mapped[str] = mapped_column(String(150), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[str] = mapped_column(Enum(Role, name="role_enum"), default=Role.USER)
    created_trips: Mapped[List["Trip"]] = relationship(
        "Trip", back_populates="creator", cascade="all, delete-orphan"
    )
    user_trips = relationship("UserTrip", back_populates="user")
