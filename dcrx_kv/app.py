from fastapi import FastAPI
from dcrx_kv.services.storage.service import storage_router
from dcrx_kv.services.users.service import users_router
from dcrx_kv.lifespan import lifespan
from dcrx_kv.middleware.auth_middleware import AuthMidlleware


app = FastAPI(lifespan=lifespan)
app.include_router(storage_router)
app.include_router(users_router)
app.add_middleware(AuthMidlleware)