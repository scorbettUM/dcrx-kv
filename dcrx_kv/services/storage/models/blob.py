from pydantic import (
    BaseModel,
    StrictStr,
    StrictBytes
)
from typing import Optional, Literal


class Blob(BaseModel):
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
    data: Optional[StrictBytes]
    error: Optional[StrictStr]
    encoding: StrictStr='utf-8'
    backup_type: Literal["disk", "aws", "gcs", "azure"]='disk'