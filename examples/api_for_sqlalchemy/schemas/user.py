from typing import Annotated, Optional

from pydantic import ConfigDict

from fastapi_jsonapi.schema_base import BaseModel
from fastapi_jsonapi.types_metadata import ClientCanSetId, RelationshipInfo

from .computer import ComputerSchema
from .post import PostSchema
from .post_comment import PostCommentSchema
from .user_bio import UserBioBaseSchema
from .workplace import WorkplaceSchema


class UserAttributesBaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    name: str

    age: Optional[int] = None
    email: Optional[str] = None


class UserBaseSchema(UserAttributesBaseSchema):
    """User base schema."""

    bio: Annotated[
        Optional[UserBioBaseSchema],
        RelationshipInfo(
            resource_type="user_bio",
        ),
    ] = None
    comments: Annotated[
        Optional[list[PostCommentSchema]],
        RelationshipInfo(
            resource_type="post_comment",
            many=True,
        ),
    ] = None
    computers: Annotated[
        Optional[list[ComputerSchema]],
        RelationshipInfo(
            resource_type="computer",
            many=True,
        ),
    ] = None
    posts: Annotated[
        Optional[list[PostSchema]],
        RelationshipInfo(
            resource_type="post",
            many=True,
        ),
    ] = None
    workplace: Annotated[
        Optional[WorkplaceSchema],
        RelationshipInfo(
            resource_type="workplace",
        ),
    ] = None


class UserPatchSchema(UserBaseSchema):
    """User PATCH schema."""


class UserInSchema(UserBaseSchema):
    """User input schema."""


class UserInSchemaAllowIdOnPost(UserBaseSchema):
    id: Annotated[str, ClientCanSetId()]


class UserSchema(UserInSchema):
    """User item schema."""

    id: int


class CustomUserAttributesSchema(UserBaseSchema):
    spam: str
    eggs: str
