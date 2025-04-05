from .start import router as start_router
from .main_menu import router as menu_router
from .events import channel_router

routers = [start_router, menu_router, channel_router]

def register_handlers(dp):
    for router in routers:
        dp.include_router(router)