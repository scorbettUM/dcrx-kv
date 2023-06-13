from pydantic import (
    BaseModel,
    StrictStr
)


class AuthenticationFailureException(BaseModel):
    detail: StrictStr