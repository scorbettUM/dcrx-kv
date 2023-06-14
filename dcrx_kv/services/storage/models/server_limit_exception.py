from pydantic import (
    BaseModel,
    StrictFloat,
    StrictInt,
    StrictStr
)

from typing import Union


class ServerLimitException(BaseModel):
    message: StrictStr
    limit: Union[StrictInt, StrictFloat]
    current: Union[StrictFloat, StrictInt]