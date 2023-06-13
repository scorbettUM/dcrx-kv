import asyncio
from sqlalchemy import Table
from sqlalchemy.sql import (
    Select,
    Insert,
    Update,
    Delete
)
from sqlalchemy.schema import (
    CreateTable, 
    DropTable
)
from aiomysql.sa.engine import Engine as MySQLEngine
from aiomysql.sa import create_engine
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine as PostgresEngine,
    AsyncConnection
)
from typing import (
    Union, 
    Generic,
    TypeVar,
    List
)
from .connection_config import ConnectionConfig
from .models import DatabaseTransactionResult


T = TypeVar('T')


class DatabaseConnection(Generic[T]):

    def __init__(self, config: ConnectionConfig) -> None:
        
        self.config = config

        self.engine: Union[
            MySQLEngine,
            PostgresEngine,
            None
        ] = None

        self.connection: Union[
            AsyncConnection,
            None
        ] = None

        self.loop: Union[asyncio.AbstractEventLoop, None] = None

    def setup(self):

        if self.config.database_type == 'asyncpg':
            engine_url = ['postgresql+asyncpg://']

        elif self.config.database_type == 'sqlite':
            engine_url = ['sqlite+aiosqlite://']

        if self.config.database_username and self.config.database_password:
            engine_url.append(
                f'{self.config.database_username}:{self.config.database_password}@'
            )

        if self.config.database_port:
            engine_url.append(
                f'{self.config.database_uri}:{self.config.database_port}/{self.config.database_name}'
            )

        elif self.config.database_uri:
            engine_url.append(
                f'{self.config.database_uri}/{self.config.database_name}'
            )

        else:
            engine_url.append(
                f'/{self.config.database_name}'
            )


        engine_url = ''.join(engine_url)

        if self.engine is None and self.config.database_type == 'mysql':
            self.engine = create_engine(
                user=self.config.database_username,
                password=self.config.database_password,
                host=self.config.database_uri,
                database=self.config.database_name,
                loop=self.loop
            )

        elif self.engine is None and self.config.database_type == 'asyncpg':
            
            self.engine = create_async_engine(engine_url)

        elif self.engine is None and self.config.database_type == 'sqlite':
            self.engine = create_async_engine(engine_url)

    async def connect(self):
        self.loop = asyncio.get_event_loop()    

        if self.engine is None:
            self.setup()

    async def create_table(
        self,
        table: Table
    ) -> DatabaseTransactionResult[T]:
        
        last_error: Union[str, None]=None

        for _ in range(self.config.database_transaction_retries):
            async with self.engine.connect() as connection:
                try:
                    await connection.execute(
                        CreateTable(
                            table,
                            if_not_exists=True
                        )
                    )

                    await connection.commit()

                    return DatabaseTransactionResult(
                        message='Table created'
                    )

                except Exception as transaction_exception:
                    last_error = str(transaction_exception)
                    await connection.rollback()

                await connection.commit()
        
        return DatabaseTransactionResult(
            message='Database transaction failed',
            error=last_error
        )


    async def get(
        self, 
        statement: Select
    ) -> DatabaseTransactionResult[T]:
        
        last_error: Union[str, None]=None
        results: List[T] = []

        for _ in range(self.config.database_transaction_retries):
            async with self.engine.connect() as connection:
                
                try:

                    results: List[T] = await connection.execute(statement)
                    await connection.commit()

                    return DatabaseTransactionResult(
                        message='Records successfully retrieved',
                        data=[
                            row for row in results
                        ]
                    )
                
                except Exception as transaction_exception:
                    last_error = str(transaction_exception)
                    await connection.rollback()

                await connection.commit()
        
        return DatabaseTransactionResult(
            message='Database transaction failed',
            last_error=last_error
        )
    
    async def insert_or_update(
        self,
        statements: List[
            Union[Insert, Update]
        ]
    ) -> DatabaseTransactionResult[T]:
        
        last_error: Union[str, None]=None
        for _ in range(self.config.database_transaction_retries):
            async with self.engine.connect() as connection:
                try:
                    for statement in statements:
                        await connection.execute(statement)

                    await connection.commit()

                    return DatabaseTransactionResult(
                        message='Records successfully created or updated'
                    )

                except Exception as transaction_exception:
                    last_error = str(transaction_exception)
                    await connection.rollback()
                
                await connection.commit()
        
        return DatabaseTransactionResult(
            message='Database transaction failed',
            last_error=last_error
        )


    async def delete(
        self,
        statements: List[Delete]
    ) -> DatabaseTransactionResult[T]:
        
        last_error: Union[str, None]=None
        for _ in range(self.config.database_transaction_retries):
            async with self.engine.connect() as connection:

                try:
                    for statement in statements:
                        await connection.execute(statement)

                    await connection.commit()

                    return DatabaseTransactionResult(
                        message='Records successfully dropped'
                    )

                except Exception as transaction_exception:
                    last_error = str(transaction_exception)
                    await connection.rollback()
            
                await connection.commit()
        
        return DatabaseTransactionResult(
            message='Database transaction failed',
            last_error=last_error
        )

    async def drop_table(
        self,
        table: Table
    ) -> DatabaseTransactionResult[T]:
        
        last_error: Union[str, None]=None
        for _ in range(self.config.database_transaction_retries):

            async with self.engine.connect() as connection:
                
                try:
                    await connection.execute(
                        DropTable(
                            table,
                            if_exists=True
                        )
                    )

                    await connection.commit()

                    return DatabaseTransactionResult(
                        message='Table successfully dropped'
                    )

                except Exception as transaction_exception:
                    last_error = str(transaction_exception)
                    await connection.rollback()

                await connection.commit()
        
        return DatabaseTransactionResult(
            message='Database transaction failed',
            last_error=last_error
        )
    
    async def close(self):

        last_error: Union[str, None]=None
        for _ in range(self.config.database_transaction_retries):

            try:

                if self.connection:
                    await self.connection.close()

                return DatabaseTransactionResult(
                    message='Connection successfully closed'
                )

            except Exception as transaction_exception:
                last_error = str(transaction_exception)

        return DatabaseTransactionResult(
            message='Database transaction failed',
            last_error=last_error
        )