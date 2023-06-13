from contextlib import asynccontextmanager
from fastapi import FastAPI
from dcrx_kv.services.auth.context import (
    AuthorizationSessionManager,
    AuthServiceContext
)
from dcrx_kv.services.users.context import (
    UsersConnection,
    UsersServiceContext
)
from dcrx_kv.services.monitoring.context import (
    CPUMonitor,
    MemoryMonitor,
    MonitoringServiceContext
)

from dcrx_kv.context.manager import context
from .env import load_env, Env


@asynccontextmanager
async def lifespan(app: FastAPI):

    env = load_env(Env.types_map())

    auth_service_context = AuthServiceContext(
        env=env,
        manager=AuthorizationSessionManager(env)
    )

    monitoring_service_context = MonitoringServiceContext(
        env=env,
        monitor_name='dcrx.main',
        cpu=CPUMonitor(),
        memory=MemoryMonitor()
    )

    users_service_context = UsersServiceContext(
        env=env,
        connection=UsersConnection(env)
    )

    await context.initialize([
        auth_service_context,
        monitoring_service_context,
        users_service_context
    ])

    yield

    await context.close()