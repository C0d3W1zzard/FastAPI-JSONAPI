from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .post import Post
    from .user import User


class PostComment(Base):
    __tablename__ = "post_comments"

    text: Mapped[str] = mapped_column(default="", server_default="")

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=False)
    user: Mapped[User] = relationship(back_populates="comments")
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), unique=False)
    post: Mapped[Post] = relationship(back_populates="comments")
