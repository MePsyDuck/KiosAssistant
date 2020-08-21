import os

# Gmail config
SMTP_SERVER = 'imap.gmail.com'
SMTP_PORT = '993'
BOT_EMAIL = os.getenv('BOT_EMAIL')
BOT_PWD = os.getenv('BOT_PWD')
MAIL_LABEL = '"Form Submission Notifications"'
RESP_OK = 'OK'

# Heroku config
DATABASE_URL = os.environ['DATABASE_URL']

# Discord config
TOKEN = os.getenv('TOKEN')
CAPTAINS_CHANNEL_ID = 708609781610315807
EVENTS_CHANNEL_ID = 623521212676440074
ROLES_CHANNEL_ID = 692447219575685140
SLEEP_TIME = 60

# Guild config
EVENT_REMINDER_TIMEOUT = 120
EVENT_EMOJI = 'KiosAcademy'

# Debug
if DEBUG := os.getenv('DEBUG', '0') == '1':
    EVENTS_CHANNEL_ID = 739549756019179601
    SLEEP_TIME = 10
    EVENT_EMOJI = 'psy'
