from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from examples.api_for_sqlalchemy.models.base import Base


class User(Base):
    __tablename__ = "users"

    name: Mapped[str]

    bio: Mapped[UserBio] = relationship(back_populates="user")
    computers: Mapped[list[Computer]] = relationship(back_populates="user")


class Computer(Base):
    __tablename__ = "computers"

    name: Mapped[str]

    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    user: Mapped[User] = relationship(back_populates="computers")


class UserBio(Base):
    __tablename__ = "user_bio"

    birth_city: Mapped[str] = mapped_column(default="", server_default="")
    favourite_movies: Mapped[str] = mapped_column(default="", server_default="")

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    user: Mapped[User] = relationship(back_populates="bio")
