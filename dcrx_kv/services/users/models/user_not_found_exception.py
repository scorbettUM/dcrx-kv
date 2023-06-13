import uuid
from pydantic import (
    BaseModel,
    StrictStr
)


class UserNotFoundException(BaseModel):
    user_id: uuid.UUID
    message: StrictStr