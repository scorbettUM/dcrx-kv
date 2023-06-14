import sqlalchemy
import uuid
from dcrx_kv.database.table_types import TableTypes


class StorageSQLiteTable:

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
                default=lambda: str(uuid.uuid4()).encode()
            ),
            sqlalchemy.Column(
                'key',
                sqlalchemy.TEXT,
            ),
            sqlalchemy.Column(
                'namespace',
                sqlalchemy.TEXT
            ),
            sqlalchemy.Column(
                'path',
                sqlalchemy.Text,
                unique=True
            ),
            sqlalchemy.Column(
                'filename',
                sqlalchemy.TEXT
            ),
            sqlalchemy.Column(
                'content_type',
                sqlalchemy.TEXT
            ),
            sqlalchemy.Column(
                'operation_type',
                sqlalchemy.TEXT
            ),
            sqlalchemy.Column(
                'backup_type',
                sqlalchemy.TEXT
            ),
            sqlalchemy.Column(
                'encoding',
                sqlalchemy.TEXT
            ),
            sqlalchemy.Column(
                'context',
                sqlalchemy.TEXT
            ),
            sqlalchemy.Column(
                'status',
                sqlalchemy.TEXT
            ),
            sqlalchemy.Column(
                'error',
                sqlalchemy.TEXT
            )
        )

        self.columns = {
            'id': self.table.c.id,
            'key': self.table.c.key,
            'namespace': self.table.c.namespace,
            'path': self.table.c.path,
            'filename': self.table.c.filename,
            'content_type': self.table.c.content_type,
            'operation_type': self.table.c.operation_type,
            'backup_type': self.table.c.backup_type,
            'encoding': self.table.c.encoding,
            'context': self.table.c.context,
            'status': self.table.c.status,
            'error': self.table.c.error
        }

        self.types_map = {
            'id': lambda value: str(value).encode(),
            'key': lambda value: str(value),
            'namespace': lambda value: str(value),
            'path': lambda value: str(value),
            'filename': lambda value: str(value),
            'content_type': lambda value: str(value),
            'operation_type': lambda value: str(value),
            'backup_type': lambda value: str(value),
            'encoding': lambda value: str(value),
            'context': lambda value: str(value),
            'status': lambda value: str(value),
            'error': lambda value: str(value) if value else None
        }

        self.table_type = TableTypes.SQLITE
