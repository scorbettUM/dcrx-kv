from pydantic import (
    BaseModel,
    StrictStr
)

from typing import (
    Generic,
    Optional,
    List,
    TypeVar
)


T = TypeVar('T')


class DatabaseTransactionResult(BaseModel, Generic[T]):
    message: StrictStr
    data: Optional[List[T]]
    error: Optional[StrictStr]