from __future__ import annotations

from typing import Annotated, Optional

from fastapi_jsonapi.schema_base import BaseModel
from fastapi_jsonapi.types_metadata import RelationshipInfo


class SelfRelationshipAttributesSchema(BaseModel):
    name: str

    parent_object: Annotated[
        Optional[SelfRelationshipAttributesSchema],
        RelationshipInfo(
            resource_type="self_relationship",
        ),
    ] = None
    children_objects: Annotated[
        Optional[list[SelfRelationshipAttributesSchema]],
        RelationshipInfo(
            resource_type="self_relationship",
            many=True,
        ),
    ] = None
