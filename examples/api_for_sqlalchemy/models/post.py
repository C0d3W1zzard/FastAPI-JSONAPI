from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .post_comment import PostComment

if TYPE_CHECKING:
    from .user import User


class Post(Base):
    __tablename__ = "posts"

    body: Mapped[str] = mapped_column(default="", server_default="")
    title: Mapped[str]

    comments: Mapped[list[PostComment]] = relationship(back_populates="post", cascade="delete")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped[User] = relationship(back_populates="posts")
