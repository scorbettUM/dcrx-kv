from dcrx_kv.context.types import ContextType
from dcrx_kv.env import Env
from pydantic import BaseModel
from .connection import StorageConnection
from .queue import JobQueue



class StorageServiceContext(BaseModel):
    env: Env
    connection: StorageConnection
    queue: JobQueue
    context_type: ContextType=ContextType.STORAGE_SERVICE


    class Config:
        arbitrary_types_allowed = True

    async def initialize(self):
        await self.connection.connect()
        await self.connection.init()

    async def close(self):
        await self.connection.close()