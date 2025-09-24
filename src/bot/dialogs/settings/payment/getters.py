from typing import Any

from aiogram_dialog import DialogManager
from asgiref.sync import sync_to_async

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
        if tariff.code != "free"
    ]

    return {
        "packages": packages,
        "current_plan": (
            subscription.tariff_period.tariff.name if subscription else "Без підписки"
        ),
        "days_left": (
            (subscription.end_date - subscription.start_date).days
            if subscription
            else 0
        ),
    }


async def periods_getter(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    selected_package = dialog_manager.dialog_data.get("selected_package")

    if not selected_package:
        return {"periods": [], "selected_package": {}}

    tariff_id = selected_package["id"]

    periods = await sync_to_async(list)(
        TariffPeriod.objects.filter(tariff_id=tariff_id).order_by("months")
    )

    periods_data = [
        {
            "id": str(period.id),
            "name": f"{period.months} місяць"
            if period.months == 1
            else f"{period.months} місяців",
            "price": f"{period.price}",
            "discount_display": f" -{period.discount_percent}%"
            if period.discount_percent
            else "",
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

    total_price = "0.00"
    if selected_package and selected_period:
        tariff_period = await TariffPeriod.objects.filter(
            tariff_id=int(selected_package["id"]), id=int(selected_period["id"])
        ).afirst()

        if tariff_period:
            total_price = f"{tariff_period.price:.2f}"
    return {
        "package": selected_package,
        "period": selected_period,
        "total_price": total_price,
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


async def monobank_getter(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    payment_service = Container.payment_service()

    package = dialog_manager.dialog_data.get("selected_package")
    period = dialog_manager.dialog_data.get("selected_period")
    total_price = dialog_manager.dialog_data.get("total_price")
    user_id = dialog_manager.event.from_user.id

    payment_dto = await payment_service.create_payment(
        user_id=user_id,
        amount=total_price,
        payment_method="monobank",
        description=f"Підписка: {package['name']} • {period['name']}",
        currency="UAH",
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
    user_id = dialog_manager.event.from_user.id

    payment_dto = await payment_service.create_payment(
        user_id=user_id,
        amount=total_price,
        payment_method="cryptobot",
        description=f"Підписка: {package['name']} • {period['name']}",
        currency="USDT",
    )

    return {
        "package": package,
        "period": period,
        "total_price": total_price,
        "cryptobot_link": payment_dto.pay_url,
    }
