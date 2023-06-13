import uuid
from pydantic import (
    BaseModel,
    StrictStr
)


class Blob(BaseModel):
    id: uuid.UUID
    key: StrictStr
    storage_resource_type: StrictStr
    storage_resource_group: StrictStr