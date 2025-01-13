from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Annotated,
    Optional,
)

from pydantic import ConfigDict

from fastapi_jsonapi.schema_base import BaseModel
from fastapi_jsonapi.types_metadata import RelationshipInfo

if TYPE_CHECKING:
    from .parent_to_child import ParentToChildAssociationSchema


class ParentAttributesSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    name: str


class ParentBaseSchema(ParentAttributesSchema):
    """Parent base schema."""

    children: Annotated[
        Optional[list[ParentToChildAssociationSchema]],
        RelationshipInfo(
            resource_type="parent_child_association",
            many=True,
        ),
    ] = None


class ParentPatchSchema(ParentBaseSchema):
    """Parent PATCH schema."""


class ParentInSchema(ParentBaseSchema):
    """Parent input schema."""


class ParentSchema(ParentInSchema):
    """Parent item schema."""

    id: int
