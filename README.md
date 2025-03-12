[![Last Commit](https://img.shields.io/github/last-commit/mts-ai/FastAPI-JSONAPI?style=for-the-badge)](https://github.com/mts-ai/FastAPI-JSONAPI)
[![PyPI](https://img.shields.io/pypi/v/fastapi-jsonapi?label=PyPI&style=for-the-badge)](https://pypi.org/project/FastAPI-JSONAPI/)
[![](https://img.shields.io/pypi/pyversions/FastAPI-JSONAPI?style=for-the-badge)](https://pypi.org/project/FastAPI-JSONAPI/)
[![](https://img.shields.io/github/license/ycd/manage-fastapi?style=for-the-badge)](https://pypi.org/project/FastAPI-JSONAPI/)
[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/mts-ai/FastAPI-JSONAPI/testing.yml?style=for-the-badge)](https://github.com/mts-ai/FastAPI-JSONAPI/actions)
[![Read the Docs](https://img.shields.io/readthedocs/fastapi-jsonapi?style=for-the-badge)](https://fastapi-jsonapi.readthedocs.io/en/latest/)
[![Codecov](https://img.shields.io/codecov/c/github/mts-ai/FastAPI-JSONAPI?style=for-the-badge)](https://codecov.io/gh/mts-ai/FastAPI-JSONAPI)

[![📖 Docs (gh-pages)](https://github.com/mts-ai/FastAPI-JSONAPI/actions/workflows/documentation.yaml/badge.svg)](https://mts-ai.github.io/FastAPI-JSONAPI/)


# FastAPI-JSONAPI

FastAPI-JSONAPI is a FastAPI extension for building REST APIs.
Implementation of a strong specification [JSONAPI 1.0](http://jsonapi.org/).
This framework is designed to quickly build REST APIs and fit the complexity
of real life projects with legacy data and multiple data storages.

## Architecture

![docs/img/schema.png](docs/img/schema.png)

## Install

```bash
pip install FastAPI-JSONAPI
```

## A minimal API

Create a test.py file and copy the following code into it

```python
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, ClassVar, Optional
from typing import Union

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.responses import ORJSONResponse as JSONResponse
from pydantic import ConfigDict
from sqlalchemy.engine import URL
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fastapi_jsonapi import ApplicationBuilder
from fastapi_jsonapi.misc.sqla.generics.base import ViewBaseGeneric
from fastapi_jsonapi.schema_base import BaseModel
from fastapi_jsonapi.views import ViewBase, Operation, OperationConfig

CURRENT_DIR = Path(__file__).resolve().parent
sys.path.append(f"{CURRENT_DIR.parent.parent}")


class DB:
    def __init__(
        self,
        url: Union[str, URL],
        echo: bool = False,
        echo_pool: bool = False,
    ):
        self.engine: AsyncEngine = create_async_engine(
            url=url,
            echo=echo,
            echo_pool=echo_pool,
        )

        self.session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
            autocommit=False,
            bind=self.engine,
            expire_on_commit=False,
        )

    async def dispose(self):
        await self.engine.dispose()

    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self.session_maker() as session:
            yield session


db = DB(
    url=make_url(f"sqlite+aiosqlite:///{CURRENT_DIR}/db.sqlite3"),
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]]


class UserSchema(BaseModel):
    """User base schema."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    name: str


class SessionDependency(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    session: AsyncSession = Depends(db.session)


def session_dependency_handler(view: ViewBase, dto: SessionDependency) -> dict[str, Any]:
    return {
        "session": dto.session,
    }


class UserView(ViewBaseGeneric):
    operation_dependencies: ClassVar = {
        Operation.ALL: OperationConfig(
            dependencies=SessionDependency,
            prepare_data_layer_kwargs=session_dependency_handler,
        ),
    }


def add_routes(app: FastAPI):
    builder = ApplicationBuilder(app)
    builder.add_resource(
        path="/users",
        tags=["User"],
        view=UserView,
        schema=UserSchema,
        model=User,
        resource_type="user",
    )
    builder.initialize()


# noinspection PyUnusedLocal
@asynccontextmanager
async def lifespan(app: FastAPI):
    add_routes(app)

    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await db.dispose()


app = FastAPI(
    title="FastAPI and SQLAlchemy",
    lifespan=lifespan,
    debug=True,
    default_response_class=JSONResponse,
    docs_url="/docs",
    openapi_url="/openapi.json",
)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
    )
```

This example provides the following API structure:

| URL                | method | endpoint    | Usage                         |
|--------------------|--------|-------------|-------------------------------|
| `/users/`          | GET    | user_list   | Get a collection of users     |
| `/users/`          | POST   | user_list   | Create a user                 |
| `/users/`          | DELETE | user_list   | Delete users                  |
| `/users/{obj_id}/` | GET    | user_detail | Get user details              |
| `/users/{obj_id}/` | PATCH  | user_detail | Update a user                 |
| `/users/{obj_id}/` | DELETE | user_detail | Delete a user                 |
| `/operations/`     | POST   | atomic      | Create, update, delete users  |
