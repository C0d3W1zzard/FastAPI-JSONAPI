from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Optional

from pydantic import ConfigDict

from fastapi_jsonapi.schema_base import BaseModel
from fastapi_jsonapi.types_metadata import RelationshipInfo

if TYPE_CHECKING:
    from .user import UserSchema


class WorkplaceBaseSchema(BaseModel):
    """Workplace base schema."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    name: str

    user: Annotated[
        Optional[UserSchema],
        RelationshipInfo(
            resource_type="user",
        ),
    ] = None


class WorkplacePatchSchema(WorkplaceBaseSchema):
    """Workplace PATCH schema."""


class WorkplaceInSchema(WorkplaceBaseSchema):
    """Workplace input schema."""


class WorkplaceSchema(WorkplaceInSchema):
    """Workplace item schema."""

    id: int
