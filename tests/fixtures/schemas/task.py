from __future__ import annotations

from typing import Annotated, Optional

from pydantic import ConfigDict, field_validator

from fastapi_jsonapi.schema_base import BaseModel
from fastapi_jsonapi.types_metadata.custom_filter_sql import (
    sql_filter_pg_json_contains,
    sql_filter_pg_json_ilike,
    sql_filter_pg_jsonb_contains,
    sql_filter_pg_jsonb_ilike,
    sql_filter_sqlite_json_contains,
    sql_filter_sqlite_json_ilike,
)
from tests.common import is_postgres_tests


class TaskBaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    if is_postgres_tests():
        task_ids_dict_json: Annotated[Optional[dict], sql_filter_pg_json_ilike]
        task_ids_list_json: Annotated[Optional[list], sql_filter_pg_json_contains]
    else:
        task_ids_dict_json: Annotated[Optional[dict], sql_filter_sqlite_json_ilike]
        task_ids_list_json: Annotated[Optional[list], sql_filter_sqlite_json_contains]

    # noinspection PyMethodParameters
    @field_validator("task_ids_dict_json", mode="before", check_fields=False)
    @classmethod
    def task_ids_dict_json_validator(cls, value: Optional[dict]):
        """
        return `{}`, if value is None both on get and on create
        """
        return value or {}

    # noinspection PyMethodParameters
    @field_validator("task_ids_list_json", mode="before", check_fields=False)
    @classmethod
    def task_ids_list_json_validator(cls, value: Optional[list]):
        """
        return `[]`, if value is None both on get and on create
        """
        return value or []

    if is_postgres_tests():
        task_ids_dict_jsonb: Annotated[Optional[dict], sql_filter_pg_jsonb_ilike]
        task_ids_list_jsonb: Annotated[Optional[list], sql_filter_pg_jsonb_contains]

        # noinspection PyMethodParameters
        @field_validator("task_ids_dict_jsonb", mode="before", check_fields=False)
        @classmethod
        def task_ids_dict_jsonb_validator(cls, value: Optional[dict]):
            """
            return `{}`, if value is None both on get and on create
            """
            return value or {}

        # noinspection PyMethodParameters
        @field_validator("task_ids_list_jsonb", mode="before", check_fields=False)
        @classmethod
        def task_ids_list_jsonb_validator(cls, value: Optional[list]):
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
