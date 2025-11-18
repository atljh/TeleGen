from typing import Any

from aiogram_dialog import DialogManager
from asgiref.sync import sync_to_async
from django.utils import timezone

from admin_panel.models import Subscription, Tariff, TariffPeriod
from bot.containers import Container


async def packages_getter(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    user = dialog_manager.event.from_user

    tariffs = await sync_to_async(list)(Tariff.objects.filter(is_active=True))

    subscription = (
        await Subscription.objects.select_related(
            "tariff_period", "tariff_period__tariff"
        )
        .filter(
            user__telegram_id=user.id,
            is_active=True,
        )
        .afirst()
    )

    # Get current tariff to filter out lower-tier subscriptions
    current_tariff = subscription.tariff_period.tariff if subscription else None

    packages = [
        {
            "id": tariff.id,
            "name": tariff.name,
            "price": "від "
            + str(
                await sync_to_async(
                    lambda t: t.periods.order_by("price").first().price
                )(tariff)
            )
            + " грн",
            "features": tariff.description or "",
        }
        for tariff in tariffs
        # Filter out: free tariff and tariffs lower than current subscription
        # BUT allow current tariff (for longer periods)
        if tariff.code != "free" and (
            tariff.is_higher_than(current_tariff)
            or (current_tariff and tariff.level == current_tariff.level)
        )
    ]

    return {
        "packages": packages,
        "current_plan": (
            subscription.tariff_period.tariff.name if subscription else "Без підписки"
        ),
        "days_left": (
            max((subscription.end_date - timezone.now()).days, 0) if subscription else 0
        ),
    }


async def periods_getter(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    selected_package = dialog_manager.dialog_data.get("selected_package")

    if not selected_package:
        return {"periods": [], "selected_package": {}}

    tariff_id = selected_package["id"]
    user = dialog_manager.event.from_user

    # Get user's active subscription
    subscription = (
        await Subscription.objects.select_related(
            "tariff_period", "tariff_period__tariff"
        )
        .filter(
            user__telegram_id=user.id,
            is_active=True,
        )
        .afirst()
    )

    periods = await sync_to_async(list)(
        TariffPeriod.objects.filter(tariff_id=tariff_id).select_related("tariff").order_by("months")
    )

    # Filter periods based on current subscription
    if subscription:
        current_tariff_period = subscription.tariff_period
        # If user selected their current tariff, show only longer periods
        if subscription.tariff_period.tariff_id == tariff_id:
            periods = [p for p in periods if p.months > current_tariff_period.months]

    periods_data = [
        {
            "id": str(period.id),
            "name": f"{period.months} місяць"
            if period.months == 1
            else f"{period.months} місяців",
            "price": f"{period.price}",
        }
        for period in periods
    ]

    return {
        "periods": periods_data,
        "selected_package": selected_package,
    }


async def methods_getter(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    selected_package = dialog_manager.dialog_data.get("selected_package")
    selected_period = dialog_manager.dialog_data.get("selected_period")

    # Check if promo code was applied
    promo_applied = dialog_manager.dialog_data.get("promocode_status") == "success"

    total_price = "0.00"
    original_price = "0.00"
    discount_info = ""

    if selected_package and selected_period:
        if promo_applied:
            # Use discounted price from dialog_data
            total_price_val = dialog_manager.dialog_data.get('total_price', 0)
            original_price_val = dialog_manager.dialog_data.get('original_price', 0)
            # Convert to float if string
            if isinstance(total_price_val, str):
                total_price_val = float(total_price_val)
            if isinstance(original_price_val, str):
                original_price_val = float(original_price_val)
            total_price = f"{total_price_val:.2f}"
            original_price = f"{original_price_val:.2f}"
            discount_percent = dialog_manager.dialog_data.get('discount_percent', 0)
            discount_info = f"-{discount_percent}% (промокод: {dialog_manager.dialog_data.get('promocode', '')})"
        else:
            tariff_period = await TariffPeriod.objects.filter(
                tariff_id=int(selected_package["id"]), id=int(selected_period["id"])
            ).afirst()

            if tariff_period:
                total_price = f"{tariff_period.price:.2f}"
                original_price = total_price

    return {
        "package": selected_package,
        "period": selected_period,
        "total_price": total_price,
        "original_price": original_price,
        "discount_info": discount_info,
        "promo_applied": promo_applied,
    }


async def success_getter(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    return {
        "package": dialog_manager.dialog_data.get("selected_package"),
        "period": dialog_manager.dialog_data.get("selected_period"),
        "total_price": dialog_manager.dialog_data.get("total_price"),
    }


async def promocode_getter(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    return {
        "selected_package": dialog_manager.dialog_data.get("selected_package"),
        "entered_promocode": dialog_manager.dialog_data.get("entered_promocode", ""),
        "promocode_status": dialog_manager.dialog_data.get("promocode_status", ""),
    }


async def promocode_success_getter(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    selected_package = dialog_manager.dialog_data.get("selected_package")
    selected_period = dialog_manager.dialog_data.get("selected_period")

    return {
        "package": selected_package,
        "period": selected_period,
        "promocode": dialog_manager.dialog_data.get("promocode", ""),
        "original_price": f"{dialog_manager.dialog_data.get('original_price', 0):.2f}",
        "discount_percent": dialog_manager.dialog_data.get("discount_percent", 0),
        "discount_amount": f"{dialog_manager.dialog_data.get('discount_amount', 0):.2f}",
        "total_price": f"{dialog_manager.dialog_data.get('total_price', 0):.2f}",
    }


async def monobank_getter(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    payment_service = Container.payment_service()

    package = dialog_manager.dialog_data.get("selected_package")
    period = dialog_manager.dialog_data.get("selected_period")
    total_price = dialog_manager.dialog_data.get("total_price")
    promo_code_id = dialog_manager.dialog_data.get("promocode_id")
    user_id = dialog_manager.event.from_user.id

    payment_dto = await payment_service.create_payment(
        user_id=user_id,
        amount=total_price,
        payment_method="monobank",
        tariff_period_id=int(period["id"]),
        description="Оплата за інформаційні послуги. Без ПДВ.",
        currency="UAH",
        promo_code_id=promo_code_id,
    )

    return {
        "package": package,
        "period": period,
        "total_price": total_price,
        "monobank_link": payment_dto.pay_url,
    }



async def cryptobot_getter(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    payment_service = Container.payment_service()

    package = dialog_manager.dialog_data.get("selected_package")
    period = dialog_manager.dialog_data.get("selected_period")
    total_price = dialog_manager.dialog_data.get("total_price")
    promo_code_id = dialog_manager.dialog_data.get("promocode_id")
    user_id = dialog_manager.event.from_user.id

    payment_dto = await payment_service.create_payment(
        user_id=user_id,
        amount=total_price,
        tariff_period_id=int(period["id"]),
        payment_method="cryptobot",
        description="Оплата за інформаційні послуги. Без ПДВ.",
        currency="UAH",
        promo_code_id=promo_code_id,
    )

    return {
        "package": package,
        "period": period,
        "total_price": total_price,
        "cryptobot_link": payment_dto.pay_url,
    }
