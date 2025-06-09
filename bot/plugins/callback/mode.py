from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from database import db
from bot.config import Script
from bot.utils.helpers import get_random_thumb
from database import db

@Client.on_callback_query(filters.regex(r"^mode$"))
async def mode(bot: Client, query: CallbackQuery):
    data = {
        "mp4": "🎞️ ᴠɪᴅᴇᴏ",
        "mkv": "📁 ᴅᴏᴄᴜᴍᴇɴᴛ",
    }

    user = await db.users.get_user(query.from_user.id)
    text = "Mode:\n\n"
    text += f"Current Mode: {data[user['ext']]}\n\n"

    text += "Select the mode you want to use for downloading files."

    markup = []

    for mode, name in data.items():
        markup.append([InlineKeyboardButton(name, f"set_mode_{mode}")])

    markup.append([InlineKeyboardButton("⋞ ʙ ᴀ ᴄ ᴋ ⋟", "start")])

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

@Client.on_callback_query(filters.regex(r"^set_mode_(.*)$"))
async def set_mode(bot: Client, query: CallbackQuery):
    mode_ = query.data.split("_")[-1]

    await db.users.update_user(query.from_user.id, {"ext": mode_})
    await query.answer("Mode updated!")

    await mode(bot, query)
