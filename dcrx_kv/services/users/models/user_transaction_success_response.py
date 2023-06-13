from pydantic import (
    BaseModel,
    StrictStr
)


class UserTransactionSuccessResponse(BaseModel):
    message: StrictStr