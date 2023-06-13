from pydantic import (
    BaseModel,
    StrictStr,
    StrictBool
)
from typing import Optional


class UpdatedUser(BaseModel):
    username: Optional[StrictStr]
    first_name: Optional[StrictStr]
    last_name: Optional[StrictStr]
    email: Optional[StrictStr]
    disabled: Optional[StrictBool]
    hashed_password: Optional[StrictStr]

