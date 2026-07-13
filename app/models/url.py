from peewee import BooleanField, DateTimeField, IntegerField, TextField

from app.database import BaseModel


class ShortURL(BaseModel):
    id = IntegerField(primary_key=True)
    user_id = IntegerField(null=True)
    short_code = TextField(unique=True)
    original_url = TextField()
    title = TextField(null=True)
    is_active = BooleanField(default=True)
    created_at = DateTimeField()
    updated_at = DateTimeField()

    class Meta:
        table_name = "urls"
