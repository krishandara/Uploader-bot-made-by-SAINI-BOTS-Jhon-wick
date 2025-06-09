from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from bot.config import Script
from bot.utils.helpers import get_random_thumb
from database import db


@Client.on_callback_query(filters.regex(r"^settings$"))
async def settings(bot: Client, query: CallbackQuery):
    data = {"mp4": "Video", "mkv": "Document"}

    text = "Settings:\n\n"
    user = await db.users.get_user(query.from_user.id)
    text += f"Custom Caption: {'✅' if user['custom_caption_enabled'] and user['custom_caption'] else '❌'}\n"
    text += f"Thumbnail: {'✅' if user['thumbnail_enabled'] and user['thumbnail'] else '❌'}\n"
    text += f"Mode: {data[user['ext']]}\n"

    settings_markup = [
        [
            ("ᴄᴜsᴛᴏᴍ - ᴄᴀᴘᴛɪᴏɴ", "custom_caption"),
        ],
        [
            ("ᴄᴜsᴛᴏᴍ - ᴛʜᴜᴍʙ", "thumbnail"),
        ],
        [
            ("ᴍᴏᴅᴇ", "mode"),
        ],
        [("⋞ ʙ ᴀ ᴄ ᴋ ⋟", "start")],
    ]

    markup = []

    for row in settings_markup:
        button_row = []
        for button in row:
            button_row.append(InlineKeyboardButton(button[0], callback_data=button[1]))
        markup.append(button_row)

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
