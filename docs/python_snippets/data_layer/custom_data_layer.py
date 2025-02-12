from fastapi import FastAPI

from fastapi_jsonapi import ApplicationBuilder
from fastapi_jsonapi.data_layers.base import BaseDataLayer
from fastapi_jsonapi.data_layers.sqla.orm import SqlalchemyDataLayer
from fastapi_jsonapi.views import ViewBase


class MyCustomDataLayer(BaseDataLayer):
    """Overload abstract methods here"""


class MyCustomSqlaDataLayer(SqlalchemyDataLayer):
    """Overload any methods here"""

    async def before_delete_objects(self, objects: list, view_kwargs: dict):
        raise Exception("not allowed to delete objects")


class UserView(ViewBase):
    data_layer_cls = MyCustomDataLayer


app = FastAPI()
builder = ApplicationBuilder(app)
builder.add_resource(
    # ...
    view=UserView,
    # ...
)
