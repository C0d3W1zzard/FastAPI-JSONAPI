"""
Base JSON:API schemas.

Pydantic (for FastAPI).
"""

from __future__ import annotations

from inspect import isclass
from types import GenericAlias
from typing import TYPE_CHECKING, Optional, Sequence, Type, Union, get_args

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

# noinspection PyProtectedMember
from pydantic._internal._typing_extra import is_none_type

# noinspection PyProtectedMember
from pydantic.fields import FieldInfo

from fastapi_jsonapi.common import search_relationship_info

if TYPE_CHECKING:
    from fastapi_jsonapi.data_typing import TypeSchema


class BaseJSONAPIRelationshipSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    id: str = Field(default=..., description="Related object ID")
    type: str = Field(default=..., description="Type of the related resource object")


class BaseJSONAPIRelationshipDataToOneSchema(BaseModel):
    data: BaseJSONAPIRelationshipSchema


class BaseJSONAPIRelationshipDataToManySchema(BaseModel):
    data: list[BaseJSONAPIRelationshipSchema]


class BaseJSONAPIItemSchema(BaseModel):
    """Base JSON:API item schema."""

    type: str = Field(description="Resource type")
    attributes: dict = Field(description="Resource object attributes")


class BaseJSONAPIItemInSchema(BaseJSONAPIItemSchema):
    """
    Schema for post/patch method

    TODO POST: optionally accept custom id for object https://jsonapi.org/format/#crud-creating-client-ids
    TODO PATCH: accept object id (maybe create a new separate schema)
    """

    attributes: TypeSchema = Field(description="Resource object attributes")
    relationships: Optional[TypeSchema] = Field(default=None, description="Resource object relationships")
    id: Optional[str] = Field(description="Resource object ID")


class BaseJSONAPIDataInSchema(BaseModel):
    data: BaseJSONAPIItemInSchema


class BaseJSONAPIObjectSchema(BaseJSONAPIItemSchema):
    """Base JSON:API object schema."""

    id: str = Field(description="Resource object ID")


class JSONAPIResultListMetaSchema(BaseModel):
    """JSON:API list meta schema."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    count: Optional[int]
    total_pages: Optional[int] = Field(alias="totalPages")


class JSONAPIDocumentObjectSchema(BaseModel):
    """
    JSON:API Document Object Schema.

    https://jsonapi.org/format/#document-jsonapi-object
    """

    version: str = Field(default="1.0", description="json-api версия")


class JSONAPIObjectSchema(BaseJSONAPIObjectSchema):
    """JSON:API base object schema."""

    model_config = ConfigDict(
        from_attributes=True,
    )


class BaseJSONAPIResultSchema(BaseModel):
    """
    JSON:API Required fields schema
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    meta: Optional[JSONAPIResultListMetaSchema] = Field(default=None, description="JSON:API metadata")
    jsonapi: JSONAPIDocumentObjectSchema = JSONAPIDocumentObjectSchema()


class JSONAPIResultListSchema(BaseJSONAPIResultSchema):
    """JSON:API list base result schema."""

    data: Sequence[JSONAPIObjectSchema] = Field(description="Resource objects collection")


class JSONAPIResultDetailSchema(BaseJSONAPIResultSchema):
    """JSON:API base detail schema."""

    data: JSONAPIObjectSchema = Field(description="Resource object data")


RelationshipInfoSchema = Union[
    Type[BaseJSONAPIRelationshipDataToOneSchema],
    Type[BaseJSONAPIRelationshipDataToManySchema],
]


class JSONAPISchemaIntrospectionError(Exception):
    pass


def get_model_field(schema: Type["TypeSchema"], field: str) -> str:
    """
    Get the model field of a schema field.

    # todo: use alias (custom names)?
       For example:

    class Computer(sqla_base):
        user = relationship(User)

    class ComputerSchema(pydantic_base):
        owner = Field(alias="user", relationship=...)

    :param schema: a pydantic schema
    :param field: the name of the schema field
    :return: the name of the field in the model
    :raises Exception: if the schema from parameter has no attribute for parameter.
    """
    if schema.model_fields.get(field) is None:
        msg = f"{schema.__name__} has no attribute {field}"
        raise JSONAPISchemaIntrospectionError(msg)
    return field


def get_relationship_fields_names(schema: Type["TypeSchema"]) -> set[str]:
    """
    Return relationship fields of a schema.

    :param schema: a schemas schema
    """
    names: set[str] = set()
    for i_name, i_type in schema.model_fields.items():
        if search_relationship_info.first(i_type):
            names.add(i_name)
    return names


def get_schema_from_type(resource_type: str, app: FastAPI) -> Type[BaseModel]:
    """
    Retrieve a schema from the registry by his type.

    :param resource_type: the type of the resource.
    :param app: FastAPI app instance.
    :return Schema: the schema class.
    :raises Exception: if the schema not found for this resource type.
    """
    schemas: dict[str, Type[BaseModel]] = getattr(app, "schemas", {})
    try:
        return schemas[resource_type]
    except KeyError:
        msg = f"Couldn't find schema for type: {resource_type}"
        raise Exception(msg)


def get_schema_from_field_annotation(field: FieldInfo) -> Optional[Type[TypeSchema]]:
    annotation_ = field.annotation

    if isclass(annotation_) and issubclass(annotation_, BaseModel):
        return annotation_

    choices = list(get_args(field.annotation))
    while choices:
        elem = choices.pop(0)
        if isinstance(elem, GenericAlias):
            choices.extend(get_args(elem))
            continue

        if is_none_type(elem):
            continue

        if isclass(elem) and issubclass(elem, BaseModel):
            return elem

    return None


def get_related_schema(schema: Type[TypeSchema], field: str) -> Type[TypeSchema]:
    """
    Retrieve the related schema of a relationship field.

    :params schema: the schema to retrieve le relationship field from
    :params field: the relationship field
    :return: the related schema
    """
    return get_schema_from_field_annotation(schema.model_fields[field])
