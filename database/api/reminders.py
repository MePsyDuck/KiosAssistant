from datetime import datetime

from pony.orm import db_session

from database.models import Reminders
from util.datetime_util import utc_now


class RemindersDB:
    def __init__(self, db):
        self.db = db

    @db_session
    def add(self, for_message_id: int, reminder_datetime: datetime, info: str = None):
        return Reminders(for_message=for_message_id, info=info, scheduled_dt=reminder_datetime)

    @db_session
    def get(self, reminder_id: int):
        return Reminders.get(id=reminder_id)

    @db_session
    def get_current(self):
        n = utc_now()
        return Reminders.select(lambda r: r.scheduled_dt <= n)

    @db_session
    def delete(self, reminder_id: int):
        if (reminder := Reminders.get(id=reminder_id)) is not None:
            reminder.delete()

    @db_session
    def delete_for_user(self, user_id: int):
        Reminders.select(lambda r: r.for_message.user.id == user_id).delete(bulk=True)
