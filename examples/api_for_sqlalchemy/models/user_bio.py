from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User


class UserBio(Base):
    __tablename__ = "user_bio"

    birth_city: Mapped[str] = mapped_column(default="", server_default="")
    favourite_movies: Mapped[str] = mapped_column(default="", server_default="")

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    user: Mapped[User] = relationship(back_populates="bio")
