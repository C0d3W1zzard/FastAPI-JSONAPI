"""Route creator"""

from fastapi import APIRouter, FastAPI

from fastapi_jsonapi import ApplicationBuilder
from fastapi_jsonapi.atomic import AtomicOperations

from .api.views_base import ViewBase
from .models import (
    Child,
    Computer,
    Parent,
    ParentToChildAssociation,
    Post,
    User,
    UserBio,
    Workplace,
)
from .schemas import (
    ChildInSchema,
    ChildPatchSchema,
    ChildSchema,
    ComputerInSchema,
    ComputerPatchSchema,
    ComputerSchema,
    ParentInSchema,
    ParentPatchSchema,
    ParentSchema,
    ParentToChildAssociationSchema,
    PostInSchema,
    PostPatchSchema,
    PostSchema,
    UserBioBaseSchema,
    UserBioInSchema,
    UserBioPatchSchema,
    UserInSchema,
    UserPatchSchema,
    UserSchema,
    WorkplaceInSchema,
    WorkplacePatchSchema,
    WorkplaceSchema,
)


def add_routes(app: FastAPI):
    router: APIRouter = APIRouter()
    builder = ApplicationBuilder(app)
    builder.add_resource(
        router=router,
        path="/children",
        tags=["Child"],
        view=ViewBase,
        model=Child,
        schema=ChildSchema,
        resource_type="child",
        schema_in_patch=ChildPatchSchema,
        schema_in_post=ChildInSchema,
    )
    builder.add_resource(
        router=router,
        path="/computers",
        tags=["Computer"],
        view=ViewBase,
        model=Computer,
        schema=ComputerSchema,
        resource_type="computer",
        schema_in_patch=ComputerPatchSchema,
        schema_in_post=ComputerInSchema,
    )
    builder.add_resource(
        router=router,
        path="/parent-to-child-association",
        tags=["Parent To Child Association"],
        view=ViewBase,
        schema=ParentToChildAssociationSchema,
        resource_type="parent-to-child-association",
        model=ParentToChildAssociation,
    )
    builder.add_resource(
        router=router,
        path="/parents",
        tags=["Parent"],
        view=ViewBase,
        model=Parent,
        schema=ParentSchema,
        resource_type="parent",
        schema_in_patch=ParentPatchSchema,
        schema_in_post=ParentInSchema,
    )
    builder.add_resource(
        router=router,
        path="/posts",
        tags=["Post"],
        view=ViewBase,
        model=Post,
        schema=PostSchema,
        resource_type="post",
        schema_in_patch=PostPatchSchema,
        schema_in_post=PostInSchema,
    )
    builder.add_resource(
        router=router,
        path="/user-bio",
        tags=["Bio"],
        view=ViewBase,
        model=UserBio,
        schema=UserBioBaseSchema,
        resource_type="user_bio",
        schema_in_patch=UserBioPatchSchema,
        schema_in_post=UserBioInSchema,
    )
    builder.add_resource(
        router=router,
        path="/users",
        tags=["User"],
        view=ViewBase,
        model=User,
        schema=UserSchema,
        resource_type="user",
        schema_in_patch=UserPatchSchema,
        schema_in_post=UserInSchema,
    )
    builder.add_resource(
        router=router,
        path="/workplaces",
        tags=["Workplace"],
        view=ViewBase,
        model=Workplace,
        schema=WorkplaceSchema,
        resource_type="workplace",
        schema_in_patch=WorkplacePatchSchema,
        schema_in_post=WorkplaceInSchema,
    )
    builder.initialize()

    atomic = AtomicOperations()

    app.include_router(router, prefix="")
    app.include_router(atomic.router, prefix="")
