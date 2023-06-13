from pydantic import (
    BaseModel,
    StrictStr,
    StrictBytes
)
from typing import Union


class AuthorizedUser(BaseModel):
    id: Union[StrictStr, StrictBytes]
    username: StrictStr