import sqlalchemy
import uuid
from dcrx_api.database.table_types import TableTypes


class UsersMySQLTable:

    def __init__(
        self, 
        users_table_name: str
    ) -> None:
        self.table = sqlalchemy.Table(
            users_table_name,
            sqlalchemy.MetaData(),
            sqlalchemy.Column(
                'id', 
                sqlalchemy.String(36),
                primary_key=True,
                default=uuid.uuid4
            ),
            sqlalchemy.Column(
                'username',
                sqlalchemy.TEXT
            ),
            sqlalchemy.Column(
                'first_name',
                sqlalchemy.TEXT
            ),
            sqlalchemy.Column(
                'last_name',
                sqlalchemy.TEXT
            ),
            sqlalchemy.Column(
                'email',
                sqlalchemy.TEXT
            ),
            sqlalchemy.Column(
                'disabled',
                sqlalchemy.BOOLEAN
            ),
            sqlalchemy.Column(
                'hashed_password',
                sqlalchemy.TEXT
            )
        )

        self.columns = {
            'id': self.table.c.id,
            'username': self.table.c.username,
            'first_name': self.table.c.first_name,
            'last_name': self.table.c.last_name,
            'email': self.table.c.email,
            'disable': self.table.c.disabled,
            'hashed_password': self.table.c.hashed_password
        }

        self.types_map = {
            'id': lambda value: str(value),
            'username': lambda value: str(value),
            'first_name': lambda value: str(value),
            'last_name': lambda value: str(value),
            'email': lambda value: str(value),
            'disabled': lambda value: bool(value),
            'hashed_password': lambda value: str(value)
        }

        self.table_type = TableTypes.MYSQL

