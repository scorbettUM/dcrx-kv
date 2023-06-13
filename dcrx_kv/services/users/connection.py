from dcrx_kv.database import (
    DatabaseConnection,
    ConnectionConfig
)
from dcrx_api.database.models import DatabaseTransactionResult
from dcrx_kv.env import Env
from typing import (
    List,
    Dict,
    Any
)
from .models import DBUser
from .table import UsersTable


class UsersConnection(DatabaseConnection[DBUser]):

    def __init__(self, env: Env) -> None:
        super().__init__(
            ConnectionConfig(
                database_username=env.DCRX_KV_DATABASE_USER,
                database_password=env.DCRX_KV_DATABASE_PASSWORD,
                database_type=env.DCRX_KV_DATABASE_TYPE,
                database_uri=env.DCRX_KV_DATABASE_URI,
                database_port=env.DCRX_KV_DATABASE_PORT,
                database_name=env.DCRX_KV_DATABASE_NAME,
                database_transaction_retries=env.DCRX_KV_DATABASE_TRANSACTION_RETRIES
            )
        )

        self.table: UsersTable[DBUser] = UsersTable(
            'users',
            database_type=self.config.database_type
        )

    async def init(self) -> DatabaseTransactionResult[DBUser]:
        return await self.create_table(self.table.selected.table)

    async def select(
        self, 
        filters: Dict[str, Any]={}
    ) -> DatabaseTransactionResult[DBUser]:
        return await self.get(
            self.table.select(
                filters={
                    name: self.table.selected.types_map.get(
                        name
                    )(value) for name, value in filters.items()
                }
            )
        )

    async def create(
        self, 
        users: List[DBUser]
    ) -> DatabaseTransactionResult[DBUser]:
       return await self.insert_or_update(
           self.table.insert(users)
       )
    
    async def update(
        self, 
        users: List[DBUser],
        filters: Dict[str, Any]={}
    ) -> DatabaseTransactionResult[DBUser]:
        return await self.insert_or_update(
            self.table.update(
                users,
                filters={
                    name: self.table.selected.types_map.get(
                        name
                    )(value) for name, value in filters.items()
                }
            )
        )
    
    async def remove(
        self,
        filters: Dict[str, Any]
    ) -> DatabaseTransactionResult[DBUser]:
        return await self.delete([
            self.table.delete({
                name: self.table.selected.types_map.get(
                    name
                )(value) for name, value in filters.items()
            })
        ])
    
    async def drop(self) -> DatabaseTransactionResult[DBUser]:
        return await self.drop_table(self.table)
    
