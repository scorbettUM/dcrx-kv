from pydantic import BaseModel
from sqlalchemy.sql import (
    Select,
    Insert,
    Update,
    Delete
)
from typing import (
    Literal, 
    Dict, 
    List,
    Any,
    Union,
    Callable,
    Optional,
    TypeVar,
    Generic
)
from .storage_mysql_table import StorageMySQLTable
from .storage_postgres_table import StoragePostgresMySQLTable
from .storage_sqllite_table import StorageSQLiteTable

M = TypeVar('M', bound=BaseModel)

class StorageTable(Generic[M]):

    def __init__(
        self,
        users_table_name: str,
        database_type: Literal["mysql", "postgres", "sqlite"]="sqlite"
    ) -> None:
        self._table_types: Dict[
            Literal["mysql", "postgres", "sqlite"],
            Callable[
                [str],
                Union[
                    StorageMySQLTable,
                    StoragePostgresMySQLTable,
                    StorageSQLiteTable
                ]
            ]
        ] = {
            'mysql': lambda table_name: StorageMySQLTable(table_name),
            'postgres': lambda table_name: StoragePostgresMySQLTable(table_name),
            'sqlite': lambda table_name: StorageSQLiteTable(table_name)
        }

        self.selected: Union[
            StorageMySQLTable,
            StoragePostgresMySQLTable,
            StorageSQLiteTable
        ] = self._table_types.get(
            database_type,
            StorageMySQLTable
        )(users_table_name)

    def select(
        self, 
        filters: Optional[Dict[str, Any]]={}
    ) -> Select:

        select_clause: Select = self.selected.table.select()

        if filters:
            for field_name, value in filters.items():
                select_clause = select_clause.where(
                    self.selected.columns.get(field_name) == self.selected.types_map.get(
                        field_name
                    )(value)
                )

        return select_clause
    
    def insert(
        self,
        blobs: List[M]
    ) -> List[Insert]:
        
        return [
            self.selected.table.insert().values({
                name: self.selected.types_map.get(
                    name
                )(value) for name, value in blob.dict().items()
            }) for blob in blobs
        ]
    
    def update(
        self,
        users: List[M],
        filters: Optional[Dict[str, Any]]={}
    ) -> List[Update]:
        
        updates: List[Update] = []

        for user in users:

            update_clause: Update = self.selected.table.update()


            for field_name, value in filters.items():
                update_clause = update_clause.where(
                    self.selected.columns.get(field_name) == self.selected.types_map.get(
                        field_name
                    )(value)
                )

            update_clause = update_clause.values({
                name: self.selected.types_map.get(
                    name
                )(value) for name, value in user.dict(  
                    exclude_none=True,
                    exclude_unset=True
                ).items()
            })
            updates.append(update_clause)

        return updates
    
    def delete(
        self,
        filters: Dict[str, Any]
    ) -> List[Delete]:
        
        delete_clause: Delete = self.selected.table.delete()

        if filters:
            for field_name, value in filters.items():
                delete_clause = delete_clause.where(
                    self.selected.columns.get(field_name) == self.selected.types_map.get(
                        field_name
                    )(value)
                )

        return delete_clause
        
