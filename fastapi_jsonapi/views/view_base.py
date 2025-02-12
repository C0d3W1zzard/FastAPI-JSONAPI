import inspect
import logging
from functools import partial
from typing import Any, Callable, ClassVar, Iterable, Optional, Type

from fastapi import Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel as PydanticBaseModel

from fastapi_jsonapi import QueryStringManager, RoutersJSONAPI
from fastapi_jsonapi.common import get_relationship_info_from_field_metadata
from fastapi_jsonapi.data_layers.base import BaseDataLayer
from fastapi_jsonapi.data_typing import TypeModel, TypeSchema
from fastapi_jsonapi.models_storage import models_storage
from fastapi_jsonapi.schema_base import BaseModel
from fastapi_jsonapi.schemas_storage import schemas_storage
from fastapi_jsonapi.types_metadata import RelationshipInfo
from fastapi_jsonapi.views.utils import HTTPMethod, HTTPMethodConfig

logger = logging.getLogger(__name__)


class ViewBase:
    """
    Views are inited for each request
    """

    data_layer_cls = BaseDataLayer
    method_dependencies: ClassVar[dict[HTTPMethod, HTTPMethodConfig]] = {}

    def __init__(self, *, request: Request, jsonapi: RoutersJSONAPI, **options):
        self.request: Request = request
        self.jsonapi: RoutersJSONAPI = jsonapi
        self.options: dict = options
        self.query_params: QueryStringManager = QueryStringManager(request=request)

    def _get_data_layer(self, schema: Type[BaseModel], **dl_kwargs):
        return self.data_layer_cls(
            request=self.request,
            schema=schema,
            model=self.jsonapi.model,
            resource_type=self.jsonapi.type_,
            **dl_kwargs,
        )

    async def get_data_layer(
        self,
        extra_view_deps: dict[str, Any],
    ) -> BaseDataLayer:
        raise NotImplementedError

    async def get_data_layer_for_detail(
        self,
        extra_view_deps: dict[str, Any],
    ) -> BaseDataLayer:
        """
        Prepares data layer for detail view

        :param extra_view_deps:
        :return:
        """
        dl_kwargs = await self.handle_endpoint_dependencies(extra_view_deps)
        return self._get_data_layer(
            schema=self.jsonapi.schema_detail,
            **dl_kwargs,
        )

    async def get_data_layer_for_list(
        self,
        extra_view_deps: dict[str, Any],
    ) -> BaseDataLayer:
        """
        Prepares data layer for list view

        :param extra_view_deps:
        :return:
        """
        dl_kwargs = await self.handle_endpoint_dependencies(extra_view_deps)
        return self._get_data_layer(
            schema=self.jsonapi.schema_list,
            **dl_kwargs,
        )

    async def _run_handler(
        self,
        handler: Callable,
        dto: Optional[BaseModel] = None,
    ):
        handler = partial(handler, self, dto) if dto is not None else partial(handler, self)

        if inspect.iscoroutinefunction(handler):
            return await handler()

        return await run_in_threadpool(handler)

    async def _handle_config(
        self,
        method_config: HTTPMethodConfig,
        extra_view_deps: dict[str, Any],
    ) -> dict[str, Any]:
        if method_config.handler is None:
            return {}

        if method_config.dependencies:
            dto_class: Type[PydanticBaseModel] = method_config.dependencies
            dto = dto_class(**extra_view_deps)
            return await self._run_handler(method_config.handler, dto)

        return await self._run_handler(method_config.handler)

    async def handle_endpoint_dependencies(
        self,
        extra_view_deps: dict[str, Any],
    ) -> dict:
        """
        :return dict: this is **kwargs for DataLayer.__init___
        """
        dl_kwargs = {}
        if common_method_config := self.method_dependencies.get(HTTPMethod.ALL):
            dl_kwargs.update(await self._handle_config(common_method_config, extra_view_deps))

        if self.request.method not in HTTPMethod.names():
            return dl_kwargs

        if method_config := self.method_dependencies.get(HTTPMethod[self.request.method]):
            dl_kwargs.update(await self._handle_config(method_config, extra_view_deps))

        return dl_kwargs

    @classmethod
    def _prepare_item_data(
        cls,
        db_item,
        resource_type: str,
        include_fields: Optional[dict[str, dict[str, Type[TypeSchema]]]] = None,
    ) -> dict:
        if include_fields is None or not (field_schemas := include_fields.get(resource_type)):
            attrs_schema = schemas_storage.get_attrs_schema(resource_type, operation_type="get")
            data_schema = schemas_storage.get_data_schema(resource_type, operation_type="get")
            return data_schema(
                id=f"{db_item.id}",
                attributes=attrs_schema.model_validate(db_item),
            ).model_dump()

        result_attributes = {}
        # empty str means skip all attributes
        if "" not in field_schemas:
            pre_values = {}
            for field_name, field_schema in field_schemas.items():
                pre_values[field_name] = getattr(db_item, field_name)

            before_validators, after_validators = schemas_storage.get_model_validators(
                resource_type,
                operation_type="get",
            )
            if before_validators:
                for validator_name, validator in before_validators.items():
                    pre_values = validator.wrapped(pre_values)

            for field_name, field_schema in field_schemas.items():
                validated_model = field_schema(**{field_name: pre_values[field_name]})

                if after_validators:
                    for validator_name, validator in after_validators.items():
                        validated_model = validator.wrapped(validated_model)

                result_attributes[field_name] = getattr(validated_model, field_name)

        return {
            "id": f"{models_storage.get_object_id(db_item, resource_type)}",
            "type": resource_type,
            "attributes": result_attributes,
        }

    def _prepare_include_params(self) -> list[list[str]]:
        result = []
        includes = sorted(self.query_params.include)
        prev, *_ = includes

        for include in includes:
            if not include.startswith(prev):
                result.append(prev.split("."))

            prev = include

        result.append(prev.split("."))
        return result

    @classmethod
    def _get_include_key(cls, db_item: TypeModel, info: RelationshipInfo) -> tuple[str, str]:
        return info.resource_type, str(getattr(db_item, info.id_field_name))

    def _process_includes(
        self,
        db_items: list[TypeModel],
        items_data: list[dict],
        resource_type: str,
        include_paths: list[Iterable[str]],
        include_fields: dict[str, dict[str, Type[TypeSchema]]],
        result_included: Optional[dict] = None,
    ) -> dict[tuple[str, str], dict]:
        result_included = result_included or {}

        for db_item, item_data in zip(db_items, items_data):
            item_data["relationships"] = item_data.get("relationships", {})

            for path in include_paths:
                target_relationship, *include_path = path
                info: RelationshipInfo = schemas_storage.get_relationship(
                    resource_type=resource_type,
                    operation_type="get",
                    field_name=target_relationship,
                )
                db_items_to_process: list[TypeModel] = []
                items_data_to_process: list[dict] = []

                if info.many:
                    relationship_data = []

                    for relationship_db_item in getattr(db_item, target_relationship):
                        include_key = self._get_include_key(relationship_db_item, info)

                        if not (relationship_item_data := result_included.get(include_key)):
                            relationship_item_data = self._prepare_item_data(
                                db_item=relationship_db_item,
                                resource_type=info.resource_type,
                                include_fields=include_fields,
                            )
                            result_included[include_key] = relationship_item_data

                        db_items_to_process.append(relationship_db_item)
                        relationship_data.append(
                            {
                                "id": str(getattr(relationship_db_item, info.id_field_name)),
                                "type": info.resource_type,
                            },
                        )
                        items_data_to_process.append(relationship_item_data)
                else:
                    if (relationship_db_item := getattr(db_item, target_relationship)) is None:
                        item_data["relationships"][target_relationship] = {"data": None}
                        continue

                    db_items_to_process.append(relationship_db_item)
                    relationship_data = {
                        "id": str(getattr(relationship_db_item, info.id_field_name)),
                        "type": info.resource_type,
                    }

                    include_key = self._get_include_key(relationship_db_item, info)

                    if not (relationship_item_data := result_included.get(include_key)):
                        relationship_item_data = self._prepare_item_data(relationship_db_item, info.resource_type)
                        result_included[include_key] = relationship_item_data

                    items_data_to_process.append(relationship_item_data)

                if include_path:
                    self._process_includes(
                        db_items=db_items_to_process,
                        items_data=items_data_to_process,
                        resource_type=info.resource_type,
                        include_paths=[include_path],
                        result_included=result_included,
                        include_fields=include_fields,
                    )

                item_data["relationships"][target_relationship] = {"data": relationship_data}

        return result_included

    @classmethod
    def _get_schema_field_names(cls, schema: type[TypeSchema]) -> set[str]:
        """Returns all attribute names except relationships"""
        result = set()

        for field_name, field in schema.model_fields.items():
            if get_relationship_info_from_field_metadata(field):
                continue

            result.add(field_name)

        return result

    def _get_include_fields(self) -> dict[str, dict[str, Type[TypeSchema]]]:
        include_fields = {}
        for resource_type, field_names in self.query_params.fields.items():
            include_fields[resource_type] = {}

            for field_name in field_names:
                include_fields[resource_type][field_name] = schemas_storage.get_field_schema(
                    resource_type=resource_type,
                    operation_type="get",
                    field_name=field_name,
                )

        return include_fields

    def _build_detail_response(self, db_item: TypeModel) -> dict:
        include_fields = self._get_include_fields()
        item_data = self._prepare_item_data(db_item, self.jsonapi.type_, include_fields)
        response = {
            "data": item_data,
            "jsonapi": {"version": "1.0"},
            "meta": None,
        }

        if self.query_params.include:
            included = self._process_includes(
                db_items=[db_item],
                items_data=[item_data],
                include_paths=self._prepare_include_params(),
                resource_type=self.jsonapi.type_,
                include_fields=include_fields,
            )
            response["included"] = [value for _, value in sorted(included.items(), key=lambda item: item[0])]

        return response

    def _build_list_response(
        self,
        items_from_db: list[TypeModel],
        count: int,
        total_pages: int,
    ) -> dict:
        include_fields = self._get_include_fields()
        items_data = [
            self._prepare_item_data(db_item, self.jsonapi.type_, include_fields) for db_item in items_from_db
        ]
        response = {
            "data": items_data,
            "jsonapi": {"version": "1.0"},
            "meta": {"count": count, "totalPages": total_pages},
        }

        if self.query_params.include:
            included = self._process_includes(
                db_items=items_from_db,
                items_data=items_data,
                resource_type=self.jsonapi.type_,
                include_paths=self._prepare_include_params(),
                include_fields=include_fields,
            )
            response["included"] = [value for _, value in sorted(included.items(), key=lambda item: item[0])]

        return response
