from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from pydantic import ConfigDict

from fastapi_jsonapi.schema_base import BaseModel
from fastapi_jsonapi.types_metadata import RelationshipInfo

if TYPE_CHECKING:
    from .post import PostSchema
    from .user import UserSchema


class PostCommentAttributesBaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    text: str


class PostCommentBaseSchema(PostCommentAttributesBaseSchema):
    """PostComment base schema."""

    post: Annotated[
        PostSchema,
        RelationshipInfo(
            resource_type="post",
        ),
    ]
    user: Annotated[
        UserSchema,
        RelationshipInfo(
            resource_type="user",
        ),
    ]


class PostCommentSchema(PostCommentBaseSchema):
    """PostComment item schema."""

    id: int
