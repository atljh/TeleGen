from aiogram_dialog import Window, Dialog
from aiogram_dialog.widgets.text import Const, Format, Multi
from aiogram_dialog.widgets.kbd import (
    Button, Row, Column, Back, Cancel, Select, Group, ScrollingGroup
)
from aiogram.enums import ParseMode

from bot.dialogs.settings.payment.states import PaymentMenu

from .getters import (
    packages_getter, 
    periods_getter, methods_getter, success_getter
)
from .callbacks import (
    on_payment_start, on_package_selected, on_period_selected,
    on_method_selected, on_promo_code_apply, on_card_payment_confirm,
    on_crypto_payment_confirm, on_back_to_main, on_back_to_methods,
    on_back_to_periods, on_back_to_packages
)

def create_payment_dialog():
    return Dialog(
        Window(
            Multi(
                Format("✨ *Підписка на бота*"),
                Format(""),
                Format("*Ваш поточний статус:*"),
                Format("    `{current_plan}` •  `{days_left} днів`"),
                Format(""),
                Format(" *Доступні пакети:*"),
                Format(""),
                sep="\n"
            ),
            Column(
                Select(
                    text=Format(
                        "{item[name]}"
                        " • {item[price]}" 
                        " • {item[features]}"
                    ),
                    item_id_getter=lambda item: item["id"],
                    items="packages", 
                    id="package_select",
                    on_click=on_package_selected
                ),
            ),
            Row(
                Button(Const("🎫 Маю промокод"), id="enter_promo", on_click=on_method_selected),
                Back(Const("🔙 Назад")),
            ),
            state=PaymentMenu.main,
            getter=packages_getter,
            parse_mode=ParseMode.MARKDOWN
        ),
        
        Window(
            Multi(
                Format("📅 *Оберіть термін підписки*"),
                Format(""),
                Format("📦 *Обраний пакет:* {selected_package[name]}"),
                Format(""),
                sep="\n"
            ),
            ScrollingGroup(
                Select(
                    text=Format("{item[name]} - {item[price]} {item[discount] if item.get('discount') else ''}"),
                    item_id_getter=lambda item: item["id"],
                    items="periods",
                    id="period_select",
                    on_click=on_period_selected
                ),
                width=2,
                height=4,
                id="periods_scroll"
            ),
            Back(Const("🔙 До пакетів")),
            Cancel(Const("❌ Скасувати")),
            state=PaymentMenu.choose_period,
            getter=periods_getter,
            parse_mode=ParseMode.MARKDOWN
        ),
        
        Window(
            Multi(
                Format("💳 *Оберіть спосіб оплати*"),
                Format(""),
                Format("📦 *Пакет:* {package[name]}"),
                Format("⏰ *Термін:* {period[name]}"),
                Format("💰 *Загальна сума:* {total_price}"),
                Format(""),
                sep="\n"
            ),
            Group(
                Button(Const("💳 Картка"), id="card_pay", on_click=on_method_selected),
                Button(Const("₿ Криптовалюта"), id="crypto_pay", on_click=on_method_selected),
                width=2
            ),
            Back(Const("🔙 До термінів")),
            Cancel(Const("❌ Скасувати")),
            state=PaymentMenu.choose_method,
            getter=methods_getter,
            parse_mode=ParseMode.MARKDOWN
        ),
        
        Window(
            Multi(
                Format("💳 *Оплата карткою*"),
                Format(""),
                Format("📦 *Пакет:* {package[name]}"),
                Format("⏰ *Термін:* {period[name]}"), 
                Format("💰 *Сума:* {total_price}"),
                Format(""),
                Format("➡️ *Перейдіть за посиланням для оплати:*"),
                Format("[Посилання на оплату](https://payment.example.com)"),
                Format(""),
                Format("✅ *Після оплати натисніть кнопку нижче*"),
                sep="\n"
            ),
            Button(Const("✅ Я сплатив"), id="confirm_card", on_click=on_card_payment_confirm),
            Back(Const("🔙 До способів")),
            state=PaymentMenu.card_payment,
            getter=methods_getter,
            parse_mode=ParseMode.MARKDOWN
        ),
        
        Window(
            Multi(
                Format("₿ *Оплата криптовалютою*"),
                Format(""),
                Format("📦 *Пакет:* {package[name]}"),
                Format("⏰ *Термін:* {period[name]}"),
                Format("💰 *Сума:* {crypto_amount}"),
                Format(""),
                Format("🔷 *Адреса для оплати:*"),
                Format("`{crypto_address}`"),
                Format(""),
                Format("💡 *Надішліть точну суму на вказану адресу*"),
                sep="\n"
            ),
            Button(Const("✅ Я сплатив"), id="confirm_crypto", on_click=on_crypto_payment_confirm),
            Back(Const("🔙 До способів")),
            state=PaymentMenu.crypto_payment,
            getter=methods_getter,
            parse_mode=ParseMode.MARKDOWN
        ),
        
        Window(
            Multi(
                Format("🎉 *Дякуємо за оплату!*"),
                Format(""),
                Format("✅ *Підписка активована*"),
                Format("📦 *Пакет:* {package[name]}"),
                Format("⏰ *Термін:* {period[name]}"),
                Format("💰 *Сума:* {total_price}"),
                Format(""),
                Format("⏳ *Термін дії до:* 01.01.2025"),
                Format(""),
                Format("💫 *Насолоджуйтесь повним доступом!*"),
                sep="\n"
            ),
            Button(Const("🏠 На головну"), id="to_main", on_click=on_back_to_main),
            state=PaymentMenu.success,
            getter=success_getter,
            parse_mode=ParseMode.MARKDOWN
        )
    )