import logging

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button, Select
from asgiref.sync import sync_to_async

from admin_panel.models import PromoCode, Subscription, TariffPeriod, User
from admin_panel.services import PaymentHandler
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
    """Validate promo code and activate free subscription"""
    promo_code = promo.strip().upper()
    logging.info(f"Validating promo code: {promo_code}")

    # Find promo code in database
    promo_obj = await PromoCode.objects.select_related("tariff").filter(
        code=promo_code,
        is_active=True
    ).afirst()

    if not promo_obj:
        await callback.answer("❌ Промокод недійсний або неактивний", show_alert=True)
        return

    # Get tariff period for this promo code
    tariff_period = await TariffPeriod.objects.filter(
        tariff=promo_obj.tariff,
        months=promo_obj.months
    ).afirst()

    if not tariff_period:
        await callback.answer("❌ Помилка: тарифний період не знайдено", show_alert=True)
        logging.error(f"TariffPeriod not found for promo {promo_code}: tariff={promo_obj.tariff.id}, months={promo_obj.months}")
        return

    # All promo codes give free subscription - activate immediately
    telegram_user_id = callback.from_user.id

    # Get Django user from database
    user = await User.objects.filter(telegram_id=telegram_user_id).afirst()

    if not user:
        await callback.answer("❌ Користувача не знайдено в системі", show_alert=True)
        logging.error(f"User not found for telegram_id: {telegram_user_id}")
        return

    # Activate subscription using PaymentHandler service
    payment_handler = PaymentHandler()
    subscription = await sync_to_async(payment_handler.activate_subscription_from_promo)(
        user, promo_obj
    )

    if subscription:
        logging.info(
            f"Free subscription activated for user {telegram_user_id} "
            f"via promo code {promo_code}"
        )
        # Close the dialog - subscription is already activated
        await manager.done()
    else:
        # Check if user has an active subscription that might be preventing the downgrade
        active_subscription = await Subscription.objects.select_related(
            "tariff_period__tariff"
        ).filter(
            user=user,
            is_active=True
        ).afirst()

        if active_subscription and not tariff_period.is_upgrade_from(active_subscription.tariff_period):
            current = active_subscription.tariff_period
            await callback.answer(
                f"❌ Не можна використати цей промокод: у вас вже є підписка {current.tariff.name} на {current.months} міс.",
                show_alert=True
            )
        else:
            await callback.answer("❌ Помилка активації підписки. Спробуйте пізніше", show_alert=True)
        logging.error(f"Failed to activate subscription from promo code {promo_code}")
