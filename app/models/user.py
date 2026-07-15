from peewee import AutoField, DateTimeField, TextField

from app.database import BaseModel


class User(BaseModel):
    id = AutoField()
    username = TextField()
    email = TextField()
    created_at = DateTimeField()

    class Meta:
        table_name = "users"
