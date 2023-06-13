from pydantic import (
    BaseModel,
    StrictStr
)


class LoginUser(BaseModel):
    username: StrictStr
    password: StrictStr
