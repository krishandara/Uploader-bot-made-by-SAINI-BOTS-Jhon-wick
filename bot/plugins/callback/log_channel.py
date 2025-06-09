from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)
from database import db
from bot.config import Script
from bot.utils.helpers import get_random_thumb
from database import db


@Client.on_callback_query(filters.regex(r"^log_channel$"))
async def log_channel(bot: Client, query: CallbackQuery):
    user = await db.users.get_user(query.from_user.id)

    text = "**Log Channel**\n\n"
    text += f"Channel: {user['log_channel'] or 'Not Set'}"

    markup = [
        [
            InlineKeyboardButton("Sᴇᴛ", "set_log_channel"),
            InlineKeyboardButton("Rᴇᴍᴏᴠᴇ", "remove_log_channel"),
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
                kwargs["caption"] = kwargs["text"]
                kwargs.pop("text")
                func = query.message.reply_photo
    await func(**kwargs)


@Client.on_callback_query(filters.regex(r"^set_log_channel$"))
async def set_log_channel(bot: Client, query: CallbackQuery):
    try:
        ask_log_channel = await query.message.chat.ask(
            "Send me the new channel id or forward a message from the channel.",
            filters=filters.text | filters.forwarded,
        )
    except Exception as e:
        await query.message.reply_text(str(e))
        return

    if ask_log_channel.text and ask_log_channel.text.replace("-", "").isdigit():
        try:
            ask_log_channel = int(ask_log_channel.text)
        except ValueError:
            await query.message.reply_text("Invalid Channel ID.")
            return
    elif ask_log_channel.forward_from_chat:
        ask_log_channel = ask_log_channel.forward_from_chat.id
    else:
        await query.message.reply_text("Invalid Channel ID.")
        return

    try:
        chat = await bot.get_chat(ask_log_channel)
    except Exception as e:
        await query.message.reply_text("Bot is not an admin in the channel.")
        return

    await db.users.update_user(query.from_user.id, {"log_channel": ask_log_channel})

    await query.message.reply_text(
        f"Channel updated! - {chat.title}",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("⋞ ʙ ᴀ ᴄ ᴋ ⋟", "log_channel")]]
        ),
    )


@Client.on_callback_query(filters.regex(r"^remove_log_channel$"))
async def remove_log_channel(bot: Client, query: CallbackQuery):
    # with confirmation
    return await query.message.edit(
        "Are you sure you want to remove the channel?",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Yes", "confirm_remove_log_channel"),
                    InlineKeyboardButton("No", "log_channel"),
                ]
            ]
        ),
    )


@Client.on_callback_query(filters.regex(r"^confirm_remove_log_channel$"))
async def confirm_remove_log_channel(bot: Client, query: CallbackQuery):
    await db.users.update_user(query.from_user.id, {"log_channel": 0})

    await query.message.edit(
        "Channel removed Successfully!",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("⋞ ʙ ᴀ ᴄ ᴋ ⋟", "log_channel")]]
        ),
    )
