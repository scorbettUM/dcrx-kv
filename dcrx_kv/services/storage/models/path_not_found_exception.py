from pydantic import BaseModel, StrictStr


class PathNotFoundException(BaseModel):
    namespace: StrictStr
    key: StrictStr
    message: StrictStr