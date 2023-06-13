from pydantic import (
    BaseModel,
    StrictStr
)


class NewBlob(BaseModel):
    key: StrictStr
    storage_resource_type: StrictStr
    storage_resource_group: StrictStr