import urllib.parse as up

import pony

from config import DB_PROVIDER, DB_URL, DEBUG
from database.api.events import EventsDB
from database.api.messages import MessagesDB
from database.api.reminders import RemindersDB
from database.api.users import UsersDB
from database.models import db


class DatabaseAPI:
    def __init__(self):
        """Method to initialize db connection. Binds PonyORM Database object `db` to configured database.
        Creates the mapping between db tables and models.

        pros of using ths api (db_session for each call)
        * strict typing
        * well defined structure
        * logic abstraction
        * no stray operations

        cons
        * no optimal cache usage
        * most methods are just single line, superficial
        * cant rollback changes
        """
        self.db = db
        if DB_PROVIDER == 'sqlite':
            self.db.bind(provider='sqlite', filename=DB_URL, create_db=True)
        elif DB_PROVIDER == 'mysql':
            up.uses_netloc.append("mysql")
            url = up.urlparse(DB_URL)
            self.db.bind(provider='mysql', host=url.hostname, user=url.username, passwd=url.password, db=url.path[1:])
        elif DB_PROVIDER == 'postgres':
            up.uses_netloc.append("postgres")
            url = up.urlparse(DB_URL)
            self.db.bind(provider='postgres', user=url.username, password=url.password, host=url.hostname,
                         database=url.path[1:])
        else:
            self.db.bind(provider='sqlite', filename='bot.db', create_db=True)

        self.db.generate_mapping(create_tables=True)

        self.events = EventsDB(db)
        self.messages = MessagesDB(db)
        self.reminders = RemindersDB(db)
        self.users = UsersDB(db)

    def create_all_tables(self):
        """Method to create all tables defined in the models
        """
        self.db.create_tables()

    def drop_all_tables(self):
        """Method to drop all tables defined in the models
        """
        self.db.drop_all_tables(with_all_data=True)


db_api = DatabaseAPI()

if DEBUG:
    pony.options.CUT_TRACEBACK = False
