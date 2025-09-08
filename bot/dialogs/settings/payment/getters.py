
from typing import Dict, Any
from aiogram_dialog import DialogManager

async def packages_getter(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    return {
        "packages": [
            {
                "id": "basic",
                "name": "БАЗОВИЙ",
                "price": "100 грн/міс",
                "features": "5 каналів • 10 постів"
            },
            {
                "id": "pro",
                "name": "ПРОФЕСІЙНИЙ",
                "price": "300 грн/міс",
                "features": "15 каналів • 50 постів • AI"
            },
            {
                "id": "enterprise",
                "name": "ПРЕМІУМ",
                "price": "500 грн/міс",
                "features": "∞ каналів • 200 постів • VIP"
            }
        ],
        "current_plan": "Базовий",
        "days_left": "15",
    }

async def periods_getter(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    selected_package = dialog_manager.dialog_data.get("selected_package", {})
    periods = [
        {
            "id": "1",
            "name": "1 місяць",
            "price": "100 грн",
            "discount_display": ""
        },
        {
            "id": "6",
            "name": "6 місяців",
            "price": "500 грн",
            "discount_display": " -17%"
        },
        {
            "id": "9",
            "name": "9 місяців",
            "price": "750 грн",
            "discount_display": " -25%"
        },
        {
            "id": "12",
            "name": "1 рік",
            "price": "900 грн",
            "discount_display": " -33%"
        },
    ]
    return {
        "periods": periods,
        "selected_package": selected_package,
    }


async def methods_getter(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    selected_package = dialog_manager.dialog_data.get("selected_package")
    selected_period = dialog_manager.dialog_data.get("selected_period")
    total_price = "100.00"

    return {
        "package": selected_package,
        "period": selected_period,
        "total_price": total_price
    }

async def success_getter(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    return {
        "package": dialog_manager.dialog_data.get("selected_package"),
        "period": dialog_manager.dialog_data.get("selected_period"),
        "total_price": dialog_manager.dialog_data.get("total_price")
    }