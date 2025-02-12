from collections import defaultdict
from typing import Any, Literal, Optional, Type

from fastapi_jsonapi.data_typing import TypeSchema
from fastapi_jsonapi.models_storage import models_storage
from fastapi_jsonapi.schema import JSONAPIObjectSchemas, get_schema_from_field_annotation
from fastapi_jsonapi.types_metadata.relationship_info import RelationshipInfo


class SchemasStorage:
    def __init__(self):
        self._data = {}
        self._registered_schemas = set()
        self._jsonapi_object_schemas = {}

    def _init_resource_if_needed(self, resource_type: str):
        if resource_type not in self._data:
            self._data[resource_type] = {
                "relationships": defaultdict(lambda: defaultdict(dict)),
            }

    def add_relationship(
        self,
        from_resource_type: str,
        to_resource_type: str,
        operation_type: Literal["create", "update", "get"],
        field_name: str,
        relationship_schema: Type[TypeSchema],
        relationship_info: RelationshipInfo,
    ):
        self._init_resource_if_needed(from_resource_type)
        relationships = self._data[from_resource_type]["relationships"][to_resource_type]
        relationships[(operation_type, field_name)] = {
            "schema": relationship_schema,
            "info": relationship_info,
        }

    def get_relationship_schema(
        self,
        from_resource_type: str,
        to_resource_type: str,
        operation_type: Literal["create", "update", "get"],
        field_name: str,
    ) -> Optional[TypeSchema]:
        self._init_resource_if_needed(from_resource_type)

        relationships = self._data[from_resource_type]["relationships"][to_resource_type]
        return relationships.get((operation_type, field_name), {}).get("schema")

    def add_resource(
        self,
        builder,
        resource_type: str,
        operation_type: Literal["create", "update", "get"],
        source_schema: Type[TypeSchema],
        data_schema: Type[TypeSchema],
        attributes_schema: Type[TypeSchema],
        field_schemas: dict[str, Type[TypeSchema]],
        relationships_info: dict[str, tuple[RelationshipInfo, Any]],
        model_validators: dict,
    ):
        self._init_resource_if_needed(resource_type)
        if operation_type in self._data[resource_type]:
            return

        before_validators, after_validators = {}, {}
        for validator_name, validator in model_validators.items():
            if validator.decorator_info.mode == "before":
                before_validators[validator_name] = validator
            else:
                after_validators[validator_name] = validator

        self._data[resource_type][operation_type] = {
            "attrs_schema": attributes_schema,
            "field_schemas": field_schemas,
            "data_schema": data_schema,
            "relationships_info": {
                relationship_name: info for relationship_name, (info, _) in relationships_info.items()
            },
            "model_validators": (before_validators, after_validators),
        }
        self._registered_schemas.add((source_schema, resource_type, operation_type))
        model = models_storage.get_model(resource_type)

        # User can have relationship resources without having CRUD operations for these resource types.
        # So the SchemaStorage will not be filled with schemas without passing through the relationships.
        for relationship_name, (info, field) in relationships_info.items():
            relationship_source_schema = get_schema_from_field_annotation(field)

            if (relationship_source_schema, info.resource_type, "get") in self._registered_schemas:
                continue

            relationship_model = models_storage.search_relationship_model(resource_type, model, relationship_name)
            models_storage.add_model(info.resource_type, relationship_model, info.id_field_name)

            dto = builder._get_info_from_schema_for_building(
                base_name=f"{info.resource_type}_hidden_generation",
                schema=relationship_source_schema,
                operation_type="get",
            )
            data_schema = builder._build_jsonapi_object(
                base_name=f"{info.resource_type}_hidden_generation_ObjectJSONAPI",
                resource_type=info.resource_type,
                dto=dto,
                with_relationships=False,
                id_field_required=True,
            )

            self.add_resource(
                builder,
                resource_type=info.resource_type,
                operation_type="get",
                source_schema=relationship_source_schema,
                data_schema=data_schema,
                attributes_schema=dto.attributes_schema,
                field_schemas=dto.field_schemas,
                relationships_info=dto.relationships_info,
                model_validators=dto.model_validators,
            )

    def get_data_schema(
        self,
        resource_type: str,
        operation_type: Literal["create", "update", "get"],
    ) -> Optional[TypeSchema]:
        return self._data[resource_type][operation_type]["data_schema"]

    def get_attrs_schema(
        self,
        resource_type: str,
        operation_type: Literal["create", "update", "get"],
    ) -> Optional[TypeSchema]:
        return self._data[resource_type][operation_type]["attrs_schema"]

    def get_field_schema(
        self,
        resource_type: str,
        operation_type: Literal["create", "update", "get"],
        field_name: str,
    ) -> Optional[TypeSchema]:
        return self._data[resource_type][operation_type]["field_schemas"].get(field_name)

    def get_model_validators(
        self,
        resource_type: str,
        operation_type: Literal["create", "update", "get"],
    ) -> tuple[dict, dict]:
        return self._data[resource_type][operation_type]["model_validators"]

    def get_relationship(
        self,
        resource_type: str,
        operation_type: Literal["create", "update", "get"],
        field_name: str,
    ) -> Optional[RelationshipInfo]:
        return self._data[resource_type][operation_type]["relationships_info"].get(field_name)

    def get_jsonapi_object_schema(
        self,
        source_schema: Type[TypeSchema],
        resource_type: str,
    ) -> Optional[JSONAPIObjectSchemas]:
        return self._jsonapi_object_schemas.get((source_schema, resource_type))

    def add_jsonapi_object_schema(
        self,
        source_schema: Type[TypeSchema],
        resource_type: str,
        jsonapi_object_schema,
    ):
        self._jsonapi_object_schemas[(source_schema, resource_type)] = jsonapi_object_schema


schemas_storage = SchemasStorage()
