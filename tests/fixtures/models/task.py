from typing import Optional

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from examples.api_for_sqlalchemy.models.base import Base
from tests.common import is_postgres_tests


class Task(Base):
    __tablename__ = "tasks"

    task_ids_dict_json: Mapped[Optional[dict]] = mapped_column(JSON, unique=False)
    task_ids_list_json: Mapped[Optional[list]] = mapped_column(JSON, unique=False)

    if is_postgres_tests():
        task_ids_dict_jsonb: Mapped[Optional[dict]] = mapped_column(JSONB, unique=False)
        task_ids_list_jsonb: Mapped[Optional[list]] = mapped_column(JSONB, unique=False)
