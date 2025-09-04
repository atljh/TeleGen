from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Select, Button, Row

from bot.dialogs.settings.payment.states import PaymentMenu

async def on_payment_start(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(PaymentMenu.choose_package)

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
        base_price = 100
        months = int(item_id)
        total_price = base_price * months
        manager.dialog_data["total_price"] = f"{total_price} грн"
        
        await manager.switch_to(PaymentMenu.choose_method)

async def on_method_selected(callback: CallbackQuery, widget: Select, manager: DialogManager, item_id: str):
    if item_id == "card":
        await manager.switch_to(PaymentMenu.card_payment)
    elif item_id == "crypto":
        await manager.switch_to(PaymentMenu.crypto_payment)
    elif item_id == "promo":
        await manager.switch_to(PaymentMenu.promo_code)

async def on_promo_code_apply(callback: CallbackQuery, button: Button, manager: DialogManager):
    promo_code = manager.dialog_data.get("promo_code", "")
    if promo_code == "TEST2024":
        manager.dialog_data["discount"] = "20%"
        manager.dialog_data["total_price"] = "80.00 грн"
        await callback.answer("✅ Промокод застосовано! Знижка 20%")
    else:
        await callback.answer("❌ Невірний промокод")

async def on_card_payment_confirm(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(PaymentMenu.success)

async def on_crypto_payment_confirm(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data["crypto_address"] = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    manager.dialog_data["crypto_amount"] = "0.025 ETH"
    await manager.switch_to(PaymentMenu.success)

async def on_back_to_main(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.done()

async def on_back_to_methods(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(PaymentMenu.choose_method)

async def on_back_to_periods(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(PaymentMenu.choose_period)

async def on_back_to_packages(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(PaymentMenu.choose_package)