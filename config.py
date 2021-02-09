import os

# Gmail config
SMTP_SERVER = 'imap.gmail.com'
SMTP_PORT = '993'
BOT_EMAIL = os.getenv('BOT_EMAIL')
BOT_PWD = os.getenv('BOT_PWD')
MAIL_LABEL = '"Form Submission Notifications"'
RESP_OK = 'OK'

# DB config
DB_URL = os.getenv('DATABASE_URL')
DB_PROVIDER = 'postgres'

# Discord config
TOKEN = os.getenv('TOKEN')
TASK_SLEEP_TIME = 60
MSG_MAX_LENGTH = 1000

# Debug
if DEBUG := os.getenv('DEBUG', '0') == '1':
    TASK_SLEEP_TIME = 10
    DB_PROVIDER = ''
    DB_URL = ''
