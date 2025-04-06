from aiogram.fsm.state import State, StatesGroup
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.kbd import Button, Column, Row, Back
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog import DialogManager, StartMode
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.enums import ParseMode

from dialogs.buffer.states import BufferMenu


class EditPostMenu(StatesGroup):
    edit_options = State()
    edit_text = State()
    edit_media = State()
    edit_links = State()
    edit_buttons = State()

async def get_edit_data(dialog_manager: DialogManager, **kwargs):
    return {"post_text": dialog_manager.dialog_data.get("post_text", "Текст вiдсутнiй")}

def create_edit_dialog():
    return Dialog(
        Window(
            Format("Поточний текст: {post_text}"),
            Row(
                Button(Const("Змінити текст"), id="edit_text_btn", on_click=lambda c, b, m: m.switch_to(EditPostMenu.edit_text)),
                Button(Const("Змінити медіа"), id="edit_media_btn", on_click=lambda c, b, m: m.switch_to(EditPostMenu.edit_media)),
            ),
            Row(
                Button(Const("Заміна посилань"), id="edit_links_btn", on_click=lambda c, b, m: m.switch_to(EditPostMenu.edit_links)),
                Button(Const("URL-кнопки"), id="edit_buttons_btn", on_click=lambda c, b, m: m.switch_to(EditPostMenu.edit_buttons)),
            ),
            Row(
                Button(Const("🔙 Назад"), id='go_back_to_buffer', on_click=go_back_to_buffer),
            ),
            state=EditPostMenu.edit_options,
            parse_mode=ParseMode.HTML,
            getter=get_edit_data,
        ),

        Window(
            Const("✏️ Введіть новий текст повідомлення:"),
            MessageInput(
                func=save_new_text,
                content_types=ContentType.TEXT
            ),
            Row(
                Back(Const("🔙 Назад")),
            ),
            state=EditPostMenu.edit_text,
            parse_mode=ParseMode.HTML
        ),

        Window(
            Const("🖼 Надішліть нове фото/відео:"),
            MessageInput(
                func=save_new_media,
                content_types=[ContentType.PHOTO, ContentType.VIDEO]
            ),
            Row(
                Button(Const("Видалити медіа"), id="remove_media", on_click=remove_media),
                Back(Const("🔙 Назад")),
            ),
            state=EditPostMenu.edit_media,
            parse_mode=ParseMode.HTML
        ),
    )


async def save_new_text(message: Message, widget: MessageInput, manager: DialogManager):
    new_text = message.html_text
    manager.dialog_data["post_text"] = new_text

    await manager.start(BufferMenu.preview, mode=StartMode.RESET_STACK, data={"post_text": new_text})
    await message.answer("✅ Текст успішно оновлено!")

async def save_new_media(message: Message, widget: MessageInput, manager: DialogManager):
    if message.photo:
        manager.dialog_data["media"] = message.photo[-1].file_id
    elif message.video:
        manager.dialog_data["media"] = message.video.file_id
    await manager.switch_to(EditPostMenu.edit_options)
    await message.answer("✅ Медіа успішно оновлено!")

async def remove_media(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data.pop("media", None)
    await callback.answer("Медіа видалено")
    await manager.switch_to(EditPostMenu.edit_options)

async def go_back_to_buffer(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(BufferMenu.preview, mode=StartMode.RESET_STACK)
