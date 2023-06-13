import json
from dcrx_kv.context.manager import context, ContextType
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware



class AuthMidlleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request, call_next):

        auth_service_context = context.get(ContextType.AUTH_SERVICE)
        users_service_context = context.get(ContextType.USERS_SERVICE)

        allowed_urls = [
            "/docs",
            "/favicon.ico",
            "/openapi.json",
            "/users/login"
        ]
        
        if request.url.path in allowed_urls:
            response = await call_next(request)
            return response


        token = request.cookies.get('X-Auth-Token')

        authorization = await auth_service_context.manager.verify_token(
            users_service_context.connection,
            token
        )

        if authorization.error:
            response = Response(
                status_code=401,
                content=json.dumps({
                    'detail': authorization.error
                })
            )

            if token:
                response.delete_cookie('X-Auth-Token')

            return response

        response = await call_next(request)
        return response