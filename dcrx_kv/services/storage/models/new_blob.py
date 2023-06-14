from pydantic import (
    BaseModel,
    StrictStr
)
from typing import Literal


class NewBlob(BaseModel):
    data: StrictStr