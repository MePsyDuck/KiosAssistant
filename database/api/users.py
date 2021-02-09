from pony.orm import db_session

from database.models import Users, Reminders, Events


class UsersDB:
    def __init__(self, db):
        self.db = db

    @db_session
    def add(self, user_id: int, timezone=None, time_format=None):
        return Users(id=user_id, timezone=timezone, time_format=time_format)

    @db_session
    def get(self, user_id: int):
        return Users.get(id=user_id)

    @db_session
    def get_or_add(self, user_id: int):
        return user if (user := Users.get(id=user_id)) else Users(id=user_id)

    @db_session
    def get_reminders(self, user_id: int, from_dt: int = None):
        if from_dt is None:
            return Users[user_id].remniders.sort_by(Reminders.scheduled_dt)
        else:
            return Users[user_id].reminders.sort_by(Reminders.scheduled_dt).filter(lambda r: r.scheduled_date >= from_dt)

    @db_session
    def get_events(self, user_id: int, from_dt: int = None):
        if from_dt is None:
            return Users[user_id].events.sort_by(Events.scheduled_dt)
        else:
            return Users[user_id].events.sort_by(Events.scheduled_dt).filter(lambda e: e.scheduled_date >= from_dt)

    @db_session
    def update(self, user_id: int, timezone: str = None, time_format: str = None):
        if timezone is not None:
            Users[user_id].timezone = timezone
        if time_format is not None:
            Users[user_id].time_format = time_format

    @db_session
    def upsert(self, user_id: int, timezone: str = None, time_format: str = None):
        if Users[user_id] is not None:
            self.update(user_id, timezone, time_format)
        else:
            self.add(user_id, timezone, time_format)
