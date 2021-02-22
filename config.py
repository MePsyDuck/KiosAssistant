import os

from dotenv import load_dotenv

load_dotenv()

# Gmail config
BOT_EMAIL = os.getenv('BOT_EMAIL')
BOT_PWD = os.getenv('BOT_PWD')

# DB config
DB_URL = 'sqlite://database/bot.db'

# Discord config
TOKEN = os.getenv('TOKEN')
TASK_SLEEP_TIME = 60
MSG_MAX_LENGTH = 1000

# Debug
if DEBUG := os.getenv('DEBUG', '0') == '1':
    TASK_SLEEP_TIME = 30
