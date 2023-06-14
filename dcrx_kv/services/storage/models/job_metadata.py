import uuid
from pydantic import (
    BaseModel,
    StrictStr
)
from typing import Optional, Literal


class JobMetadata(BaseModel):
    id: uuid.UUID
    key: StrictStr
    namespace: StrictStr
    filename: StrictStr
    path: StrictStr
    content_type: StrictStr='application/octet-stream'
    operation_type: Literal[
        "upload", 
        "download", 
        "list", 
        "delete"
    ]="list"
    backup_type: Literal["disk", "aws", "gcs", "azure"]='disk'
    encoding: StrictStr='utf-8'
    context: StrictStr
    status: StrictStr
    error: Optional[StrictStr]