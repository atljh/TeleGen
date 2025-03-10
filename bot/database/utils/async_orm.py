from asgiref.sync import sync_to_async
from functools import wraps

class AsyncORM:
    """Базовый класс для автоматического применения sync_to_async ко всем методам."""

    def __getattribute__(self, name):
        attr = super().__getattribute__(name)
        if callable(attr) and not name.startswith("_"):  # Игнорируем приватные методы
            # Если метод вызываемый, оборачиваем его в sync_to_async
            @wraps(attr)
            async def wrapped(*args, **kwargs):
                return await sync_to_async(attr)(*args, **kwargs)
            return wrapped
        return attr