from pydantic import (
    BaseModel,
    StrictStr
)

from .base_user import BaseUser


class NewUser(BaseUser):
    password: StrictStr