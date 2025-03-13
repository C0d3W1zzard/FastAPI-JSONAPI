from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship

from examples.api_for_sqlalchemy.enums.enums import EnumColumn
from examples.api_for_sqlalchemy.enums.user import UserStatusEnum

from .base import Base
from .computer import Computer
from .post import Post
from .post_comment import PostComment
from .user_bio import UserBio
from .workplace import Workplace


class User(Base):
    __tablename__ = "users"

    age: Mapped[Optional[int]]
    email: Mapped[Optional[str]]
    name: Mapped[Optional[str]] = mapped_column(unique=True)
    status: Mapped[UserStatusEnum] = mapped_column(
        EnumColumn(UserStatusEnum),
        default=UserStatusEnum.active,
    )

    bio: Mapped[UserBio] = relationship(back_populates="user", cascade="delete")
    comments: Mapped[list[PostComment]] = relationship(back_populates="user", cascade="delete")
    computers: Mapped[list[Computer]] = relationship(back_populates="user")
    posts: Mapped[list[Post]] = relationship(back_populates="user", cascade="delete")
    workplace: Mapped[Workplace] = relationship(back_populates="user")

    class Enum:
        Status = UserStatusEnum
