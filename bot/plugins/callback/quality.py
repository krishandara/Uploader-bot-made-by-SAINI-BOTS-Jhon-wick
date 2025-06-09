from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from bot.config import Script
from bot.utils.helpers import get_random_thumb
from database import db

@Client.on_callback_query(filters.regex(r"^quality$"))
async def quality(bot: Client, query: CallbackQuery):
    user = await db.users.get_user(query.from_user.id)

    text = "Quality:\n\n"
    text += (
        f"Current Quality: {['High', 'Medium', 'Low'][int(user['quality']) - 1]}\n\n"
    )
    text += "Select the quality you want to download the files in."

    markup = [
        [
            InlineKeyboardButton("⬜ ʜɪɢʜ", "quality_1"),
            InlineKeyboardButton("◻️ ᴍᴇᴅɪᴜᴍ", "quality_2"),
            InlineKeyboardButton("◽️ ʟᴏᴡ", "quality_3"),
        ],
        [InlineKeyboardButton("⋞ ʙ ᴀ ᴄ ᴋ ⋟", "start")],
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

@Client.on_callback_query(filters.regex(r"^quality_(\d)$"))
async def set_quality(bot: Client, query: CallbackQuery):
    _quality = int(query.data.split("_")[1])

    await db.users.update_user(query.from_user.id, {"quality": str(_quality)})
    await query.answer("Quality updated!")

    await quality(bot, query)
