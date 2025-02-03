from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Optional

from pydantic import ConfigDict

from fastapi_jsonapi.schema_base import BaseModel
from fastapi_jsonapi.types_metadata import RelationshipInfo

if TYPE_CHECKING:
    from .user import UserSchema


class ComputerAttributesBaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    name: str


class ComputerBaseSchema(ComputerAttributesBaseSchema):
    """Computer base schema."""

    user: Annotated[
        Optional[UserSchema],
        RelationshipInfo(
            resource_type="user",
        ),
    ] = None


class ComputerPatchSchema(ComputerBaseSchema):
    """Computer PATCH schema."""


class ComputerInSchema(ComputerBaseSchema):
    """Computer input schema."""


class ComputerSchema(ComputerInSchema):
    """Computer item schema."""

    id: int
