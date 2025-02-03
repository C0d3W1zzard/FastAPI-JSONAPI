"""Functions for extracting and updating signatures."""

import inspect
import logging
from enum import Enum
from inspect import Parameter
from typing import Optional

from fastapi import Query

# noinspection PyProtectedMember
from pydantic.fields import FieldInfo

from fastapi_jsonapi.common import get_relationship_info_from_field_metadata
from fastapi_jsonapi.schema_base import BaseModel

log = logging.getLogger(__name__)


def create_filter_parameter(
    name: str,
    field: FieldInfo,
) -> Parameter:
    filter_alias = field.alias or name
    query_filter_name = f"filter[{filter_alias}]"
    if (
        inspect.isclass(field.annotation)
        and issubclass(field.annotation, Enum)
        and hasattr(field.annotation, "values")
    ):
        default = Query(None, alias=query_filter_name, enum=list(field.annotation))
        type_field = str
    else:
        default = Query(None, alias=query_filter_name)
        type_field = field.annotation

    return Parameter(
        name=name,
        kind=Parameter.POSITIONAL_OR_KEYWORD,
        annotation=Optional[type_field],
        default=default,
    )


def create_additional_query_params(schema: type[BaseModel]) -> tuple[list[Parameter], list[Parameter]]:
    filter_params: list[Parameter] = []
    include_params: list[Parameter] = []
    if not schema:
        return filter_params, include_params

    available_includes_names = []
    for name, field in schema.model_fields.items():
        if get_relationship_info_from_field_metadata(field):
            available_includes_names.append(name)
        else:
            parameter = create_filter_parameter(
                name=name,
                field=field,
            )
            filter_params.append(parameter)

    if available_includes_names:
        doc_available_includes = "\n".join([f"* `{name}`" for name in available_includes_names])
        include_param = Parameter(
            "_jsonapi_include",
            kind=Parameter.POSITIONAL_OR_KEYWORD,
            annotation=Optional[str],
            default=Query(
                ",".join(available_includes_names),
                alias="include",
                description=f"Available includes:\n {doc_available_includes}",
            ),
        )
        include_params.append(include_param)
    return filter_params, include_params
