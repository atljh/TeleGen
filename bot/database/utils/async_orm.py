from asgiref.sync import sync_to_async
from functools import wraps


class AsyncORM:
    def __getattribute__(self, name):
        attr = super().__getattribute__(name)
        if callable(attr) and not name.startswith("_"):

            @wraps(attr)
            async def wrapped(*args, **kwargs):
                return await sync_to_async(attr)(*args, **kwargs)

            return wrapped
        return attr
