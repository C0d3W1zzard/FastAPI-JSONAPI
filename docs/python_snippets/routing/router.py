from fastapi import FastAPI

from examples.api_for_sqlalchemy.models import User
from examples.api_for_sqlalchemy.schemas import UserInSchema, UserPatchSchema, UserSchema
from examples.api_for_sqlalchemy.urls import ViewBase
from fastapi_jsonapi import ApplicationBuilder


def add_routes(app: FastAPI):
    builder = ApplicationBuilder(app)
    builder.add_resource(
        path="/users",
        tags=["User"],
        view=ViewBase,
        model=User,
        schema=UserSchema,
        resource_type="user",
        schema_in_patch=UserPatchSchema,
        schema_in_post=UserInSchema,
    )


app = FastAPI()
add_routes(app)
