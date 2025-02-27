from copy import copy
from typing import Annotated, Generator, Optional, Type

import pytest
from fastapi import FastAPI, status
from fastapi.datastructures import QueryParams
from httpx import AsyncClient
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from pytest_asyncio import fixture
from sqlalchemy.ext.asyncio import AsyncSession

from examples.api_for_sqlalchemy.models import User
from fastapi_jsonapi import RoutersJSONAPI
from fastapi_jsonapi.schemas_storage import schemas_storage
from fastapi_jsonapi.types_metadata import ClientCanSetId
from fastapi_jsonapi.validation_utils import extract_validators
from tests.fixtures.app import build_app_custom
from tests.fixtures.models import Task
from tests.fixtures.schemas import TaskBaseSchema
from tests.misc.utils import fake


@fixture()
async def task_with_none_ids(
    async_session: AsyncSession,
) -> Task:
    task = Task(
        task_ids_dict=None,
        task_ids_list=None,
    )
    async_session.add(task)
    await async_session.commit()

    return task


@pytest.fixture
def resource_type():
    return "task"


class TestTaskValidators:
    async def test_base_model_validator_pre_true_get_one(
        self,
        app: FastAPI,
        client: AsyncClient,
        resource_type: str,
        task_with_none_ids: Task,
    ):
        assert task_with_none_ids.task_ids_dict is None
        assert task_with_none_ids.task_ids_list is None
        url = app.url_path_for(f"get_{resource_type}_detail", obj_id=task_with_none_ids.id)
        res = await client.get(url)
        assert res.status_code == status.HTTP_200_OK, res.text
        response_data = res.json()
        attributes = response_data["data"].pop("attributes")
        assert response_data == {
            "data": {
                "id": f"{task_with_none_ids.id}",
                "type": resource_type,
            },
            "jsonapi": {"version": "1.0"},
            "meta": None,
        }
        assert attributes == {
            # not `None`! schema validator returns empty dict `{}` and empty list `[]`
            # "task_ids": None,
            "task_ids_dict": {},
            "task_ids_list": [],
        }
        assert attributes == TaskBaseSchema.model_validate(task_with_none_ids).model_dump()

    async def test_base_model_model_validator_get_list_and_dict(
        self,
        app: FastAPI,
        client: AsyncClient,
        resource_type: str,
        task_with_none_ids: Task,
    ):
        assert task_with_none_ids.task_ids_dict is None
        assert task_with_none_ids.task_ids_list is None
        url = app.url_path_for(f"get_{resource_type}_list")
        res = await client.get(url)
        assert res.status_code == status.HTTP_200_OK, res.text
        response_data = res.json()
        assert response_data == {
            "data": [
                {
                    "id": f"{task_with_none_ids.id}",
                    "type": resource_type,
                    "attributes": {
                        # not `None`! schema validator returns empty dict `{}` and empty list `[]`
                        # "task_ids": None,
                        "task_ids_dict": {},
                        "task_ids_list": [],
                    },
                },
            ],
            "jsonapi": {
                "version": "1.0",
            },
            "meta": {
                "count": 1,
                "totalPages": 1,
            },
        }

    async def test_base_model_model_validator_create(
        self,
        app: FastAPI,
        client: AsyncClient,
        resource_type: str,
        async_session: AsyncSession,
    ):
        data_create = {
            "data": {
                "type": resource_type,
                "attributes": {
                    # should be converted to [] and {} by schema on create
                    "task_ids_dict": None,
                    "task_ids_list": None,
                },
            },
        }
        url = app.url_path_for(f"create_{resource_type}_list")
        res = await client.post(url, json=data_create)
        assert res.status_code == status.HTTP_201_CREATED, res.text
        response_data: dict = res.json()
        task_id = response_data["data"].pop("id")
        task = await async_session.get(Task, int(task_id))
        assert isinstance(task, Task)
        # we sent request with `None`, but value in db is `[]` and `{}`
        # because validator converted data before object creation
        assert task.task_ids_dict == {}
        assert task.task_ids_list == []
        assert response_data == {
            "data": {
                "type": resource_type,
                "attributes": {
                    # should be empty list and empty dict
                    "task_ids_dict": {},
                    "task_ids_list": [],
                },
            },
            "jsonapi": {"version": "1.0"},
            "meta": None,
        }


class TestValidators:
    resource_type = "validator"

    @fixture(autouse=True)
    def _refresh_caches(self) -> Generator:
        all_jsonapi_routers = copy(RoutersJSONAPI.all_jsonapi_routers)
        schemas_data = copy(schemas_storage._data)

        yield

        RoutersJSONAPI.all_jsonapi_routers = all_jsonapi_routers
        schemas_storage._data = schemas_data

    def build_app(self, schema, resource_type: Optional[str] = None) -> FastAPI:
        return build_app_custom(
            model=User,
            schema=schema,
            resource_type=resource_type or self.resource_type,
        )

    def inherit(self, schema: Type[BaseModel]) -> Type[BaseModel]:
        class InheritedSchema(schema):
            pass

        return InheritedSchema

    async def execute_request_and_check_response(
        self,
        app: FastAPI,
        body: dict,
        expected_detail: str,
        resource_type: Optional[str] = None,
    ):
        resource_type = resource_type or self.resource_type
        async with AsyncClient(app=app, base_url="http://test") as client:
            url = app.url_path_for(f"create_{resource_type}_list")
            res = await client.post(url, json=body)
            assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, res.text
            response_json = res.json()

        assert response_json
        assert "detail" in response_json, response_json
        error = response_json["detail"][0]
        assert error["msg"].endswith(expected_detail), (error, expected_detail)

    async def execute_request_twice_and_check_response(
        self,
        schema: Type[BaseModel],
        body: dict,
        expected_detail: str,
    ):
        """
        Makes two requests for check schema inheritance
        """
        resource_type_1 = self.resource_type + fake.word()
        app_1 = self.build_app(schema, resource_type=resource_type_1)
        resource_type_2 = self.resource_type + fake.word()
        app_2 = self.build_app(self.inherit(schema), resource_type=resource_type_2)

        for app, resource_type in [(app_1, resource_type_1), (app_2, resource_type_2)]:
            await self.execute_request_and_check_response(
                app=app,
                body=body,
                expected_detail=expected_detail,
                resource_type=resource_type,
            )

    async def test_field_validator_call(self):
        """
        Basic check to ensure that field validator called
        """

        class UserSchemaWithValidator(BaseModel):
            model_config = ConfigDict(
                from_attributes=True,
            )

            name: str

            @field_validator("name")
            @classmethod
            def validate_name(cls, value):
                msg = "Check validator"
                raise ValueError(msg)

        create_user_body = {
            "data": {
                "attributes": {
                    "name": fake.name(),
                },
            },
        }
        await self.execute_request_twice_and_check_response(
            schema=UserSchemaWithValidator,
            body=create_user_body,
            expected_detail="Check validator",
        )

    async def test_field_validator_each_item_arg(self):
        class UserSchemaWithValidator(BaseModel):
            model_config = ConfigDict(
                from_attributes=True,
            )

            names: list[str]

            @field_validator("names", mode="after")
            @classmethod
            def validate_name(cls, value):
                for item in value:
                    if item == "bad_name":
                        msg = "Bad name not allowed"
                        raise ValueError(msg)

        create_user_body = {
            "data": {
                "attributes": {
                    "names": ["good_name", "bad_name"],
                },
            },
        }
        await self.execute_request_twice_and_check_response(
            schema=UserSchemaWithValidator,
            body=create_user_body,
            expected_detail="Bad name not allowed",
        )

    async def test_field_validator_pre_arg(self):
        class UserSchemaWithValidator(BaseModel):
            model_config = ConfigDict(
                from_attributes=True,
            )

            name: list[str]

            @field_validator("name", mode="before")
            @classmethod
            def validate_name_pre(cls, value):
                msg = "Pre validator called"
                raise ValueError(msg)

            @field_validator("name", mode="after")
            @classmethod
            def validate_name(cls, value):
                msg = "Not pre validator called"
                raise ValueError(msg)

        create_user_body = {
            "data": {
                "attributes": {
                    "name": fake.name(),
                },
            },
        }
        await self.execute_request_twice_and_check_response(
            schema=UserSchemaWithValidator,
            body=create_user_body,
            expected_detail="Pre validator called",
        )

    async def test_field_validator_several_validators(self):
        class UserSchemaWithValidator(BaseModel):
            model_config = ConfigDict(
                from_attributes=True,
            )

            field: str

            @field_validator("field", mode="after")
            @classmethod
            def validator_1(cls, value):
                if value == "check_validator_1":
                    msg = "Called validator 1"
                    raise ValueError(msg)

                return value

            @field_validator("field", mode="after")
            @classmethod
            def validator_2(cls, value):
                if value == "check_validator_2":
                    msg = "Called validator 2"
                    raise ValueError(msg)

                return value

        create_user_body = {
            "data": {
                "attributes": {
                    "field": "check_validator_1",
                },
            },
        }
        app = self.build_app(UserSchemaWithValidator)
        await self.execute_request_and_check_response(
            app=app,
            body=create_user_body,
            expected_detail="Called validator 1",
        )

        create_user_body = {
            "data": {
                "attributes": {
                    "field": "check_validator_2",
                },
            },
        }
        await self.execute_request_and_check_response(
            app=app,
            body=create_user_body,
            expected_detail="Called validator 2",
        )

    async def test_field_validator_asterisk(self):
        class UserSchemaWithValidator(BaseModel):
            model_config = ConfigDict(
                from_attributes=True,
            )

            field_1: str
            field_2: str

            @field_validator("*", mode="before")
            @classmethod
            def validator(cls, value):
                if value == "bad_value":
                    msg = "Check validator"
                    raise ValueError(msg)
                return value

        create_user_body = {
            "data": {
                "attributes": {
                    "field_1": "bad_value",
                    "field_2": "",
                },
            },
        }
        app = self.build_app(UserSchemaWithValidator)
        await self.execute_request_and_check_response(
            app=app,
            body=create_user_body,
            expected_detail="Check validator",
        )

        create_user_body = {
            "data": {
                "attributes": {
                    "field_1": "",
                    "field_2": "bad_value",
                },
            },
        }
        await self.execute_request_and_check_response(
            app=app,
            body=create_user_body,
            expected_detail="Check validator",
        )

    async def test_check_validator_for_id_field(self):
        """
        Unusual case because of "id" field handling in a different way than attributes
        """

        class UserSchemaWithValidator(BaseModel):
            model_config = ConfigDict(
                from_attributes=True,
            )

            id: Annotated[int, ClientCanSetId()]

            @field_validator("id", mode="after")
            @classmethod
            def validate_id(cls, value):
                msg = "Check validator"
                raise ValueError(msg)

        create_user_body = {
            "data": {
                "attributes": {},
                "id": "42",
            },
        }
        await self.execute_request_twice_and_check_response(
            schema=UserSchemaWithValidator,
            body=create_user_body,
            expected_detail="Check validator",
        )

    @pytest.mark.parametrize(
        "inherit",
        [
            pytest.param(True, id="inherited_true"),
            pytest.param(False, id="inherited_false"),
        ],
    )
    async def test_field_validator_can_change_value(self, inherit: bool):
        class UserSchemaWithValidator(BaseModel):
            model_config = ConfigDict(
                from_attributes=True,
            )

            name: str

            @field_validator("name", mode="after")
            @classmethod
            def fix_title(cls, value):
                return value.title()

        create_user_body = {
            "data": {
                "attributes": {
                    "name": "john doe",
                },
            },
        }

        if inherit:
            UserSchemaWithValidator = self.inherit(UserSchemaWithValidator)
        app = self.build_app(UserSchemaWithValidator)

        async with AsyncClient(app=app, base_url="http://test") as client:
            url = app.url_path_for(f"get_{self.resource_type}_list")
            res = await client.post(url, json=create_user_body)
            assert res.status_code == status.HTTP_201_CREATED, res.text
            res_json = res.json()

        assert res_json["data"]
        assert res_json["data"].pop("id")
        assert res_json == {
            "data": {
                "attributes": {"name": "John Doe"},
                "type": "validator",
            },
            "jsonapi": {"version": "1.0"},
            "meta": None,
        }

    @pytest.mark.parametrize(
        ("name", "expected_detail"),
        [
            pytest.param("check_pre_1", "Raised 1 pre validator", id="check_1_pre_validator"),
            pytest.param("check_pre_2", "Raised 2 pre validator", id="check_2_pre_validator"),
            pytest.param("check_post_1", "Raised 1 post validator", id="check_1_post_validator"),
            pytest.param("check_post_2", "Raised 2 post validator", id="check_2_post_validator"),
        ],
    )
    async def test_model_validator(self, name: str, expected_detail: str):
        class UserSchemaWithValidator(BaseModel):
            model_config = ConfigDict(
                from_attributes=True,
            )

            name: str

            @model_validator(mode="before")
            @classmethod
            def validator_pre_1(cls, values):
                if values["name"] == "check_pre_1":
                    msg = "Raised 1 pre validator"
                    raise ValueError(msg)

                return values

            @model_validator(mode="before")
            @classmethod
            def validator_pre_2(cls, values):
                if values["name"] == "check_pre_2":
                    msg = "Raised 2 pre validator"
                    raise ValueError(msg)

                return values

            @model_validator(mode="after")
            @classmethod
            def validator_post_1(cls, values):
                if values.name == "check_post_1":
                    msg = "Raised 1 post validator"
                    raise ValueError(msg)

                return values

            @model_validator(mode="after")
            @classmethod
            def validator_post_2(cls, values):
                if values.name == "check_post_2":
                    msg = "Raised 2 post validator"
                    raise ValueError(msg)

                return values

        create_user_body = {
            "data": {
                "attributes": {
                    "name": name,
                },
            },
        }
        await self.execute_request_twice_and_check_response(
            schema=UserSchemaWithValidator,
            body=create_user_body,
            expected_detail=expected_detail,
        )

    @pytest.mark.parametrize(
        "inherit",
        [
            pytest.param(True, id="inherited_true"),
            pytest.param(False, id="inherited_false"),
        ],
    )
    async def test_model_validator_can_change_value(self, inherit: bool):
        class UserSchemaWithValidator(BaseModel):
            model_config = ConfigDict(
                from_attributes=True,
            )

            name: str

            @model_validator(mode="after")
            @classmethod
            def fix_title(cls, value):
                value.name = value.name.title()
                return value

        create_user_body = {
            "data": {
                "attributes": {
                    "name": "john doe",
                },
            },
        }

        if inherit:
            UserSchemaWithValidator = self.inherit(UserSchemaWithValidator)
        app = self.build_app(UserSchemaWithValidator)

        async with AsyncClient(app=app, base_url="http://test") as client:
            url = app.url_path_for(f"get_{self.resource_type}_list")
            res = await client.post(url, json=create_user_body)
            assert res.status_code == status.HTTP_201_CREATED, res.text
            res_json = res.json()

        assert res_json["data"]
        assert res_json["data"].pop("id")
        assert res_json == {
            "data": {
                "attributes": {
                    "name": "John Doe",
                },
                "type": "validator",
            },
            "jsonapi": {"version": "1.0"},
            "meta": None,
        }

    @pytest.mark.parametrize(
        ("name", "expected_detail"),
        [
            pytest.param("check_pre_1", "check_pre_1", id="check_1_pre_validator"),
            pytest.param("check_pre_2", "check_pre_2", id="check_2_pre_validator"),
            pytest.param("check_post_1", "check_post_1", id="check_1_post_validator"),
            pytest.param("check_post_2", "check_post_2", id="check_2_post_validator"),
        ],
    )
    async def test_model_validator_inheritance(self, name: str, expected_detail: str):
        class UserSchemaWithValidatorBase(BaseModel):
            model_config = ConfigDict(
                from_attributes=True,
            )

            name: str

            @model_validator(mode="before")
            @classmethod
            def validator_pre_1(cls, values):
                if values["name"] == "check_pre_1":
                    msg = "Base check_pre_1"
                    raise ValueError(msg)

                return values

            @model_validator(mode="before")
            @classmethod
            def validator_pre_2(cls, values):
                if values["name"] == "check_pre_2":
                    msg = "Base check_pre_2"
                    raise ValueError(msg)

                return values

            @model_validator(mode="after")
            @classmethod
            def validator_post_1(cls, values):
                if values.name == "check_post_1":
                    msg = "Base check_post_1"
                    raise ValueError(msg)

                return values

            @model_validator(mode="after")
            @classmethod
            def validator_post_2(cls, values):
                if values.name == "check_post_2":
                    msg = "Base check_post_2"
                    raise ValueError(msg)

                return values

        class UserSchemaWithValidator(UserSchemaWithValidatorBase):
            model_config = ConfigDict(
                from_attributes=True,
            )

            name: str

            @model_validator(mode="before")
            @classmethod
            def validator_pre_1(cls, values):
                if values["name"] == "check_pre_1":
                    msg = "check_pre_1"
                    raise ValueError(msg)

                return values

            @model_validator(mode="before")
            @classmethod
            def validator_pre_2(cls, values):
                if values["name"] == "check_pre_2":
                    msg = "check_pre_2"
                    raise ValueError(msg)

                return values

            @model_validator(mode="after")
            @classmethod
            def validator_post_1(cls, values):
                if values.name == "check_post_1":
                    msg = "check_post_1"
                    raise ValueError(msg)

                return values

            @model_validator(mode="after")
            @classmethod
            def validator_post_2(cls, values):
                if values.name == "check_post_2":
                    msg = "check_post_2"
                    raise ValueError(msg)

                return values

        create_user_body = {
            "data": {
                "attributes": {
                    "name": name,
                },
            },
        }
        await self.execute_request_and_check_response(
            app=self.build_app(UserSchemaWithValidator),
            body=create_user_body,
            expected_detail=expected_detail,
        )

    async def test_validator_calls_for_field_requests(self, user_1: User):
        class UserSchemaWithValidator(BaseModel):
            model_config = ConfigDict(
                from_attributes=True,
            )

            name: str

            @field_validator("name", mode="before")
            @classmethod
            def pre_field_validator(cls, value):
                return f"{value} (pre_field)"

            @field_validator("name", mode="after")
            @classmethod
            def post_field_validator(cls, value):
                return f"{value} (post_field)"

            @model_validator(mode="before")
            @classmethod
            def pre_model_validator(cls, data: dict):
                name = data["name"]
                data["name"] = f"{name} (pre_model)"
                return data

            @model_validator(mode="after")
            @classmethod
            def post_model_validator(self, value):
                value.name = f"{value.name} (post_model)"
                return value

        params = QueryParams(
            [
                (f"fields[{self.resource_type}]", "name"),
            ],
        )

        app = self.build_app(UserSchemaWithValidator)

        async with AsyncClient(app=app, base_url="http://test") as client:
            url = app.url_path_for(f"get_{self.resource_type}_detail", obj_id=user_1.id)
            res = await client.get(url, params=params)
            assert res.status_code == status.HTTP_200_OK, res.text
            res_json = res.json()

        assert res_json["data"]
        assert res_json["data"].pop("id")
        assert res_json == {
            "data": {
                "attributes": {
                    # check validators call order
                    "name": f"{user_1.name} (pre_model) (pre_field) (post_field) (post_model)",
                },
                "type": self.resource_type,
            },
            "jsonapi": {"version": "1.0"},
            "meta": None,
        }


class TestValidationUtils:
    @pytest.mark.parametrize(
        ("include", "exclude", "expected"),
        [
            pytest.param({"item_1"}, None, {"item_1_validator"}, id="include"),
            pytest.param(None, {"item_1"}, {"item_2_validator"}, id="exclude"),
            pytest.param(None, None, {"item_1_validator", "item_2_validator"}, id="empty_params"),
            pytest.param({"item_1", "item_2"}, {"item_2"}, {"item_1_validator"}, id="intersection"),
        ],
    )
    def test_extract_field_validators_args(
        self,
        include: set[str],
        exclude: set[str],
        expected: set[str],
    ):
        class ValidationSchema(BaseModel):
            item_1: str
            item_2: str

            @field_validator("item_1", mode="after")
            @classmethod
            def item_1_validator(cls, value):
                return value

            @field_validator("item_2", mode="after")
            @classmethod
            def item_2_validator(cls, value):
                return value

        field_validators, model_validators = extract_validators(
            ValidationSchema,
            include_for_field_names=include,
            exclude_for_field_names=exclude,
        )
        assert {*field_validators.keys(), *model_validators.keys()} == expected
