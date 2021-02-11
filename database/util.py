from functools import wraps

from tortoise.transactions import in_transaction


def atomic(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with in_transaction():
            return await func(*args, **kwargs)

    return wrapper
