from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    InputMediaPhoto,
)
from bot.config import Script
from bot.utils.helpers import get_random_thumb
from database import db


@Client.on_callback_query(filters.regex(r"^thumbnail$"))
async def thumbnail(bot: Client, query: CallbackQuery):
    user = await db.users.get_user(query.from_user.id)

    text = " Thumbnail:\n\n"
    text += f"Status: {'Enabled' if user['thumbnail_enabled'] else 'Disabled'}\n"
    text += f"Current Thumbnail: {'Set' if user['thumbnail'] else 'Not Set'}\n"

    if user["thumbnail_enabled"]:
        text += "\nTo disable thumbnail, click the button below."
    else:
        text = text[:-1]

    text += "\n\n"

    text += "You can set a custom thumbnail for your files by sending the photo you want to set as the thumbnail."

    markup = [
        (
            [InlineKeyboardButton("👀 ᴠɪᴇᴡ-ᴛʜᴜᴍʙ", "view_thumbnail")]
            if user["thumbnail"] is not None
            else []
        ),
        [InlineKeyboardButton("ᴇɴᴀʙʟᴇ / ᴅɪsᴀʙʟᴇ", "toggle_thumbnail")],
        [
            InlineKeyboardButton("ᴀᴅᴅ-ᴛʜᴜᴍʙ", "set_thumbnail"),
        ],
        [InlineKeyboardButton("⋞ ʙ ᴀ ᴄ ᴋ ⋟", "start")],
    ]

    if user["thumbnail"]:
        markup.insert(1, [InlineKeyboardButton("🗑 ʀᴇᴍᴏᴠᴇ-ᴛʜᴜᴍʙ", "reset_thumbnail")])

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


@Client.on_callback_query(filters.regex(r"^toggle_thumbnail$"))
async def toggle_thumbnail(bot: Client, query: CallbackQuery):
    user = await db.users.get_user(query.from_user.id)

    await db.users.update_user(
        query.from_user.id, {"thumbnail_enabled": not user["thumbnail_enabled"]}
    )
    await query.answer("Thumbnail status updated!")

    await thumbnail(bot, query)


@Client.on_callback_query(filters.regex(r"^set_thumbnail$"))
async def set_thumbnail(bot: Client, query: CallbackQuery):
    try:
        ask_thumbnail = await query.message.chat.ask(
            "Send me the photo you want to set as the thumbnail."
        )
        thumbnail_ = ask_thumbnail.photo.file_id
    except Exception as e:
        await query.message.reply_text(str(e))
        return

    await db.users.update_user(query.from_user.id, {"thumbnail": thumbnail_})
    markup = [
        [InlineKeyboardButton("⋞ ʙ ᴀ ᴄ ᴋ ⋟", "thumbnail")],
    ]
    await query.message.reply_photo(
        thumbnail_,
    )

    await query.message.reply_text(
        "Thumbnail updated!", reply_markup=InlineKeyboardMarkup(markup)
    )


@Client.on_callback_query(filters.regex(r"^view_thumbnail$"))
async def view_thumbnail(bot: Client, query: CallbackQuery):
    user = await db.users.get_user(query.from_user.id)
    if user["thumbnail"]:
        await query.message.reply_photo(user["thumbnail"], caption="Current thumbnail")
    else:
        return await query.answer("No thumbnail set yet!", show_alert=True)

    query.message.from_user = query.from_user
    await thumbnail(bot, query.message)


@Client.on_callback_query(filters.regex(r"^reset_thumbnail$"))
async def reset_thumbnail(bot: Client, query: CallbackQuery):
    await db.users.update_user(query.from_user.id, {"thumbnail": None})
    await query.answer("Thumbnail reset!")
    await thumbnail(bot, query)
