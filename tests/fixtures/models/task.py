from typing import Optional

from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from examples.api_for_sqlalchemy.models.base import Base


class Task(Base):
    __tablename__ = "tasks"

    task_ids: Mapped[Optional[list]] = mapped_column(JSON, unique=False)
