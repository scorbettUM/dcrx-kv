from pydantic import (
    BaseModel,
    StrictStr,
    StrictInt
)


class GeneratedToken(BaseModel):
    token: StrictStr
    expiration: StrictInt