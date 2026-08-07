from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(
        primary_key=True
    )
    username: Mapped[str] = mapped_column(
        nullable=False,
        unique=True
    )
    hashed_password: Mapped[str] = mapped_column(
        nullable=False
    )
    full_name: Mapped[str] = mapped_column(
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
