from sqlalchemy.orm import Mapped, relationship

from .base import Base
from .parent_to_child_association import ParentToChildAssociation


class Child(Base):
    __tablename__ = "right_table_children"

    name: Mapped[str]

    parents: Mapped[list[ParentToChildAssociation]] = relationship(back_populates="child", cascade="delete")
