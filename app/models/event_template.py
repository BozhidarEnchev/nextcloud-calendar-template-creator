from datetime import datetime, timezone
from typing import List
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
        ForeignKey("user.id", ondelete="cascade"),
        nullable=False,
    )
    items: Mapped[List["EventTemplateItem"]] = relationship(
        back_populates="template",
        passive_deletes=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
