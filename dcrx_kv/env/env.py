import psutil
from pydantic import (
    BaseModel,
    StrictStr,
    StrictInt,
    StrictFloat
)
from typing import (
    Optional, 
    Dict, 
    Union,
    Callable
)


PrimaryType = Union[str, int, float, bytes, bool]


class Env(BaseModel):
    DCRX_KV_MAX_MEMORY_PERCENT_USAGE: StrictFloat=50
    DCRX_KV_STORAGE_UPLOAD_TIMEOUT: StrictStr='10m'
    DCRX_KV_STORAGE_DOWNLOAD_TIMEOUT: StrictStr='10m'
    DCRX_KV_STORAGE_PRUNE_INTERVAL: StrictStr='1s'
    DCRX_KV_STORAGE_BLOB_MAX_AGE: StrictStr='10m'
    DCRX_KV_STORAGE_WORKERS: StrictInt=25
    DCRX_KV_STORAGE_MAX_PENDING_WAIT: StrictStr='10m'
    DCRX_KV_STORAGE_MAX_PENDING: StrictInt=100
    DCRX_KV_STORAGE_POOL_SIZE: StrictInt=10
    DCRX_KV_SECRET_KEY: StrictStr
    DCRX_KV_AUTH_ALGORITHM: StrictStr='HS256'
    DCRX_KV_TOKEN_EXPIRATION: StrictStr='15m'
    DCRX_KV_DATABASE_TRANSACTION_RETRIES: StrictInt=3
    DCRX_KV_DATABASE_TYPE: Optional[StrictStr]='sqlite'
    DCRX_KV_DATABASE_USER: Optional[StrictStr]
    DCRX_KV_DATABASE_URI: Optional[StrictStr]
    DCRX_KV_DATABASE_PORT: Optional[StrictInt]
    DCRX_KV_DATABASE_PASSWORD: Optional[StrictStr]
    DCRX_KV_DATABASE_NAME: StrictStr='dcrx'

    @classmethod
    def types_map(self) -> Dict[str, Callable[[str], PrimaryType]]:
        return {
            'DCRX_KV_MAX_MEMORY_PERCENT_USAGE': float,
            'DCRX_KV_STORAGE_PRUNE_INTERVAL': str,
            'DCRX_KV_STORAGE_UPLOAD_TIMEOUT': str,
            'DCRX_KV_STORAGE_DOWNLOAD_TIMEOUT': str,
            'DCRX_KV_STORAGE_BLOB_MAX_AGE': str,
            'DCRX_KV_STORAGE_WORKERS': int,
            'DCRX_KV_STORAGE_MAX_PENDING_WAIT': str,
            'DCRX_KV_STORAGE_MAX_PENDING': int,
            'DCRX_KV_STORAGE_POOL_SIZE': int,
            'DCRX_KV_SECRET_KEY': str,
            'DCRX_KV_AUTH_ALGORITHM': str,
            'DCRX_KV_TOKEN_EXPIRATION': str,
            'DCRX_KV_DATABASE_TRANSACTION_RETRIES': int,
            'DCRX_KV_DATABASE_TYPE': str,
            'DCRX_KV_DATABASE_USER': str,
            'DCRX_KV_DATABASE_PASSWORD': str,
            'DCRX_KV_DATABASE_NAME': str,
            'DCRX_KV_DATABASE_URI': str,
            'DCRX_KV_DATABASE_PORT': int
        }