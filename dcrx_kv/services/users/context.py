from dcrx_kv.context.types import ContextType
from dcrx_kv.env import Env
from pydantic import BaseModel
from .connection import UsersConnection



class UsersServiceContext(BaseModel):
    env: Env
    connection: UsersConnection
    context_type: ContextType=ContextType.USERS_SERVICE


    class Config:
        arbitrary_types_allowed = True

    async def initialize(self):
        await self.connection.connect()
        await self.connection.init()

    async def close(self):
        await self.connection.close()