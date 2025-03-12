from typing import Annotated, Optional

from pydantic import ConfigDict

from fastapi_jsonapi.schema_base import BaseModel
from fastapi_jsonapi.types_metadata import RelationshipInfo

from .parent_to_child_association import ParentToChildAssociationSchema


class ChildAttributesSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    name: str


class ChildBaseSchema(ChildAttributesSchema):
    """Child base schema."""

    parents: Annotated[
        Optional[list[ParentToChildAssociationSchema]],
        RelationshipInfo(
            resource_type="parent_child_association",
            many=True,
        ),
    ] = None


class ChildPatchSchema(ChildBaseSchema):
    """Child PATCH schema."""


class ChildInSchema(ChildBaseSchema):
    """Child input schema."""


class ChildSchema(ChildInSchema):
    """Child item schema."""

    id: int
