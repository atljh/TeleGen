from aiogram_dialog import Window, Dialog
from aiogram_dialog.widgets.text import Const, Format, Multi
from aiogram_dialog.widgets.kbd import (
    Button, Row, Column, Back, Cancel, Select, Group, Url
)
from aiogram.enums import ParseMode

from bot.dialogs.settings.payment.states import PaymentMenu
from .getters import packages_getter, periods_getter, methods_getter, success_getter
from .callbacks import (
    on_package_selected, on_period_selected,
    on_method_selected, on_monobank_confirm, on_cryptobot_confirm,
    on_back_to_main, on_back_to_methods, on_back_to_periods
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
                        "{item[name]} • {item[price]} • {item[features]}"
                    ),
                    item_id_getter=lambda item: item["id"],
                    items="packages",
                    id="package_select",
                    on_click=on_package_selected
                ),
            ),
            Row(
                Button(Const("Маю промокод"), id='input_promocode'),
            ),
            Row(
                Cancel(Const("🔙 Назад")),
            ),
            state=PaymentMenu.main,
            getter=packages_getter,
            parse_mode=ParseMode.MARKDOWN
        ),

        Window(
            Multi(
                Format("*Оберіть термін підписки*"),
                Format(""),
                Format("*Обраний пакет:* {selected_package[name]}"),
                Format(""),
                sep="\n"
            ),
            Group(
                Select(
                    text=Format("{item[name]} - {item[price]}{item[discount_display]}"),
                    item_id_getter=lambda item: item["id"],
                    items="periods",
                    id="period_select",
                    on_click=on_period_selected,
                ),
                width=2,
                id="periods_scroll"
            ),
            Back(Const("🔙 До пакетів")),
            state=PaymentMenu.choose_period,
            getter=periods_getter,
            parse_mode=ParseMode.MARKDOWN
        ),

        Window(
            Multi(
                Format("💳 *Оберіть спосіб оплати*"),
                Format(""),
                Format("*Пакет:* {package[name]}"),
                Format("*Термін:* {period[name]}"),
                Format("*Загальна сума:* {total_price}"),
                Format(""),
                sep="\n"
            ),
            Group(
                # Url(Const("💳 Monobank"), url="https://send.monobank.ua/XXXXXX"),
                Button(Const("💳 Monobank"), id="monobank_pay", on_click=on_method_selected),
                Button(Const("₿ CryptoBot"), id="cryptobot_pay", on_click=on_method_selected),
                width=2
            ),
            Back(Const("🔙 До термінів")),
            state=PaymentMenu.choose_method,
            getter=methods_getter,
            parse_mode=ParseMode.MARKDOWN
        ),

        Window(
            Multi(
                Format("💳 *Оплата через Monobank*"),
                Format(""),
                Format("*Пакет:* {package[name]}"),
                Format("*Термін:* {period[name]}"),
                Format("*Сума:* {total_price}"),
                Format(""),
                Format("➡️ [Перейдіть за посиланням для оплати](https://pay.monobank.ua/example)"),
                Format(""),
                Format("✅ *Після оплати натисніть кнопку нижче*"),
                sep="\n"
            ),
            Button(Const("✅ Я сплатив"), id="confirm_monobank", on_click=on_monobank_confirm),
            Back(Const("🔙 До способів")),
            state=PaymentMenu.monobank_payment,
            getter=methods_getter,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        ),

        Window(
            Multi(
                Format("₿ *Оплата через CryptoBot*"),
                Format(""),
                Format("*Пакет:* {package[name]}"),
                Format("*Термін:* {period[name]}"),
                Format("*Сума:* {total_price}"),
                Format(""),
                Format("➡️ [Оплатити через CryptoBot](https://t.me/CryptoBot?start=example)"),
                Format(""),
                Format("✅ *Після оплати натисніть кнопку нижче*"),
                sep="\n"
            ),
            Button(Const("✅ Я сплатив"), id="confirm_cryptobot", on_click=on_cryptobot_confirm),
            Back(Const("🔙 До способів")),
            state=PaymentMenu.cryptobot_payment,
            getter=methods_getter,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        ),

        Window(
            Multi(
                Format("🎉 *Дякуємо за оплату!*"),
                Format(""),
                Format("✅ *Підписка активована*"),
                Format("*Пакет:* {package[name]}"),
                Format("*Термін:* {period[name]}"),
                Format("*Сума:* {total_price}"),
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
