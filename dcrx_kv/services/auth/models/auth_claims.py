from pydantic import (
    BaseModel,
    StrictStr
)


class AuthClaims(BaseModel):
    username: StrictStr