import asyncio
import functools
import click
import uuid
from dcrx_kv.env import load_env, Env
from dcrx_kv.services.auth.manager import AuthorizationSessionManager
from dcrx_kv.services.users.connection import UsersConnection
from dcrx_kv.services.users.models import DBUser, NewUser
from sqlalchemy_utils import database_exists, create_database
from typing import Dict, Any



async def create_user(
    user: Dict[str, Any],
    env: Env,
):

    loop = asyncio.get_event_loop()

    connection = UsersConnection(env)
    connection.setup()

    if connection.config.database_type == 'mysql':
        engine_url = ['mysql://']
        
    elif connection.config.database_type == 'asyncpg':
        engine_url = ['postgresql://']

    else:
        engine_url = ['sqlite://']

    if connection.config.database_username and connection.config.database_password:
        engine_url.append(
            f'{connection.config.database_username}:{connection.config.database_password}@'
        )

    if connection.config.database_port:
        engine_url.append(
            f'{connection.config.database_uri}:{connection.config.database_port}/{connection.config.database_name}'
        )

    elif connection.config.database_uri:
        engine_url.append(
            f'{connection.config.database_uri}/{connection.config.database_name}'
        )

    else:
        engine_url.append(
            f'/{connection.config.database_name}'
        )

    engine_url = ''.join(engine_url)

    api_database_exists = await loop.run_in_executor(
        None,
        functools.partial(
            database_exists,
            engine_url
        )
    )

    if not api_database_exists:
        await loop.run_in_executor(
            None,
            functools.partial(
                create_database,
                engine_url
            )
        )

    auth = AuthorizationSessionManager(env)
    await auth.connect()

    new_user = NewUser(
        username=user.get('username'),
        first_name=user.get('first_name'),
        last_name=user.get('last_name'),
        email=user.get('email'),
        disabled=False,
        password=user.get('password')

    )

    hashed_password = await auth.encrypt(new_user.password)

    user = DBUser(
        id=uuid.uuid4(),
        username=new_user.username,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        email=new_user.email,
        disabled=new_user.disabled,
        hashed_password=hashed_password
    )

    await connection.connect()
    await connection.init()

    users = await connection.select()

    if users.data is None or len(users.data) < 1:
        await connection.create([
            user
        ])
    
    await auth.close()
    await connection.close()


@click.group(help='Commands to migrate or initialize the database.')
def database():
    pass


@database.command(help='Initalize the database with the provided administrator.')
@click.option(
    '--username',
    help='Usename for initial admin user.'
)
@click.option(
    '--first-name',
    help='First name of initial admin user.'
)
@click.option(
    '--last-name',
    help='Last name of initial admin user.'
)
@click.option(
    '--email',
    help='Email name of initial admin user.'
)
@click.option(
    '--password',
    help='Password of initial admin user.'
)
def initialize(
    username: str,
    first_name: str,
    last_name: str,
    email: str,
    password: str
):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    env = load_env(Env.types_map())

    loop.run_until_complete(
        create_user({
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password': password
        }, env)
    )

