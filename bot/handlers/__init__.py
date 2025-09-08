from .basic_commands import basic_commands_router
from .events import channel_router
from .genaration import generation_router
from .main_menu import router as menu_router
from .start import router as start_router

routers = [
    start_router,
    menu_router,
    channel_router,
    basic_commands_router,
    generation_router,
]


def register_handlers(dp):
    for router in routers:
        dp.include_router(router)
