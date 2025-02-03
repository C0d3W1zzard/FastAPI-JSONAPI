from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship

from examples.api_for_sqlalchemy.models.base import Base


class CascadeCase(Base):
    __tablename__ = "cascade_case"

    parent_item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(
            "cascade_case.id",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
    )
    sub_items: Mapped[list[CascadeCase]] = relationship(
        backref=backref("parent_item", remote_side="CascadeCase.id"),
    )

    if TYPE_CHECKING:
        parent_item: Mapped[CascadeCase]
