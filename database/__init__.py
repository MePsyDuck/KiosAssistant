from tortoise import Tortoise

from config import DB_URL
from .models import *


async def init_orm():
    await Tortoise.init(
        db_url=DB_URL,
        modules={'models': ['database']}
    )
    await Tortoise.generate_schemas(safe=True)
