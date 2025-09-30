from aiogram import Router, types
from aiogram.filters import Command

basic_commands_router = Router()


@basic_commands_router.message(Command("settings"))
async def settings_command(message: types.Message):
    await message.answer(
        "⚙ **Налаштування бота**\n\n"
        "Тут ви можете налаштувати:\n"
        "- Мову інтерфейсу\n"
        "- Сповіщення\n"
        "- Особисті параметри",
        parse_mode="HTML",
    )


@basic_commands_router.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer(
        "🆘 **Допомога**\n\n"
        "Доступні команди:\n"
        "/start - Початок роботи\n"
        "/settings - Налаштування\n"
        "/price - Переглянути ціни\n\n"
        "З питань роботи бота звертайтеся до адміністратора.",
        parse_mode="HTML",
    )


@basic_commands_router.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "👋 <b>Вітаємо у нашому боті</b>n\n"
        "Цей бот допоможе вам з...\n\n"
        "Щоб почати, оберіть потрібну команду з меню або введіть /help",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardRemove(),
    )


@basic_commands_router.message(Command("price"))
async def price_command(message: types.Message):
    await message.answer(
        "💵 <b>Наші ціни</b>\n\n"
        "🔹 Базовий тариф - 100 грн/міс\n"
        "🔹 Стандартний тариф - 200 грн/міс\n"
        "🔹 Преміум тариф - 350 грн/міс\n\n",
        parse_mode="HTML",
    )


@basic_commands_router.message(Command("menu"))
async def menu_command(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="⚙ Налаштування")],
            [types.KeyboardButton(text="🆘 Допомога")],
            [types.KeyboardButton(text="💵 Ціни")],
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "📱 **Головне меню**\n\nОберіть потрібний пункт:",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
