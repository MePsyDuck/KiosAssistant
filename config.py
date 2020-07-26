import os

# Gmail config
SMTP_SERVER = 'imap.gmail.com'
SMTP_PORT = '993'
BOT_EMAIL = os.getenv('BOT_EMAIL')
BOT_PWD = os.getenv('BOT_PWD')
MAIL_LABEL = '"Form Submission Notifications"'
RESP_OK = 'OK'

# Discord config
TOKEN = os.getenv('TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
SLEEP_TIME = 30
