import asyncio
import base64
import datetime
import functools
from concurrent.futures import ThreadPoolExecutor
from cryptography.fernet import Fernet
from dcrx_kv.env import Env
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
from passlib.context import CryptContext
from typing import (
    Optional,
    Dict,
    Any,
    List,
    Union
)
from dcrx_kv.env.time_parser import TimeParser
from dcrx_kv.services.users.connection import UsersConnection
from dcrx_kv.services.users.models import (
    DBUser,
    LoginUser
)
from .models import (
    AuthResponse,
    AuthClaims,
    GeneratedToken
)


class AuthorizationSessionManager:

    def __init__(self, env: Env) -> None:

        self.pool_size = env.DCRX_KV_STORAGE_WORKERS
        self.context = CryptContext(
            schemes=["bcrypt"], 
            deprecated="auto"
        )

        self.scheme = OAuth2PasswordBearer(tokenUrl="token")
        self.secret_key = env.DCRX_KV_SECRET_KEY
        self.auth_algorithm = env.DCRX_KV_AUTH_ALGORITHM
        self.token_expiration_time = TimeParser(env.DCRX_KV_TOKEN_EXPIRATION).time

        self._executor: Union[ThreadPoolExecutor, None] = None
        self._loop: Union[asyncio.AbstractEventLoop, None] = None

        fernet_key = base64.urlsafe_b64encode(
            self.secret_key.encode().ljust(32)[:32]
        )

        self._encrypter = Fernet(fernet_key)

    async def connect(self):
        self._loop = asyncio.get_event_loop()
        self._executor = ThreadPoolExecutor(max_workers=self.pool_size)

    async def encrypt(self, password: str):
        return await self._loop.run_in_executor(
            self._executor,
            functools.partial(
                self.context.hash,
                password
            )
        )
    
    async def encrypt_fernet(self, password: str):
        encrypted_password = await self._loop.run_in_executor(
            self._executor,
            functools.partial(
                self._encrypter.encrypt,
                password.encode()
            )
        )

        return encrypted_password.decode()
    
    async def decrypt_fernet(self, password: str):
        decrypted_password = await self._loop.run_in_executor(
            self._executor,
            functools.partial(
                self._encrypter.decrypt,
                password.encode()
            )
        )

        return decrypted_password.decode()

    async def authenticate_user(
        self,
        db_connection: UsersConnection,
        username: str, 
        password: str
    ) -> Union[DBUser, None]:
        users = await db_connection.select(
            filters={
                'username': username
            }
        )

        if users.data is None or len(users.data) < 1:
            return AuthResponse(
                error='User authorization failed',
                message='Authentication failed'
            )
        
        user = users.data.pop()
        
        password_verified = await self._loop.run_in_executor(
            self._executor,
            functools.partial(
                self.context.verify,
                password, 
                user.hashed_password
            )
        )

        if password_verified is False:
            return AuthResponse(
                error='User authorization failed',
                message='Authentication failed'
            )
        
        
        return user
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[datetime.datetime]=None
    ):

        to_encode = data.copy()

        expiration: datetime.datetime = datetime.datetime.utcnow() + expires_delta

        to_encode.update({
            "exp": expiration
        })

        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key, 
            algorithm=self.auth_algorithm
        )

        return GeneratedToken(
            token=encoded_jwt,
            expiration=int(expiration.timestamp()/10**7)
        )
    
    async def generate_token(
        self,
        db_connection: UsersConnection,
        login_user: LoginUser
    ) -> AuthResponse:
        user = await self.authenticate_user(
            db_connection, 
            login_user.username, 
            login_user.password
        )

        if isinstance(user, AuthResponse):
            return user

        access_token_expires = datetime.timedelta(
            seconds=self.token_expiration_time
        )
        
        auth_token = self.create_access_token(
            data={
                "sub": user.username
            }, 
            expires_delta=access_token_expires
        )

        return AuthResponse(
            message='Loggin success',
            token=auth_token.token,
            token_expires=auth_token.expiration
        )
    
    async def verify_token(
        self,
        connection: UsersConnection,
        token: Union[str, None]
    ):

        try:

            if token is None:
                return AuthResponse(
                    error='No token provided',
                    message='Authentication failed'
                )
            
            scheme, value = get_authorization_scheme_param(token)
            if scheme.lower() != 'bearer':
                return AuthResponse(
                    error='User authorization failed',
                    message='Authentication failed'
                )

            payload = await self._loop.run_in_executor(
                self._executor,
                functools.partial(
                    jwt.decode,
                    value, 
                    self.secret_key, 
                    algorithms=[self.auth_algorithm]
                )
            )

            username: str = payload.get("sub")
            if username is None:
                return AuthResponse(
                    error='User authorization failed',
                    message='Authentication failed'
                )
            
            token_data = AuthClaims(username=username)

        except JWTError as validation_error:
            return AuthResponse(
                    error=str(validation_error),
                    message='Authentication failed'
                )
        
        users = await connection.select(
            filters={
                'username': token_data.username
            }
        )

        if users.data is None or len(users.data) < 1:
            return AuthResponse(
                error='User authorization failed',
                message='Authentication failed'
            )
        
        return AuthResponse(
            message='OK'
        )
    
    async def close(self):
        self._executor.shutdown(cancel_futures=True)