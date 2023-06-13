import uuid
from dcrx_kv.services.auth.models import AuthenticationFailureException
from dcrx_kv.context.manager import context, ContextType
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Literal
from .models import (
    AuthorizedUser,
    DBUser,
    LoginUser,
    NewUser,
    UpdatedUser,
    UserNotFoundException,
    UserTransactionSuccessResponse,
)

users_router = APIRouter()


@users_router.post(
    '/users/login',
    responses={
        401: {
            "model": AuthenticationFailureException
        }
    }
)
async def login_user(user: LoginUser) -> UserTransactionSuccessResponse:

    users_service_context = context.get(ContextType.USERS_SERVICE)
    auth_service_context = context.get(ContextType.AUTH_SERVICE)

    authorization = await auth_service_context.manager.generate_token(
        users_service_context.connection,
        user
    )

    if authorization.error:
        raise HTTPException(401, detail=authorization.error)
    
    success_response = UserTransactionSuccessResponse(
        message='User logged in.'
    )

    response = JSONResponse(
        content=success_response.dict()
    )

    response.set_cookie(
        key='X-Auth-Token',
        value=f'Bearer {authorization.token}',
        expires=authorization.token_expires
    )


    return response


@users_router.get(
    '/users/{user_id_or_name}/get',
    responses={
        401: {
            "model": AuthenticationFailureException
        },
        404: {
            "model": UserNotFoundException
        }
    }
)
async def get_user(
    user_id_or_name: str, 
    match_by: Literal["id", "username"]="id"
) -> AuthorizedUser:

    users_service_context = context.get(ContextType.USERS_SERVICE)

    filters = {
        'id': user_id_or_name
    }

    if match_by == 'username':
        filters = {
            'username': user_id_or_name
        }

    users = await users_service_context.connection.select(
        filters=filters
    )

    if len(users) < 1:
        raise HTTPException(404, detail=f'User {user_id_or_name} not found.')
    
    user = users.pop()
    
    return AuthorizedUser(
        id=user.id,
        username=user.username
    )


@users_router.post(
    '/users/create',
    status_code=201,
    responses={
        401: {
            "model": AuthenticationFailureException
        }
    }
)
async def create_user(user: NewUser) -> UserTransactionSuccessResponse:

    users_service_context = context.get(ContextType.USERS_SERVICE)
    auth_service_context = context.get(ContextType.AUTH_SERVICE)

    hashed_password = await auth_service_context.manager.encrypt(user.password)

    await users_service_context.connection.create([
        DBUser(
            id=uuid.uuid4(),
            hashed_password=hashed_password,
            **user.dict(exclude={"password"})
        )
    ])

    return UserTransactionSuccessResponse(
        message='Created user.'
    )


@users_router.put(
    '/users/update',
    status_code=202,
    responses={
        401: {
            "model": AuthenticationFailureException
        }
    }
)
async def update_user(user: UpdatedUser) -> UserTransactionSuccessResponse:

    users_service_context = context.get(ContextType.USERS_SERVICE)

    await users_service_context.connection.update([
        user
    ])

    return UserTransactionSuccessResponse(
        message='Updated user.'
    )


@users_router.delete(
    '/users/{user_id}/delete',
    status_code=200,
    responses={
        401: {
            "model": AuthenticationFailureException
        }
    }
)
async def delete_user(user_id: str) -> UserTransactionSuccessResponse:

    users_service_context = context.get(ContextType.USERS_SERVICE)

    await users_service_context.connection.remove(
        filters={
            'id': user_id
        }
    )

    return UserTransactionSuccessResponse(
        message='Deleted user.'
    )