from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Optional

from pydantic import ConfigDict

from fastapi_jsonapi.schema_base import BaseModel
from fastapi_jsonapi.types_metadata import RelationshipInfo

if TYPE_CHECKING:
    from .user import UserSchema


class UserBioAttributesBaseSchema(BaseModel):
    """UserBio base schema."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    birth_city: str
    favourite_movies: str


class UserBioBaseSchema(UserBioAttributesBaseSchema):
    """UserBio item schema."""

    user: Annotated[
        Optional[UserSchema],
        RelationshipInfo(
            resource_type="user",
        ),
    ] = None


class UserBioPatchSchema(UserBioBaseSchema):
    """UserBio PATCH schema."""


class UserBioInSchema(UserBioBaseSchema):
    """UserBio input schema."""


class UserBioSchema(UserBioInSchema):
    """UserBio item schema."""

    id: int
