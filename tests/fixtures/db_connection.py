from pytest_asyncio import fixture as async_fixture
from sqlalchemy.engine import make_url

from examples.api_for_sqlalchemy.models.base import Base
from examples.api_for_sqlalchemy.models.db import DB
from tests.common import sqla_uri

db = DB(
    url=make_url(sqla_uri()),
)


async def async_session_dependency():
    async with db.session_maker() as session:
        yield session


@async_fixture(scope="class")
async def async_engine():
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@async_fixture(scope="class")
async def async_session(async_engine):
    async with db.session_maker() as session:
        yield session


@async_fixture(autouse=True)
async def refresh_db(async_engine):  # F811
    async with db.engine.begin() as connector:
        for table in reversed(Base.metadata.sorted_tables):
            await connector.execute(table.delete())
