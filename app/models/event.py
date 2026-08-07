from peewee import AutoField, DateTimeField, IntegerField, TextField

from app.database import BaseModel


class Event(BaseModel):
    """Analytics event tied to a URL or user."""

    id = AutoField()
    url_id = IntegerField(null=True)
    user_id = IntegerField(null=True)
    event_type = TextField()
    timestamp = DateTimeField()
    details = TextField(null=True)

    class Meta:
        table_name = "events"
