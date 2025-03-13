from inspect import Parameter, Signature, signature
from typing import Any, Callable, Iterable, Literal, Optional, Type

from fastapi import Body, Path, Query, Request

from fastapi_jsonapi.api.schemas import ResourceData
from fastapi_jsonapi.data_typing import TypeModel, TypeSchema
from fastapi_jsonapi.signature import (
    create_additional_query_params,
    create_dependency_params_from_pydantic_model,
    get_separated_params,
)
from fastapi_jsonapi.views import Operation, OperationConfig, ViewBase


class OperationAlreadyHandled: ...


class EndpointsBuilder:
    def __init__(self, resource_type: str, data: ResourceData):
        self._resource_type: str = resource_type
        self._data: ResourceData = data
        self._operation_to_action: dict[Operation, Literal["get", "create", "update", "delete"]] = {
            Operation.CREATE: "create",
            Operation.GET: "get",
            Operation.GET_LIST: "get",
            Operation.DELETE: "delete",
            Operation.DELETE_LIST: "delete",
            Operation.UPDATE: "update",
        }
        self._operation_to_creation_method: dict[Operation, Callable] = {
            Operation.CREATE: self.create_post_fastapi_endpoint,
            Operation.DELETE: self.create_delete_fastapi_endpoint,
            Operation.DELETE_LIST: self.create_delete_list_fastapi_endpoint,
            Operation.GET: self.create_get_fastapi_endpoint,
            Operation.GET_LIST: self.create_get_list_fastapi_endpoint,
            Operation.UPDATE: self.create_update_fastapi_endpoint,
        }

    @classmethod
    def _update_operation_config(cls, view: Type[ViewBase], operation: Operation) -> OperationConfig:
        """
        Merge two pydantic schemas into one.
        """
        target_config = view.operation_dependencies.get(operation) or OperationConfig()
        common_config = view.operation_dependencies.get(Operation.ALL) or OperationConfig()

        # in case of relationship fetch endpoints
        if target_config.dependencies and issubclass(target_config.dependencies, OperationAlreadyHandled):
            return view.operation_dependencies[operation]

        dependencies_model = target_config.dependencies or common_config.dependencies

        same_type = target_config.dependencies is common_config.dependencies
        if not same_type and all([target_config.dependencies, common_config.dependencies]):
            dependencies_model = type(
                f"{view.__name__}{operation.name.title()}MethodDependencyModel",
                (
                    common_config.dependencies,
                    target_config.dependencies,
                    OperationAlreadyHandled,
                ),
                {},
            )

        new_method_config = OperationConfig(
            dependencies=dependencies_model,
            prepare_data_layer_kwargs=target_config.handler or common_config.handler,
        )
        view.operation_dependencies[operation] = new_method_config

        return new_method_config

    def _create_pagination_query_params(self) -> list[Parameter]:
        size = Query(self._data.pagination_default_size, alias="page[size]", title="pagination_page_size")
        number = Query(self._data.pagination_default_number, alias="page[number]", title="pagination_page_number")
        offset = Query(self._data.pagination_default_offset, alias="page[offset]", title="pagination_page_offset")
        limit = Query(self._data.pagination_default_limit, alias="page[limit]", title="pagination_page_limit")

        return [
            Parameter(
                # name doesn't really matter here
                name=q_param.title,
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                annotation=Optional[int],
                default=q_param,
            )
            for q_param in (
                size,
                number,
                offset,
                limit,
            )
        ]

    @classmethod
    def _create_filters_query_dependency_param(cls):
        filters_list = Query(
            None,
            alias="filter",
            description="[Filtering docs](https://fastapi-jsonapi.readthedocs.io/en/latest/filtering.html)"
            "\nExamples:\n* filter for timestamp interval: "
            '`[{"name": "timestamp", "op": "ge", "val": "2020-07-16T11:35:33.383"},'
            '{"name": "timestamp", "op": "le", "val": "2020-07-21T11:35:33.383"}]`',
        )
        return Parameter(
            name="filters_list",
            kind=Parameter.POSITIONAL_OR_KEYWORD,
            annotation=Optional[str],
            default=filters_list,
        )

    @classmethod
    def _create_sort_query_dependency_param(cls):
        sort = Query(
            None,
            alias="sort",
            description="[Sorting docs](https://fastapi-jsonapi.readthedocs.io/en/latest/sorting.html)"
            "\nExamples:\n* `email` - sort by email ASC\n* `-email` - sort by email DESC"
            "\n* `created_at,-email` - sort by created_at ASC and by email DESC",
        )
        return Parameter(
            name="sort",
            kind=Parameter.POSITIONAL_OR_KEYWORD,
            annotation=Optional[str],
            default=sort,
        )

    def _update_signature_for_resource_list_view(
        self,
        wrapper: Callable[..., Any],
        context_schema: Type[TypeSchema],
        additional_dependency_params: Iterable[Parameter] = (),
    ) -> Signature:
        sig = signature(wrapper)
        params, tail_params = get_separated_params(sig)

        filter_params, include_params = create_additional_query_params(schema=context_schema)

        extra_params = []
        extra_params.extend(self._create_pagination_query_params())
        extra_params.extend(filter_params)
        extra_params.append(self._create_filters_query_dependency_param())
        extra_params.append(self._create_sort_query_dependency_param())
        extra_params.extend(include_params)

        return sig.replace(parameters=params + extra_params + list(additional_dependency_params) + tail_params)

    @staticmethod
    def _update_signature_for_resource_detail_view(
        wrapper: Callable[..., Any],
        context_schema: Type[TypeSchema],
        additional_dependency_params: Iterable[Parameter] = (),
    ) -> Signature:
        sig = signature(wrapper)
        params, tail_params = get_separated_params(sig)

        _, include_params = create_additional_query_params(schema=context_schema)

        return sig.replace(parameters=params + include_params + list(additional_dependency_params) + tail_params)

    @classmethod
    def _update_method_config_and_get_dependency_params(
        cls,
        view: Type[ViewBase],
        operation: Operation,
    ) -> list[Parameter]:
        method_config = cls._update_operation_config(view, operation)

        if method_config.dependencies is None:
            return []

        return create_dependency_params_from_pydantic_model(method_config.dependencies)

    def _update_signature(
        self,
        wrapper: Callable[..., Any],
        view: Type[ViewBase],
        operation: Operation,
        context_schema: Type[TypeSchema],
        is_list_endpoint: bool = False,
    ):
        additional_dependency_params = self._update_method_config_and_get_dependency_params(
            view=view,
            operation=operation,
        )

        if is_list_endpoint:
            return self._update_signature_for_resource_list_view(
                wrapper=wrapper,
                context_schema=context_schema,
                additional_dependency_params=additional_dependency_params,
            )

        return self._update_signature_for_resource_detail_view(
            wrapper=wrapper,
            context_schema=context_schema,
            additional_dependency_params=additional_dependency_params,
        )

    def create_post_fastapi_endpoint(
        self,
        resource_type: str,
        operation: Operation,
        view: Type[ViewBase],
        model: Type[TypeModel],
        source_schema: Type[TypeSchema],
        schema_in_post_data: Type[TypeSchema],
        **view_options,
    ):
        async def wrapper(
            request: Request,
            data: schema_in_post_data = Body(embed=True),
            **extra_view_deps,
        ):
            view_instance = view(
                request=request,
                resource_type=resource_type,
                operation=operation,
                model=model,
                schema=source_schema,
                **view_options,
            )
            return await view_instance.handle_post_resource_list(data_create=data, **extra_view_deps)

        wrapper.__signature__ = self._update_signature(
            wrapper=wrapper,
            view=view,
            operation=operation,
            context_schema=self._data.source_schema,
        )
        return wrapper

    def create_update_fastapi_endpoint(
        self,
        resource_type: str,
        operation: Operation,
        view: Type[ViewBase],
        model: Type[TypeModel],
        source_schema: Type[TypeSchema],
        schema_in_patch_data: Type[TypeSchema],
        **view_options,
    ):
        async def wrapper(
            request: Request,
            data: schema_in_patch_data = Body(embed=True),
            obj_id: str = Path(...),
            **extra_view_deps,
        ):
            view_instance = view(
                request=request,
                resource_type=resource_type,
                operation=operation,
                model=model,
                schema=source_schema,
                **view_options,
            )
            return await view_instance.handle_update_resource(obj_id=obj_id, data_update=data, **extra_view_deps)

        wrapper.__signature__ = self._update_signature(
            wrapper=wrapper,
            view=view,
            operation=operation,
            context_schema=self._data.source_schema,
        )
        return wrapper

    def create_delete_fastapi_endpoint(
        self,
        resource_type: str,
        operation: Operation,
        view: Type[ViewBase],
        model: Type[TypeModel],
        source_schema: Type[TypeSchema],
        **view_options,
    ):
        async def wrapper(
            request: Request,
            obj_id: str = Path(...),
            **extra_view_deps,
        ):
            view_instance = view(
                request=request,
                resource_type=resource_type,
                operation=operation,
                model=model,
                schema=source_schema,
                **view_options,
            )
            return await view_instance.handle_delete_resource(obj_id=obj_id, **extra_view_deps)

        wrapper.__signature__ = self._update_signature(
            wrapper=wrapper,
            view=view,
            operation=operation,
            context_schema=self._data.source_schema,
        )
        return wrapper

    def create_get_fastapi_endpoint(
        self,
        resource_type: str,
        operation: Operation,
        view: Type[ViewBase],
        model: Type[TypeModel],
        source_schema: Type[TypeSchema],
        **view_options,
    ):
        async def wrapper(
            request: Request,
            obj_id: str = Path(...),
            **extra_view_deps,
        ):
            view_instance = view(
                request=request,
                resource_type=resource_type,
                operation=operation,
                model=model,
                schema=source_schema,
                **view_options,
            )
            return await view_instance.handle_get_resource_detail(obj_id=obj_id, **extra_view_deps)

        wrapper.__signature__ = self._update_signature(
            wrapper=wrapper,
            view=view,
            operation=operation,
            context_schema=self._data.source_schema,
        )
        return wrapper

    def create_get_relationship_fastapi_endpoint(
        self,
        resource_type: str,
        relationship_name: str,
        parent_resource_type: str,
        view: Type[ViewBase],
        model: Type[TypeModel],
        source_schema: Type[TypeSchema],
        **view_options,
    ):
        async def wrapper(
            request: Request,
            obj_id: str = Path(...),
            **extra_view_deps,
        ):
            view_instance = view(
                request=request,
                resource_type=resource_type,
                operation=Operation.GET,
                model=model,
                schema=source_schema,
                **view_options,
            )
            return await view.handle_get_resource_relationship(
                view_instance,
                obj_id=obj_id,
                relationship_name=relationship_name,
                parent_resource_type=parent_resource_type,
                **extra_view_deps,
            )

        wrapper.__signature__ = self._update_signature(
            wrapper=wrapper,
            view=view,
            operation=Operation.GET,
            context_schema=source_schema,
        )
        return wrapper

    def create_get_relationship_list_fastapi_endpoint(
        self,
        resource_type: str,
        relationship_name: str,
        parent_resource_type: str,
        view: Type[ViewBase],
        model: Type[TypeModel],
        source_schema: Type[TypeSchema],
        **view_options,
    ):
        async def wrapper(
            request: Request,
            obj_id: str = Path(...),
            **extra_view_deps,
        ):
            view_instance = view(
                request=request,
                resource_type=resource_type,
                operation=Operation.GET_LIST,
                model=model,
                schema=source_schema,
                **view_options,
            )
            return await view.handle_get_resource_relationship_list(
                view_instance,
                obj_id=obj_id,
                relationship_name=relationship_name,
                parent_resource_type=parent_resource_type,
                **extra_view_deps,
            )

        wrapper.__signature__ = self._update_signature(
            wrapper=wrapper,
            view=view,
            operation=Operation.GET_LIST,
            context_schema=source_schema,
        )
        return wrapper

    def create_get_list_fastapi_endpoint(
        self,
        resource_type: str,
        operation: Operation,
        view: Type[ViewBase],
        model: Type[TypeModel],
        source_schema: Type[TypeSchema],
        **view_options,
    ):
        async def wrapper(
            request: Request,
            **extra_view_deps,
        ):
            view_instance = view(
                request=request,
                resource_type=resource_type,
                operation=operation,
                model=model,
                schema=source_schema,
                **view_options,
            )
            return await view_instance.handle_get_resource_list(**extra_view_deps)

        wrapper.__signature__ = self._update_signature(
            wrapper=wrapper,
            view=view,
            operation=operation,
            is_list_endpoint=True,
            context_schema=self._data.source_schema,
        )
        return wrapper

    def create_delete_list_fastapi_endpoint(
        self,
        resource_type: str,
        operation: Operation,
        view: Type[ViewBase],
        model: Type[TypeModel],
        source_schema: Type[TypeSchema],
        **view_options,
    ):
        async def wrapper(
            request: Request,
            **extra_view_deps,
        ):
            view_instance = view(
                request=request,
                resource_type=resource_type,
                operation=operation,
                model=model,
                schema=source_schema,
                **view_options,
            )
            return await view_instance.handle_delete_resource_list(**extra_view_deps)

        wrapper.__signature__ = self._update_signature(
            wrapper=wrapper,
            view=view,
            operation=operation,
            is_list_endpoint=True,
            context_schema=self._data.source_schema,
        )
        return wrapper

    def create_common_fastapi_endpoint(
        self,
        operation: Operation,
        **view_options,
    ) -> tuple[str, Callable]:
        name = self.get_common_endpoint_name(self._resource_type, operation)
        kwargs = {
            "resource_type": self._resource_type,
            "operation": operation,
            "view": self._data.view,
            "model": self._data.model,
            "source_schema": self._data.source_schema,
        }

        if operation == Operation.CREATE:
            kwargs["schema_in_post_data"] = self._data.schema_in_post_data

        if operation == Operation.UPDATE:
            kwargs["schema_in_patch_data"] = self._data.schema_in_patch_data

        endpoint = self._operation_to_creation_method[operation](**kwargs, **view_options)
        return name, endpoint

    def create_relationship_endpoint(
        self,
        resource_type: str,
        operation: Operation,
        relationship_name: str,
        parent_resource_type: str,
        view: Type[ViewBase],
        model: Type[TypeModel],
        source_schema: Type[TypeSchema],
    ) -> tuple[str, Callable]:
        name = self.get_relationship_endpoint_name(parent_resource_type, relationship_name, operation)

        if operation == Operation.GET:
            creation_method = self.create_get_relationship_fastapi_endpoint
        elif operation == Operation.GET_LIST:
            creation_method = self.create_get_relationship_list_fastapi_endpoint
        else:
            msg = f"The operation {operation} is not supported on relationship endpoint creation"
            raise Exception(msg)

        endpoint = creation_method(
            resource_type=resource_type,
            relationship_name=relationship_name,
            parent_resource_type=parent_resource_type,
            view=view,
            model=model,
            source_schema=source_schema,
        )
        return name, endpoint

    @staticmethod
    def get_endpoint_kind(operation: Operation) -> str:
        kind = "detail"
        if operation in {Operation.GET_LIST, Operation.DELETE_LIST, Operation.CREATE}:
            kind = "list"

        return kind

    def get_common_endpoint_name(
        self,
        resource_type: str,
        operation: Operation,
    ):
        """
        Generate endpoint name
        """
        action = self._operation_to_action[operation]
        kind = self.get_endpoint_kind(operation)
        return f"{action}_{resource_type}_{kind}"

    def get_relationship_endpoint_name(
        self,
        resource_type: str,
        relationship_name: str,
        operation: Operation,
    ):
        kind = self.get_endpoint_kind(operation)
        return f"fetch_{resource_type}_{relationship_name}_{kind}"
