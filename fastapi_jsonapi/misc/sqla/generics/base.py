from fastapi_jsonapi.data_layers.sqla.orm import SqlalchemyDataLayer
from fastapi_jsonapi.views.view_base import ViewBase


class ViewBaseGeneric(ViewBase):
    data_layer_cls = SqlalchemyDataLayer
