"""Functions for extracting and updating signatures."""

import inspect
import logging
from enum import Enum
from inspect import Parameter, Signature
from typing import Any, Optional, Type, Union, get_args, get_origin

from fastapi import Query

# noinspection PyProtectedMember
from fastapi._compat import field_annotation_is_scalar, field_annotation_is_sequence
from fastapi.types import UnionType

# noinspection PyProtectedMember
from pydantic.fields import FieldInfo

from fastapi_jsonapi.common import get_relationship_info_from_field_metadata
from fastapi_jsonapi.data_typing import TypeSchema
from fastapi_jsonapi.schema_base import BaseModel

log = logging.getLogger(__name__)


def field_annotation_is_scalar_sequence(annotation: Union[Type[Any], None]) -> bool:
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:
        at_least_one_scalar_sequence = False
        for arg in get_args(annotation):
            if field_annotation_is_scalar_sequence(arg):
                at_least_one_scalar_sequence = True
                continue
            elif not field_annotation_is_scalar(arg):
                return False
        return at_least_one_scalar_sequence
    return (
        field_annotation_is_sequence(annotation)
        and all(field_annotation_is_scalar(sub_annotation) for sub_annotation in get_args(annotation))
    ) or field_annotation_is_scalar(annotation)


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
    elif not field_annotation_is_scalar_sequence(field.annotation):
        default = Query(None, alias=query_filter_name)
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


def create_dependency_params_from_pydantic_model(
    model_class: Type[TypeSchema],
) -> list[Parameter]:
    return [
        Parameter(
            name=field_name,
            kind=Parameter.POSITIONAL_OR_KEYWORD,
            annotation=field_info.annotation,
            default=field_info.default,
        )
        for field_name, field_info in model_class.model_fields.items()
    ]


def get_separated_params(sig: Signature):
    """
    Separate params, tail params, skip **kwargs

    :param sig:
    :return:
    """
    params = []
    tail_params = []

    for param in sig.parameters.values():
        if param.kind is Parameter.VAR_KEYWORD:
            # skip **kwargs for spec
            continue

        if param.kind is Parameter.KEYWORD_ONLY:
            tail_params.append(param)
        else:
            params.append(param)

    return params, tail_params
