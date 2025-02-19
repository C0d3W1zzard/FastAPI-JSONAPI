import logging
from typing import Callable, Type

from fastapi_jsonapi.data_typing import TypeModel
from fastapi_jsonapi.exceptions import BadRequest, InternalServerError

log = logging.getLogger(__name__)


class ModelsStorage:
    relationship_search_handlers: dict[str, Callable[[str, Type[TypeModel], str], Type[TypeModel]]]

    def __init__(self):
        self._data: dict[str, TypeModel] = {}
        self.relationship_search_handlers = {}

    def add_model(self, resource_type: str, model: Type[TypeModel]):
        self._data[resource_type] = model

    def get_model(self, resource_type: str) -> Type[TypeModel]:
        try:
            return self._data[resource_type]
        except KeyError:
            raise InternalServerError(detail=f"Not found model for resource_type {resource_type!r}.")

    def register_search_handler(self, orm_mode: str, handler: Callable[[str, Type[TypeModel], str], Type[TypeModel]]):
        self.relationship_search_handlers[orm_mode] = handler

    def set_orm_mode(self, orm_mode: str):
        self._orm_mode = orm_mode

    def search_relationship_model(
        self,
        resource_type: str,
        model: Type[TypeModel],
        field_name: str,
    ) -> Type[TypeModel]:
        try:
            orm_handler = self.relationship_search_handlers[self._orm_mode]
        except KeyError:
            raise InternalServerError(
                detail=f"Not found orm handler for {self._orm_mode!r}. "
                f"Please register this with SchemasStorage.register_search_handler",
            )

        return orm_handler(resource_type, model, field_name)

    @staticmethod
    def sqla_search_relationship_model(
        resource_type: str,
        model: Type[TypeModel],
        field_name: str,
    ):
        try:
            return getattr(model, field_name).property.entity.entity
        except AttributeError:
            raise BadRequest(
                detail=f"There is no related model for resource_type {resource_type!r} by relation {field_name!r}.",
            )
        except Exception as ex:
            log.error("Relationship search error", exc_info=ex)
            raise InternalServerError(
                detail=f"Relationship search error for resource_type {resource_type!r} by relation {field_name!r}.",
            )


models_storage = ModelsStorage()
models_storage.register_search_handler("sqla", ModelsStorage.sqla_search_relationship_model)
models_storage.set_orm_mode("sqla")
