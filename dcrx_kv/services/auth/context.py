from dcrx_kv.context.types import ContextType
from dcrx_kv.env import Env
from pydantic import BaseModel
from .manager import AuthorizationSessionManager



class AuthServiceContext(BaseModel):
    env: Env
    manager: AuthorizationSessionManager
    context_type: ContextType=ContextType.AUTH_SERVICE

    class Config:
        arbitrary_types_allowed = True

    async def initialize(self):
        await self.manager.connect()

    async def close(self):
        await self.manager.close()