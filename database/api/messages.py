from pony.orm import db_session

from database.models import Messages, Users


class MessagesDB:
    def __init__(self, db):
        self.db = db

    @db_session
    def add(self, message_id: int, channel_id: int, user: Users):
        return Messages(id=message_id, channel_id=channel_id, user=user)

    @db_session
    def get(self, message_id: int):
        return Messages.get(id=message_id)
