from peewee import DateTimeField, IntegerField, TextField

from app.database import BaseModel


class Event(BaseModel):
    id = IntegerField(primary_key=True)
    url_id = IntegerField(null=True)
    user_id = IntegerField(null=True)
    event_type = TextField()
    timestamp = DateTimeField()
    details = TextField(null=True)

    class Meta:
        table_name = "events"
