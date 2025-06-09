from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from bot.config import Config, Script
from bot.utils import add_user, check
from database import db


@Client.on_message(filters.command("cancel_data") & filters.private & filters.incoming)
@check
async def cancel_data(bot: Client, message: Message):
    # CANCEL_DATA = {user_id: false}
    text = ""
    for user_id, value in Config.CANCEL_DATA.items():
        try:
            user = await bot.get_users(user_id)
            text += f"👤 {user.mention} - {value}\n"
        except Exception as e:
            print(e)
            continue
    if not text:
        text = "No data found"

    await message.reply_text(text)

    await message.reply_text(str(Config.CANCEL_DATA))