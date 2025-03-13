from collections.abc import AsyncIterator
from typing import Union

from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


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
