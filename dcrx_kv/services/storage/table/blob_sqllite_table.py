import sqlalchemy
import uuid
from dcrx_kv.database.table_types import TableTypes


class BlobSQLiteTable:

    def __init__(
        self, 
        users_table_name: str
    ) -> None:
        self.table = sqlalchemy.Table(
            users_table_name,
            sqlalchemy.MetaData(),
            sqlalchemy.Column(
                'id', 
                sqlalchemy.BLOB,
                primary_key=True,
                default=uuid.uuid4
            ),
            sqlalchemy.Column(
                'key',
                sqlalchemy.TEXT
            ),
            sqlalchemy.Column(
                'storage_resource_type',
                sqlalchemy.TEXT
            ),
            sqlalchemy.Column(
                'storage_resource_group',
                sqlalchemy.TEXT
            )
        )

        self.columns = {
            'id': self.table.c.id,
            'key': self.table.c.username,
            'storage_resource_type': self.table.c.first_name,
            'storage_resource_group': self.table.c.last_name
        }

        self.types_map = {
            'id': lambda value: str(value),
            'key': lambda value: str(value),
            'storage_resource_type': lambda value: str(value),
            'storage_resource_group': lambda value: str(value)
        }

        self.table_type = TableTypes.SQLITE
