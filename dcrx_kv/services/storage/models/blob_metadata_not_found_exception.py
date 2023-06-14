from pydantic import BaseModel, StrictStr


class BlobMetadataNotFoundException(BaseModel):
    namespace: StrictStr
    key: StrictStr
    message: StrictStr