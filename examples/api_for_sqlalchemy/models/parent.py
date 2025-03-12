from sqlalchemy.orm import Mapped, relationship

from .base import Base
from .parent_to_child_association import ParentToChildAssociation


class Parent(Base):
    __tablename__ = "left_table_parents"

    name: Mapped[str]

    children: Mapped[list[ParentToChildAssociation]] = relationship(back_populates="parent", cascade="delete")
