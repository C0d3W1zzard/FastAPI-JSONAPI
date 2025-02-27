from __future__ import annotations

from typing import Optional

from pydantic import ConfigDict, field_validator

from fastapi_jsonapi.schema_base import BaseModel


class TaskBaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    task_ids_dict: Optional[dict[str, list]] = None
    task_ids_list: Optional[list] = None

    # noinspection PyMethodParameters
    @field_validator("task_ids_dict", mode="before", check_fields=False)
    @classmethod
    def task_ids_dict_validator(cls, value: Optional[dict[str, list]]):
        """
        return `{}`, if value is None both on get and on create
        """
        return value or {}

    # noinspection PyMethodParameters
    @field_validator("task_ids_list", mode="before", check_fields=False)
    @classmethod
    def task_ids_list_validator(cls, value: Optional[list]):
        """
        return `[]`, if value is None both on get and on create
        """
        return value or []


class TaskPatchSchema(TaskBaseSchema):
    """Task PATCH schema."""


class TaskInSchema(TaskBaseSchema):
    """Task create schema."""


class TaskSchema(TaskBaseSchema):
    """Task item schema."""

    id: int
