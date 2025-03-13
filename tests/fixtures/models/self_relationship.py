from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship

from examples.api_for_sqlalchemy.models.base import Base


class SelfRelationship(Base):
    __tablename__ = "selfrelationships"

    name: Mapped[str] = mapped_column(String)

    self_relationship_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(
            "selfrelationships.id",
            name="fk_self_relationship_id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
    )
    children_objects: Mapped[list[SelfRelationship]] = relationship(
        backref=backref("parent_object", remote_side="SelfRelationship.id"),
    )

    if TYPE_CHECKING:
        parent_object: Mapped[SelfRelationship]
