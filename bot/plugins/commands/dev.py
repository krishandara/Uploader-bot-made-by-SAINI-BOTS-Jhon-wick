from pyrogram import Client, filters, types
from pyrogram.types import Message
from bot.config import Script


@Client.on_message(filters.command("saini") & filters.private & filters.incoming)
@Client.on_message(filters.regex("saini") & filters.private & filters.incoming)
async def start(bot: Client, message: Message):
    markup = types.InlineKeyboardMarkup(
        [
            [
                types.InlineKeyboardButton(
                    "🛠️Help", url="https://t.me/saini_contact_bot"
                ),
                types.InlineKeyboardButton(
                    "🛠️Repo", url="https://github.com/nikhilsainiop/Uploader-bot-made-by-SAINI-BOTS-Jhon-wick"
                ),
            ],
        ]
    )
    await message.reply_text(
        Script.DEV_MESSAGE,
        disable_web_page_preview=True,
        quote=True,
        reply_markup=markup,
    )
