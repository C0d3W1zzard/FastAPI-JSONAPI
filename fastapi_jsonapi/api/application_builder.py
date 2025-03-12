from itertools import product
from queue import Queue
from typing import Callable, Iterable, Optional, Type

from fastapi import APIRouter, FastAPI, status
from pydantic import BaseModel

from fastapi_jsonapi.api.endpoint_builder import EndpointsBuilder
from fastapi_jsonapi.api.schemas import ResourceData
from fastapi_jsonapi.atomic import AtomicOperations
from fastapi_jsonapi.data_typing import TypeModel
from fastapi_jsonapi.exceptions import ExceptionResponseSchema, HTTPException
from fastapi_jsonapi.exceptions.handlers import base_exception_handler
from fastapi_jsonapi.schema import get_schema_from_field_annotation
from fastapi_jsonapi.schema_builder import SchemaBuilder
from fastapi_jsonapi.storages.models_storage import models_storage
from fastapi_jsonapi.storages.schemas_storage import schemas_storage
from fastapi_jsonapi.storages.views_storage import views_storage
from fastapi_jsonapi.views import Operation, ViewBase


class ApplicationBuilderError(Exception): ...


class ApplicationBuilder:
    def __init__(
        self,
        app: FastAPI,
        base_router: Optional[APIRouter] = None,
        exception_handler: Optional[Callable] = None,
        **base_router_include_kwargs,
    ):
        self._app: FastAPI = app
        self._base_router: APIRouter = base_router or APIRouter()
        self._base_router_include_kwargs: dict = base_router_include_kwargs
        self._routers: dict[str, APIRouter] = {}
        self._router_include_kwargs: dict[str, dict] = {}
        self._paths = set()
        self._resource_data: dict[str, ResourceData] = {}
        self._exception_handler: Callable = base_exception_handler
        self._initialized: bool = False

        if exception_handler is not None:
            self._exception_handler = exception_handler

    def add_resource(
        self,
        path: str,
        tags: Iterable[str],
        resource_type: str,
        view: Type[ViewBase],
        model: Type[TypeModel],
        schema: Type[BaseModel],
        router: Optional[APIRouter] = None,
        schema_in_post: Optional[Type[BaseModel]] = None,
        schema_in_patch: Optional[Type[BaseModel]] = None,
        pagination_default_size: Optional[int] = 25,
        pagination_default_number: Optional[int] = 1,
        pagination_default_offset: Optional[int] = None,
        pagination_default_limit: Optional[int] = None,
        operations: Iterable[str] = (),
        ending_slash: bool = True,
        model_id_field_name: str = "id",
        include_router_kwargs: Optional[dict] = None,
    ):
        if self._initialized:
            msg = "Can't add resource after app initialization"
            raise ApplicationBuilderError(msg)

        if resource_type in self._resource_data:
            msg = f"Resource {resource_type!r} already registered"
            raise ApplicationBuilderError(msg)

        if include_router_kwargs is not None and router is None:
            msg = "The argument 'include_router_kwargs' forbidden if 'router' not passed"
            raise ApplicationBuilderError(msg)

        models_storage.add_model(resource_type, model, model_id_field_name)
        views_storage.add_view(resource_type, view)
        dto = SchemaBuilder(resource_type).create_schemas(
            schema=schema,
            schema_in_post=schema_in_post,
            schema_in_patch=schema_in_patch,
        )

        resource_operations = []
        for operation in operations:
            if operation == Operation.ALL:
                resource_operations = Operation.real_operations()
                break

            resource_operations.append(operation)

        resource_operations = resource_operations or Operation.real_operations()

        resource_data = ResourceData(
            path=path,
            router=router,
            tags=list(tags),
            view=view,
            model=model,
            source_schema=schema,
            schema_in_post=schema_in_post,
            schema_in_post_data=dto.schema_in_post_data,
            schema_in_patch=schema_in_patch,
            schema_in_patch_data=dto.schema_in_patch_data,
            detail_response_schema=dto.detail_response_schema,
            list_response_schema=dto.list_response_schema,
            pagination_default_size=pagination_default_size,
            pagination_default_number=pagination_default_number,
            pagination_default_offset=pagination_default_offset,
            pagination_default_limit=pagination_default_limit,
            operations=resource_operations,
            ending_slash=ending_slash,
        )
        self._resource_data[resource_type] = resource_data

        router = router or self._base_router
        self._routers[resource_type] = router

        if router is not None:
            self._router_include_kwargs[resource_type] = include_router_kwargs or {}

    def initialize(self) -> FastAPI:
        if self._initialized:
            msg = "Application already initialized"
            raise Exception(msg)

        self._initialized = True
        self._traverse_relationship_schemas()
        self._app.add_exception_handler(HTTPException, self._exception_handler)

        status_codes = self._get_status_codes()
        summaries = self._get_summary_pattern_strings()

        for resource_type, data in self._resource_data.items():
            example_responses = self._get_example_responses(data)
            endpoints_builder = EndpointsBuilder(resource_type, data)

            for operation in data.operations:
                name, endpoint = endpoints_builder.create_common_fastapi_endpoint(operation)
                http_method = operation.http_method()
                path = self._create_path(
                    path=data.path,
                    ending_slash=data.ending_slash,
                    include_object_id=(
                        operation
                        in {
                            Operation.GET,
                            Operation.UPDATE,
                            Operation.DELETE,
                        }
                    ),
                )

                self._routers[resource_type].add_api_route(
                    path=path,
                    tags=data.tags,
                    responses=example_responses[operation] | self._get_default_error_responses(),
                    methods=[http_method],
                    summary=summaries[operation].format(resource_type),
                    status_code=status_codes[operation],
                    endpoint=endpoint,
                    name=name,
                )

            relationships_info = schemas_storage.get_relationships_info(
                resource_type=resource_type,
                operation_type="get",
            )

            for relationship_name, info in relationships_info.items():
                if not views_storage.has_view(info.resource_type):
                    continue

                operation = Operation.GET_LIST if info.many else Operation.GET
                path = self._create_path(
                    path=data.path,
                    ending_slash=data.ending_slash,
                    include_object_id=True,
                    relationship_name=relationship_name,
                )
                name, endpoint = endpoints_builder.create_relationship_endpoint(
                    resource_type=info.resource_type,
                    relationship_name=relationship_name,
                    parent_resource_type=resource_type,
                    model=models_storage.get_model(info.resource_type),
                    view=views_storage.get_view(info.resource_type),
                    source_schema=schemas_storage.get_source_schema(info.resource_type),
                    operation=operation,
                )
                self._routers[resource_type].add_api_route(
                    path=path,
                    tags=data.tags,
                    responses=example_responses[operation] | self._get_default_error_responses(),
                    methods=[operation.http_method()],
                    summary=summaries[operation].format(resource_type),
                    status_code=status_codes[operation],
                    endpoint=endpoint,
                    name=name,
                )

        registered_routers = set()
        for resource_type, router in self._routers.items():
            if id(router) in registered_routers:
                continue

            include_kwargs = self._router_include_kwargs.get(resource_type, {})
            if router is self._base_router:
                include_kwargs = self._base_router_include_kwargs

            self._app.include_router(router, **include_kwargs)
            registered_routers.add(id(router))

        atomic = AtomicOperations()
        self._app.include_router(atomic.router)

        return self._app

    @staticmethod
    def _get_status_codes() -> dict[Operation, int]:
        return {
            Operation.GET: status.HTTP_200_OK,
            Operation.CREATE: status.HTTP_201_CREATED,
            Operation.UPDATE: status.HTTP_200_OK,
            Operation.DELETE: status.HTTP_204_NO_CONTENT,
            Operation.GET_LIST: status.HTTP_200_OK,
            Operation.DELETE_LIST: status.HTTP_200_OK,
        }

    @staticmethod
    def _get_example_responses(data: ResourceData) -> dict[Operation, dict]:
        return {
            Operation.GET: {
                status.HTTP_200_OK: {"model": data.detail_response_schema},
            },
            Operation.CREATE: {
                status.HTTP_201_CREATED: {"model": data.detail_response_schema},
            },
            Operation.UPDATE: {
                status.HTTP_200_OK: {"model": data.detail_response_schema},
            },
            Operation.DELETE: {
                status.HTTP_204_NO_CONTENT: {
                    "description": "If a server is able to delete the resource,"
                    " the server MUST return a result with no data",
                },
            },
            Operation.GET_LIST: {
                status.HTTP_200_OK: {"model": data.list_response_schema},
            },
            Operation.DELETE_LIST: {
                status.HTTP_200_OK: {"model": data.detail_response_schema},
            },
        }

    @staticmethod
    def _get_default_error_responses() -> dict:
        return {
            status.HTTP_400_BAD_REQUEST: {"model": ExceptionResponseSchema},
            status.HTTP_401_UNAUTHORIZED: {"model": ExceptionResponseSchema},
            status.HTTP_404_NOT_FOUND: {"model": ExceptionResponseSchema},
            status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ExceptionResponseSchema},
        }

    @staticmethod
    def _get_summary_pattern_strings() -> dict[Operation, str]:
        return {
            Operation.GET: "Get object `{}` by id",
            Operation.CREATE: "Create object `{}`",
            Operation.UPDATE: "Update object `{}` by id",
            Operation.DELETE: "Delete object `{}` by id",
            Operation.GET_LIST: "Get list of `{}` objects",
            Operation.DELETE_LIST: "Delete objects `{}` by filters",
        }

    @staticmethod
    def _create_path(
        path: str,
        ending_slash: bool,
        include_object_id: bool,
        relationship_name: str = "",
    ) -> str:
        path = path.removesuffix("/")
        suffix = "/" if ending_slash else ""

        if include_object_id:
            obj_id = "{obj_id}"
            path = f"{path}/{obj_id}"

        if relationship_name:
            path = f"{path}/relationships/{relationship_name.replace('_', '-')}"

        return f"{path}{suffix}"

    def _traverse_relationship_schemas(self):
        # User can have relationship resources without having CRUD operations for these resource types.
        # So the SchemaStorage will not be filled with schemas without passing through the relationships.

        operations = Queue()
        handled_operations = set()

        for item in product(self._resource_data, ("create", "update", "get")):
            operations.put(item)

        while not operations.empty():
            if (operation := operations.get()) in handled_operations:
                continue

            handled_operations.add(operation)
            resource_type, operation_type = operation

            if not schemas_storage.has_operation(resource_type, operation_type):
                continue

            parent_model = models_storage.get_model(resource_type)
            relationships_info = schemas_storage.get_relationships_info(resource_type, operation_type).items()

            for relationship_name, info in relationships_info:
                if schemas_storage.has_operation(info.resource_type, operation_type="get"):
                    continue

                field = schemas_storage.get_source_relationship_pydantic_field(
                    resource_type=resource_type,
                    operation_type=operation_type,
                    field_name=relationship_name,
                )

                relationship_source_schema = get_schema_from_field_annotation(field)
                relationship_model = models_storage.search_relationship_model(
                    resource_type=resource_type,
                    model=parent_model,
                    field_name=relationship_name,
                )
                models_storage.add_model(info.resource_type, relationship_model, info.id_field_name)

                builder = SchemaBuilder(resource_type=resource_type)
                dto = builder.get_info_from_schema_for_building(
                    base_name=f"{info.resource_type}_hidden_generation",
                    schema=relationship_source_schema,
                    operation_type="get",
                )
                data_schema = builder.build_jsonapi_object(
                    base_name=f"{info.resource_type}_hidden_generation_ObjectJSONAPI",
                    resource_type=info.resource_type,
                    dto=dto,
                    with_relationships=False,
                    id_field_required=True,
                )
                schemas_storage.add_resource(
                    builder=builder,
                    resource_type=info.resource_type,
                    operation_type="get",
                    source_schema=relationship_source_schema,
                    data_schema=data_schema,
                    attributes_schema=dto.attributes_schema,
                    field_schemas=dto.field_schemas,
                    relationships_info=dto.relationships_info,
                    model_validators=dto.model_validators,
                )
                operations.put((info.resource_type, "get"))
