from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Select, Button

from bot.dialogs.settings.payment.states import PaymentMenu

async def on_package_selected(callback: CallbackQuery, widget: Select, manager: DialogManager, item_id: str):
    from .getters import packages_getter
    data = await packages_getter(manager)
    package = next((p for p in data["packages"] if p["id"] == item_id), None)
    if package:
        manager.dialog_data["selected_package"] = package
        await manager.switch_to(PaymentMenu.choose_period)

async def on_period_selected(callback: CallbackQuery, widget: Select, manager: DialogManager, item_id: str):
    from .getters import periods_getter
    data = await periods_getter(manager)
    period = next((p for p in data["periods"] if p["id"] == item_id), None)
    if period:
        manager.dialog_data["selected_period"] = period
        manager.dialog_data["total_price"] = period["price"]
        await manager.switch_to(PaymentMenu.choose_method)

async def on_method_selected(callback: CallbackQuery, widget: Button, manager: DialogManager):
    if widget.widget_id == "monobank_pay":
        await manager.switch_to(PaymentMenu.monobank_payment)
    elif widget.widget_id == "cryptobot_pay":
        await manager.switch_to(PaymentMenu.cryptobot_payment)

async def on_monobank_confirm(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(PaymentMenu.success)

async def on_cryptobot_confirm(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(PaymentMenu.success)

async def on_back_to_main(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.done()

async def on_back_to_methods(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(PaymentMenu.choose_method)

async def on_back_to_periods(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(PaymentMenu.choose_period)
