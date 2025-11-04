import logging

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button, Select
from asgiref.sync import sync_to_async

from admin_panel.models import PromoCode, TariffPeriod
from bot.dialogs.settings.payment.states import PaymentMenu

from .getters import packages_getter, periods_getter


async def on_package_selected(
    callback: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    data = await packages_getter(manager)
    package = next((p for p in data["packages"] if p["id"] == int(item_id)), None)
    if package:
        manager.dialog_data["selected_package"] = package
        await manager.switch_to(PaymentMenu.choose_period)


async def on_period_selected(
    callback: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    data = await periods_getter(manager)
    period = next((p for p in data["periods"] if p["id"] == item_id), None)
    if period:
        manager.dialog_data["selected_period"] = period
        # Convert price string to float for calculations
        manager.dialog_data["total_price"] = float(period["price"])
        await manager.switch_to(PaymentMenu.choose_method)


async def back_to_packages(
    callback: CallbackQuery, widget: Select, manager: DialogManager
):
    await manager.switch_to(PaymentMenu.main)


async def on_method_selected(
    callback: CallbackQuery, widget: Button, manager: DialogManager
):
    if widget.widget_id == "monobank_pay":
        await manager.switch_to(PaymentMenu.monobank_payment)
    elif widget.widget_id == "cryptobot_pay":
        await manager.switch_to(PaymentMenu.cryptobot_payment)


async def on_monobank_confirm(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(PaymentMenu.success)


async def on_cryptobot_confirm(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(PaymentMenu.success)


async def on_back_to_main(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.done()


async def on_back_to_methods(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(PaymentMenu.choose_method)


async def on_back_to_periods(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(PaymentMenu.choose_period)


async def on_promocode_entered(
    callback: CallbackQuery, button: Button, manager: DialogManager, promo: str
):
    """Validate and apply promo code"""
    promo_code = promo.strip().upper()
    logging.info(f"Validating promo code: {promo_code}")

    selected_package = manager.dialog_data.get("selected_package")
    selected_period = manager.dialog_data.get("selected_period")

    if not selected_package or not selected_period:
        manager.dialog_data["promocode_status"] = "error"
        manager.dialog_data["promocode_error"] = "Спочатку оберіть тариф та період"
        return

    # Get tariff period from DB
    tariff_period = await TariffPeriod.objects.filter(
        tariff_id=int(selected_package["id"]),
        id=int(selected_period["id"])
    ).afirst()

    if not tariff_period:
        manager.dialog_data["promocode_status"] = "error"
        manager.dialog_data["promocode_error"] = "Помилка: тариф не знайдено"
        return

    # Validate promo code
    promo_obj = await PromoCode.objects.filter(
        code=promo_code,
        tariff_id=int(selected_package["id"]),
        months=tariff_period.months,
        is_active=True
    ).afirst()

    if not promo_obj:
        manager.dialog_data["promocode_status"] = "error"
        manager.dialog_data["promocode_error"] = "Промокод недійсний або не підходить для обраного тарифу"
        return

    # Apply discount
    original_price = float(tariff_period.price)
    discount_amount = original_price * (promo_obj.discount_percent / 100)
    final_price = original_price - discount_amount

    # Save promo code data
    manager.dialog_data["promocode"] = promo_code
    manager.dialog_data["promocode_id"] = promo_obj.id
    manager.dialog_data["promocode_status"] = "success"
    manager.dialog_data["original_price"] = original_price
    manager.dialog_data["discount_percent"] = promo_obj.discount_percent
    manager.dialog_data["discount_amount"] = discount_amount
    manager.dialog_data["total_price"] = final_price

    logging.info(f"Promo code applied: {promo_code}, discount: {promo_obj.discount_percent}%, new price: {final_price}")

    await manager.switch_to(PaymentMenu.promocode_success)
