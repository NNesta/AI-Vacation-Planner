import uuid
from sqlalchemy import UUID, String
from sqlalchemy.orm import Mapped, mapped_column
from ..db.base import Base


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
