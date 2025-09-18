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
)
from aiogram_dialog.widgets.link_preview import LinkPreview
from aiogram_dialog.widgets.text import Const, Format, Multi

from bot.dialogs.settings.payment.states import PaymentMenu

from .callbacks import (
    back_to_packages,
    on_back_to_main,
    on_cryptobot_confirm,
    on_method_selected,
    on_monobank_confirm,
    on_package_selected,
    on_period_selected,
    on_promocode_entered,
)
from .getters import methods_getter, packages_getter, periods_getter, success_getter


def create_payment_dialog():
    return Dialog(
        Window(
            Multi(
                Format("*Підписка на бота*"),
                Format(""),
                Format("*Ваш поточний статус:*"),
                Format("    `{current_plan}` •  `{days_left} днів`"),
                Format(""),
                Format(" *Доступні пакети:*"),
                Format(""),
                sep="\n",
            ),
            Column(
                Select(
                    text=Format("{item[name]} • {item[price]} • {item[features]}"),
                    item_id_getter=lambda item: item["id"],
                    items="packages",
                    id="package_select",
                    on_click=on_package_selected,
                ),
            ),
            Row(
                Button(
                    Const("🎟 Маю промокод"),
                    id="input_promocode",
                    on_click=lambda c, w, m: m.switch_to(PaymentMenu.promocode),
                ),
            ),
            Row(
                Cancel(Const("🔙 Назад")),
            ),
            state=PaymentMenu.main,
            getter=packages_getter,
            parse_mode=ParseMode.MARKDOWN,
        ),
        Window(
            Multi(
                Const("🎟 *Введіть промокод:*"),
                Format("(наприклад: WELCOME10)"),
                sep="\n",
            ),
            TextInput(
                id="promocode_input",
                on_success=on_promocode_entered,
                on_error=lambda m, d, e: m.dialog().show(Const("❌ Невірний формат")),
            ),
            Back(Const("🔙 Назад")),
            state=PaymentMenu.promocode,
            parse_mode=ParseMode.MARKDOWN,
        ),
        Window(
            Multi(
                Format("*Оберіть термін підписки*"),
                Format(""),
                Format("*Обраний пакет:* {selected_package[name]}"),
                Format(""),
                sep="\n",
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
                id="periods_scroll",
            ),
            Button(
                Const("🔙 До пакетів"), id="back_to_packages", on_click=back_to_packages
            ),
            state=PaymentMenu.choose_period,
            getter=periods_getter,
            parse_mode=ParseMode.MARKDOWN,
        ),
        Window(
            Multi(
                Format("💳 *Оберіть спосіб оплати*"),
                Format(""),
                Format("*Пакет:* {package[name]}"),
                Format("*Термін:* {period[name]}"),
                Format("*Загальна сума:* {total_price}"),
                Format(""),
                sep="\n",
            ),
            Group(
                Button(
                    Const("💳 Monobank"), id="monobank_pay", on_click=on_method_selected
                ),
                Button(
                    Const("₿ CryptoBot"),
                    id="cryptobot_pay",
                    on_click=on_method_selected,
                ),
                width=2,
            ),
            Back(Const("🔙 До термінів")),
            state=PaymentMenu.choose_method,
            getter=methods_getter,
            parse_mode=ParseMode.MARKDOWN,
        ),
        Window(
            Multi(
                Format("💳 *Оплата через Monobank*"),
                Format(""),
                Format("*Пакет:* {package[name]}"),
                Format("*Термін:* {period[name]}"),
                Format("*Сума:* {total_price}"),
                Format(""),
                Format("➡️ [Перейдіть за посиланням для оплати]({monobank_link})"),
                Format(""),
                Format("✅ *Після оплати натисніть кнопку нижче*"),
                sep="\n",
            ),
            Button(
                Const("✅ Я сплатив"),
                id="confirm_monobank",
                on_click=on_monobank_confirm,
            ),
            Back(Const("🔙 До способів")),
            LinkPreview(is_disabled=True),
            state=PaymentMenu.monobank_payment,
            getter=methods_getter,
            parse_mode=ParseMode.MARKDOWN,
        ),
        Window(
            Multi(
                Format("₿ *Оплата через CryptoBot*"),
                Format(""),
                Format("*Пакет:* {package[name]}"),
                Format("*Термін:* {period[name]}"),
                Format("*Сума:* {total_price}"),
                Format(""),
                Format("➡️ [Оплатити через CryptoBot]({cryptobot_link})"),
                Format(""),
                Format("✅ *Після оплати натисніть кнопку нижче*"),
                sep="\n",
            ),
            Button(
                Const("✅ Я сплатив"),
                id="confirm_cryptobot",
                on_click=on_cryptobot_confirm,
            ),
            Back(Const("🔙 До способів")),
            LinkPreview(is_disabled=True),
            state=PaymentMenu.cryptobot_payment,
            getter=methods_getter,
            parse_mode=ParseMode.MARKDOWN,
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
                sep="\n",
            ),
            Button(Const("🏠 На головну"), id="to_main", on_click=on_back_to_main),
            state=PaymentMenu.success,
            getter=success_getter,
            parse_mode=ParseMode.MARKDOWN,
        ),
    )
