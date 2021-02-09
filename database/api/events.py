from datetime import datetime

from pony.orm import db_session

from database.models import Events
from util.datetime_util import utc_now


class EventsDB:
    def __init__(self, db):
        self.db = db

    @db_session
    def add(self, author_message_id: int, event_message_id: int, event_name: str, event_datetime: datetime):
        return Events(author_message=author_message_id, event_message=event_message_id, name=event_name, scheduled_dt=event_datetime)

    @db_session
    def get(self, event_id: int):
        return Events.get(id=event_id)

    @db_session
    def get_current(self):
        return Events.select(lambda e: e.scheduled_dt <= utc_now())

    @db_session
    def delete(self, event_id: int):
        if (event := Events.get(id=event_id)) is not None:
            event.delete()

    @db_session
    def delete_for_user(self, user_id: int):
        Events.select(lambda e: e.author_message.user.id == user_id).delete(bulk=True)
