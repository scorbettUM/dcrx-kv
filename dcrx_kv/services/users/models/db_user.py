import uuid
from pydantic import StrictStr
from .base_user import BaseUser


class DBUser(BaseUser):
    id: uuid.UUID
    hashed_password: StrictStr
