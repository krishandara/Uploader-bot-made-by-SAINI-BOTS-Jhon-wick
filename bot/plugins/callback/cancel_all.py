from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message
from bot.config import Config
from bot.utils import check


@Client.on_callback_query(filters.regex(r"cancel_all_(\w+)"))
@Client.on_message(filters.command("cancel"))
@check
async def cancel_all(bot: Client, query: CallbackQuery | Message):
    random_string = query.from_user.id
    func = query.reply if isinstance(query, Message) else query.message.reply

    if Config.CANCEL_DATA.get(random_string, True) is True:
        await func("No downloads are currently running!")
        return

    Config.CANCEL_DATA[random_string] = True

    if isinstance(query, Message):
        await query.reply("Download Cancelled!")
    else:
        await query.answer("Download Cancelled!")
