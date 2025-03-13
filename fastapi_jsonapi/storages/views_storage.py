from __future__ import annotations

from typing import TYPE_CHECKING, Type

from fastapi_jsonapi.exceptions import InternalServerError

if TYPE_CHECKING:
    from fastapi_jsonapi.views import ViewBase


class ViewStorage:
    def __init__(self):
        self._views: dict[str, Type[ViewBase]] = {}

    def add_view(self, resource_type: str, view: Type[ViewBase]):
        self._views[resource_type] = view

    def get_view(self, resource_type: str) -> Type[ViewBase]:
        try:
            return self._views[resource_type]
        except KeyError:
            raise InternalServerError(
                detail=f"Not found view for resource type {resource_type!r}",
            )

    def has_view(self, resource_type: str) -> bool:
        return resource_type in self._views


views_storage = ViewStorage()
