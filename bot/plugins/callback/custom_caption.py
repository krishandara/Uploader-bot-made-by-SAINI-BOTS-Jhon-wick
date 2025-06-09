from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)

from bot.utils.helpers import get_random_thumb
from database import db

from bot.config import Script


@Client.on_callback_query(filters.regex(r"^custom_caption$"))
async def custom_caption(bot: Client, query: CallbackQuery):
    user = await db.users.get_user(query.from_user.id)
    current_caption = user["custom_caption"] or "Not Set"
    default_caption = Script.DEFAULT_CAPTION
    status = "Enabled" if user["custom_caption_enabled"] else "Disabled"

    text = Script.CAPTION_CB.format(
        current_caption=current_caption,
        default_caption=default_caption,
        status=status,
        file_name="{file_name}",
        file_size="{file_size}",
        file_extension="{file_extension}",
        file_url="{file_url}",
        file_duration="{file_duration}",
        file_index="{file_index}",
        batch_name="{batch_name}",
    )

    markup = [
        [InlineKeyboardButton("ᴇɴᴀʙʟᴇ / ᴅɪsᴀʙʟᴇ", "toggle_custom_caption")],
        [InlineKeyboardButton("ᴜᴘᴅᴀᴛᴇ ᴄᴀᴘᴛɪᴏɴ", "set_caption")],
        [InlineKeyboardButton("ʙ ᴀ ᴄ ᴋ ⋟", "start")],
    ]

    markup = InlineKeyboardMarkup(markup)
    func = (
        query.edit_message_text
        if isinstance(query, CallbackQuery)
        else query.reply_text
    )

    kwargs = {
        "text": text,
        "reply_markup": markup,
    }

    if thumb := get_random_thumb():
        if isinstance(query, CallbackQuery):
            if query.message.photo:
                kwargs["media"] = InputMediaPhoto(thumb, caption=kwargs["text"])
                kwargs.pop("text")
                func = query.edit_message_media
            else:
                kwargs["photo"] = thumb
                func = query.message.reply_photo
                kwargs["caption"] = kwargs["text"]
                kwargs.pop("text")
    await func(**kwargs)


@Client.on_callback_query(filters.regex(r"^toggle_custom_caption$"))
async def toggle_custom_caption(bot: Client, query: CallbackQuery):
    user = await db.users.get_user(query.from_user.id)

    await db.users.update_user(
        query.from_user.id,
        {"custom_caption_enabled": not user["custom_caption_enabled"]},
    )
    await query.answer("Custom Caption status updated!")

    await custom_caption(bot, query)


@Client.on_callback_query(filters.regex(r"^set_caption$"))
async def set_caption(bot: Client, query: CallbackQuery):
    try:
        ask_caption = await query.message.chat.ask(
            "Send me the new caption for your files."
        )
    except Exception as e:
        await query.message.reply_text(str(e))
        return

    await db.users.update_user(query.from_user.id, {"custom_caption": ask_caption.text})
    back_markup = [
        [InlineKeyboardButton("⋞ ʙ ᴀ ᴄ ᴋ ⋟", "custom_caption")],
    ]
    await query.message.reply_text(
        "Custom Caption updated!", reply_markup=InlineKeyboardMarkup(back_markup)
    )
