from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Optional

from pydantic import ConfigDict

from fastapi_jsonapi.schema_base import BaseModel
from fastapi_jsonapi.types_metadata import RelationshipInfo

from .post_comment import PostCommentSchema

if TYPE_CHECKING:
    from .user import UserSchema


class PostAttributesBaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    body: str
    title: str


class PostBaseSchema(PostAttributesBaseSchema):
    """Post base schema."""

    user: Annotated[
        Optional[UserSchema],
        RelationshipInfo(
            resource_type="user",
        ),
    ] = None
    comments: Annotated[
        Optional[list[PostCommentSchema]],
        RelationshipInfo(
            resource_type="post_comment",
            many=True,
        ),
    ] = None


class PostPatchSchema(PostBaseSchema):
    """Post PATCH schema."""


class PostInSchema(PostBaseSchema):
    """Post input schema."""


class PostSchema(PostInSchema):
    """Post item schema."""

    id: int
