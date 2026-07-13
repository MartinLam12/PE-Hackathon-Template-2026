from peewee import DateTimeField, IntegerField, Model, TextField

from app.database import BaseModel


class User(BaseModel):
    id = IntegerField(primary_key=True)
    username = TextField()
    email = TextField()
    created_at = DateTimeField()

    class Meta:
        table_name = "users"
