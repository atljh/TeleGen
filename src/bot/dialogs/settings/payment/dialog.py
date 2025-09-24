from aiogram.enums import ParseMode
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import (
    Back,
    Button,
    Cancel,
    Column,
    Group,
    Row,
    Select,
    Url,
)
from aiogram_dialog.widgets.link_preview import LinkPreview
from aiogram_dialog.widgets.text import Const, Format, Jinja, Multi

from bot.dialogs.settings.payment.states import PaymentMenu
from bot.utils.constants.buttons import BACK_BUTTON

from .callbacks import (
    back_to_packages,
    on_back_to_main,
    on_method_selected,
    on_monobank_confirm,
    on_package_selected,
    on_period_selected,
    on_promocode_entered,
)
from .getters import (
    cryptobot_getter,
    methods_getter,
    monobank_getter,
    packages_getter,
    periods_getter,
    success_getter,
)


def create_payment_dialog():
    return Dialog(
        Window(
            Multi(
                Format("<b>Підписка на бота</b>"),
                Format("\n"),
                Format("<b>Ваш поточний статус:</b>"),
                Format("    План: <code>{current_plan}</code>"),
                Format("    Залишилось: <code>{days_left}</code> днів"),
                Format("\n"),
                Format("<b>Доступні пакети:</b>"),
                sep="\n",
            ),
            Column(
                Select(
                    text=Format("{item[name]} • {item[price]}"),
                    item_id_getter=lambda item: item["id"],
                    items="packages",
                    id="package_select",
                    on_click=on_package_selected,
                ),
            ),
            Row(
                Button(
                    Const("Ввести промокод"),
                    id="input_promocode",
                    on_click=lambda c, w, m: m.switch_to(PaymentMenu.promocode),
                ),
            ),
            Row(
                Cancel(BACK_BUTTON),
            ),
            state=PaymentMenu.main,
            getter=packages_getter,
            parse_mode=ParseMode.HTML,
        ),
        Window(
            Multi(
                Const("<b>Введіть промокод:</b>\n"),
                Const("Приклад: <code>WELCOME10</code>"),
                sep="\n",
            ),
            TextInput(
                id="promocode_input",
                on_success=on_promocode_entered,
                on_error=lambda m, d, e: m.dialog().show(Const("❌ Невірний формат")),
            ),
            Back(BACK_BUTTON),
            state=PaymentMenu.promocode,
            parse_mode=ParseMode.HTML,
        ),
        Window(
            Multi(
                Format("<b>Оберіть термін підписки</b>"),
                Format("\n"),
                Format("<b>Обраний пакет:</b> <code>{selected_package[name]}</code>"),
                Format("<b>Опис:</b>"),
                Format("<b>{selected_package[features]}</b>"),
                sep="\n",
            ),
            Group(
                Select(
                    text=Format(
                        "{item[name]} • {item[price]} {item[discount_display]}"
                    ),
                    item_id_getter=lambda item: item["id"],
                    items="periods",
                    id="period_select",
                    on_click=on_period_selected,
                ),
                width=2,
                id="periods_scroll",
            ),
            Button(
                Const("⬅️ До пакетів"), id="back_to_packages", on_click=back_to_packages
            ),
            state=PaymentMenu.choose_period,
            getter=periods_getter,
            parse_mode=ParseMode.HTML,
        ),
        Window(
            Multi(
                Format("<b>Оберіть спосіб оплати</b>"),
                Format(""),
                Format("<b>Пакет:</b> <code>{package[name]}</code>"),
                Format("<b>Термін:</b> <code>{period[name]}</code>"),
                Format("<b>Загальна сума:</b> <code>{total_price}</code>"),
                sep="\n",
            ),
            Group(
                Button(
                    Const("Monobank"), id="monobank_pay", on_click=on_method_selected
                ),
                Button(
                    Const("CryptoBot"), id="cryptobot_pay", on_click=on_method_selected
                ),
                width=2,
            ),
            Back(Const("⬅️ До термінів")),
            state=PaymentMenu.choose_method,
            getter=methods_getter,
            parse_mode=ParseMode.HTML,
        ),
        Window(
            Multi(
                Format("<b>Оплата через Monobank</b>"),
                Format(""),
                Format("<b>Пакет:</b> <code>{package[name]}</code>"),
                Format("<b>Термін:</b> <code>{period[name]}</code>"),
                Format("<b>Сума:</b> <code>{total_price}</code>"),
                sep="\n",
            ),
            Row(Url(text=Const("Оплатити"), url=Jinja("{{monobank_link}}"))),
            Button(
                Const("Перевірити оплату"),
                id="confirm_monobank",
                on_click=on_monobank_confirm,
            ),
            Back(Const("⬅️ До способів")),
            LinkPreview(is_disabled=True),
            state=PaymentMenu.monobank_payment,
            getter=monobank_getter,
            parse_mode=ParseMode.HTML,
        ),
        Window(
            Multi(
                Format("<b>Оплата через CryptoBot</b>"),
                Format(""),
                Format("<b>Пакет:</b> <code>{package[name]}</code>"),
                Format("<b>Термін:</b> <code>{period[name]}</code>"),
                Format("<b>Сума:</b> <code>{total_price}</code>"),
                sep="\n",
            ),
            Row(Url(text=Const("Оплатити"), url=Jinja("{{cryptobot_link}}"))),
            Button(
                Const("Перевірити оплату"),
                id="confirm_monobank",
                on_click=on_monobank_confirm,
            ),
            Back(Const("⬅️ До способів")),
            LinkPreview(is_disabled=True),
            state=PaymentMenu.cryptobot_payment,
            getter=cryptobot_getter,
            parse_mode=ParseMode.HTML,
        ),
        Window(
            Multi(
                Format("<b>Оплата пройшла успішно!</b>"),
                Format(""),
                Format("<b>Підписка активована</b>"),
                Format("Пакет: <code>{package[name]}</code>"),
                Format("Термін: <code>{period[name]}</code>"),
                Format("Сума: <code>{total_price}</code>"),
                Format(""),
                Format("Ви отримали повний доступ."),
                sep="\n",
            ),
            Button(Const("На головну"), id="to_main", on_click=on_back_to_main),
            state=PaymentMenu.success,
            getter=success_getter,
            parse_mode=ParseMode.HTML,
        ),
    )
