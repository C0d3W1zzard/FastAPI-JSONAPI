from __future__ import annotations

from typing import Optional, Annotated

from pydantic import BaseModel
from pydantic import ConfigDict

from fastapi_jsonapi.types_metadata import RelationshipInfo


class UserBaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    name: str

    bio: Annotated[
        Optional[UserBioBaseSchema],
        RelationshipInfo(
            resource_type="user_bio",
        ),
    ] = None
    computers: Annotated[
        Optional[list[ComputerBaseSchema]],
        RelationshipInfo(
            resource_type="computer",
            many=True,
        ),
    ] = None


class UserSchema(BaseModel):
    id: int
    name: str


class UserBioBaseSchema(BaseModel):
    birth_city: str
    favourite_movies: str

    user: Annotated[
        Optional[UserSchema],
        RelationshipInfo(
            resource_type="user",
        ),
    ] = None


class ComputerBaseSchema(BaseModel):
    id: int
    name: str

    user: Annotated[
        Optional[UserSchema],
        RelationshipInfo(
            resource_type="user",
        ),
    ] = None
