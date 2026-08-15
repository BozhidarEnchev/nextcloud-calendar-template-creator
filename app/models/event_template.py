from datetime import datetime, timezone
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class EventTemplate(Base):
    __tablename__ = "event_template"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"),
        nullable=False,
    )
    items: Mapped[list["EventTemplateItem"]] = relationship(
        back_populates="template",
    )
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
