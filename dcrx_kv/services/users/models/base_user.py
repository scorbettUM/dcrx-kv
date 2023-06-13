from pydantic import (
    BaseModel,
    StrictStr,
    StrictBool
)


class BaseUser(BaseModel):
    username: StrictStr
    first_name: StrictStr
    last_name: StrictStr
    email: StrictStr
    disabled: StrictBool

