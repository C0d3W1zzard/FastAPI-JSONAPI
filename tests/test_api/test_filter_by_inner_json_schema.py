from typing import ClassVar

import orjson as json
import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient

from fastapi_jsonapi.misc.sqla.generics.base import DetailViewBaseGeneric, ListViewBaseGeneric
from fastapi_jsonapi.views.utils import HTTPMethod, HTTPMethodConfig
from tests.common import is_postgres_tests
from tests.fixtures.models import Task
from tests.fixtures.views import SessionDependency, common_handler

pytestmark = pytest.mark.asyncio


class TaskJsonListView(ListViewBaseGeneric):
    method_dependencies: ClassVar[dict[HTTPMethod, HTTPMethodConfig]] = {
        HTTPMethod.ALL: HTTPMethodConfig(
            dependencies=SessionDependency,
            prepare_data_layer_kwargs=common_handler,
        ),
    }


class TaskJsonDetailView(DetailViewBaseGeneric):
    method_dependencies: ClassVar[dict[HTTPMethod, HTTPMethodConfig]] = {
        HTTPMethod.ALL: HTTPMethodConfig(
            dependencies=SessionDependency,
            prepare_data_layer_kwargs=common_handler,
        ),
    }


async def test_filter_inner_json_field(
    app: FastAPI,
    client: AsyncClient,
    task_1: Task,
    task_2: Task,
):
    query_params = {
        "filter": json.dumps(
            [
                {
                    "name": "task_ids_list_json",
                    "op": "pg_json_contains" if is_postgres_tests() else "sqlite_json_contains",
                    "val": [1, 2, 3],
                },
            ],
        ).decode(),
    }
    url = app.url_path_for("get_task_list")
    response = await client.get(url, params=query_params)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert "data" in response_data, response_data
    assert len(response_data["data"]) == 1
    assert response_data["data"][0]["id"] == f"{task_1.id}"


async def test_filter_inner_nested_json_field(
    app: FastAPI,
    client: AsyncClient,
    task_1: Task,
    task_2: Task,
):
    query_params = {
        "filter": json.dumps(
            [
                {
                    "name": "task_ids_dict_json",
                    "op": "pg_json_ilike" if is_postgres_tests() else "sqlite_json_ilike",
                    "val": ["completed", [1, 2, 3]],
                },
            ],
        ).decode(),
    }
    url = app.url_path_for("get_task_list")
    response = await client.get(url, params=query_params)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert "data" in response_data, response_data
    assert len(response_data["data"]) == 1
    assert response_data["data"][0]["id"] == f"{task_1.id}"


async def test_filter_inner_json_int_field(
    app: FastAPI,
    client: AsyncClient,
    task_1: Task,
    task_2: Task,
):
    query_params = {
        "filter": json.dumps(
            [
                {
                    "name": "task_ids_dict_json",
                    "op": "pg_json_ilike" if is_postgres_tests() else "sqlite_json_ilike",
                    "val": ["count", 1],
                },
            ],
        ).decode(),
    }
    url = app.url_path_for("get_task_list")
    response = await client.get(url, params=query_params)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert "data" in response_data, response_data
    assert len(response_data["data"]) == 1
    assert response_data["data"][0]["id"] == f"{task_1.id}"


async def test_filter_inner_json_bool_field(
    app: FastAPI,
    client: AsyncClient,
    task_1: Task,
    task_2: Task,
):
    query_params = {
        "filter": json.dumps(
            [
                {
                    "name": "task_ids_dict_json",
                    "op": "pg_json_ilike" if is_postgres_tests() else "sqlite_json_ilike",
                    "val": ["is_complete", True],
                },
            ],
        ).decode(),
    }
    url = app.url_path_for("get_task_list")
    response = await client.get(url, params=query_params)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert "data" in response_data, response_data
    assert len(response_data["data"]) == 1
    assert response_data["data"][0]["id"] == f"{task_1.id}"


if is_postgres_tests():

    async def test_filter_inner_jsonb_field(
        app: FastAPI,
        client: AsyncClient,
        task_1: Task,
        task_2: Task,
    ):
        query_params = {
            "filter": json.dumps(
                [
                    {
                        "name": "task_ids_list_jsonb",
                        "op": "pg_jsonb_contains",
                        "val": ["a", "b", "c"],
                    },
                ],
            ).decode(),
        }
        url = app.url_path_for("get_task_list")
        response = await client.get(url, params=query_params)
        response_data = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert "data" in response_data, response_data
        assert len(response_data["data"]) == 1
        assert response_data["data"][0]["id"] == f"{task_1.id}"

    async def test_filter_inner_nested_jsonb_field(
        app: FastAPI,
        client: AsyncClient,
        task_1: Task,
        task_2: Task,
    ):
        query_params = {
            "filter": json.dumps(
                [
                    {
                        "name": "task_ids_dict_jsonb",
                        "op": "pg_jsonb_ilike",
                        "val": ["completed", ["a", "b", "c"]],
                    },
                ],
            ).decode(),
        }
        url = app.url_path_for("get_task_list")
        response = await client.get(url, params=query_params)
        response_data = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert "data" in response_data, response_data
        assert len(response_data["data"]) == 1
        assert response_data["data"][0]["id"] == f"{task_1.id}"

    async def test_filter_inner_jsonb_int_field(
        app: FastAPI,
        client: AsyncClient,
        task_1: Task,
        task_2: Task,
    ):
        query_params = {
            "filter": json.dumps(
                [
                    {
                        "name": "task_ids_dict_jsonb",
                        "op": "pg_jsonb_ilike",
                        "val": ["count", 2],
                    },
                ],
            ).decode(),
        }
        url = app.url_path_for("get_task_list")
        response = await client.get(url, params=query_params)
        response_data = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert "data" in response_data, response_data
        assert len(response_data["data"]) == 1
        assert response_data["data"][0]["id"] == f"{task_1.id}"

    async def test_filter_inner_jsonb_bool_field(
        app: FastAPI,
        client: AsyncClient,
        task_1: Task,
        task_2: Task,
    ):
        query_params = {
            "filter": json.dumps(
                [
                    {
                        "name": "task_ids_dict_jsonb",
                        "op": "pg_jsonb_ilike",
                        "val": ["is_complete", True],
                    },
                ],
            ).decode(),
        }
        url = app.url_path_for("get_task_list")
        response = await client.get(url, params=query_params)
        response_data = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert "data" in response_data, response_data
        assert len(response_data["data"]) == 1
        assert response_data["data"][0]["id"] == f"{task_1.id}"
