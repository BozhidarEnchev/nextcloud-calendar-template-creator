from datetime import datetime, timezone, time
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EventTemplateItem(Base):
    __tablename__ = "event_template_item"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    title: Mapped[str] = mapped_column(
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )
    location: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )
    start_time: Mapped[time] = mapped_column(
        nullable=False,
    )
    end_time: Mapped[time] = mapped_column(
        nullable=False,
    )
    calendar_url: Mapped[str] = mapped_column(
        nullable=False,
    )
    template_id: Mapped[int] = mapped_column(
        ForeignKey("event_template.id"),
        nullable=False,
    )
    template: Mapped["EventTemplate"] = relationship(
        back_populates="items",
    )

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
