from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Optional

from pydantic import ConfigDict

from fastapi_jsonapi.schema_base import BaseModel
from fastapi_jsonapi.types_metadata import RelationshipInfo

if TYPE_CHECKING:
    from .child import ChildSchema
    from .parent import ParentSchema


class ParentToChildAssociationAttributesSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    extra_data: str


class ParentToChildAssociationSchema(ParentToChildAssociationAttributesSchema):
    parent: Annotated[
        Optional[ParentSchema],
        RelationshipInfo(
            resource_type="parent",
        ),
    ] = None
    child: Annotated[
        Optional[ChildSchema],
        RelationshipInfo(
            resource_type="child",
        ),
    ] = None
