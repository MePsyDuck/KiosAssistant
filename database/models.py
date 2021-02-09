from datetime import datetime

from pony.orm import Database, PrimaryKey, Required, Optional, Set

db = Database()


class Users(db.Entity):
    id = PrimaryKey(int, size=64)
    timezone = Optional(str, max_len=100, nullable=True)
    time_format = Optional(str, max_len=100, nullable=True)
    messages = Set(lambda: Messages, cascade_delete=True)


class Messages(db.Entity):
    id = PrimaryKey(int, size=64)
    channel_id = Required(int, size=64, nullable=False)
    user = Required(Users, cascade_delete=False, nullable=False)
    event_command = Optional(lambda: Events, cascade_delete=True, nullable=True)
    event_reply = Optional(lambda: Events, cascade_delete=True, nullable=True)
    reminder = Optional(lambda: Reminders, cascade_delete=True, nullable=True)


class Events(db.Entity):
    id = PrimaryKey(int, auto=True)
    author_message = Required(Messages, unique=True, cascade_delete=True, reverse="event_command", nullable=False)
    event_message = Required(Messages, unique=True, cascade_delete=True, reverse="event_reply", nullable=False)
    name = Required(str, max_len=500, nullable=True)
    scheduled_dt = Required(datetime, nullable=False)


class Reminders(db.Entity):
    id = PrimaryKey(int, auto=True)
    for_message = Required(Messages, unique=True, cascade_delete=True, nullable=False)
    info = Optional(str, max_len=1000, nullable=True)
    scheduled_dt = Required(datetime, nullable=False)
