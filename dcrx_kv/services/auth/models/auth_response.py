from pydantic import (
    BaseModel,
    StrictStr,
    StrictInt
)
from typing import Optional


class AuthResponse(BaseModel):
    error: Optional[StrictStr]
    message: StrictStr
    token: Optional[StrictStr]
    token_expires: Optional[StrictInt]