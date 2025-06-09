from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from bot.plugins.download import download


@Client.on_callback_query(filters.regex(r"select_index_(\d+)"))
async def select_index(bot: Client, query: CallbackQuery):
    message_id = int(query.data.split("_")[2])
    total = int(query.data.split("_")[3])
    message = await bot.get_messages(query.message.chat.id, message_id)

    try:
        start_index = await query.message.chat.ask(
            f"Enter the start index between 1 and {total}:\n\n/cancel to cancel the operation",
        )
        if start_index.text == "/cancel":
            return await query.message.reply_text("Operation cancelled!")
        start_index = int(start_index.text)
    except Exception as e:
        return await query.message.reply_text("Invalid start index!")

    try:
        end_index = await query.message.chat.ask(
            f"Enter the end index between {start_index} and {total}:\n\n/cancel to cancel the operation",
        )
        if end_index.text == "/cancel":
            return await query.message.reply_text("Operation cancelled!")
        end_index = int(end_index.text)
    except Exception as e:
        return await query.message.reply_text("Invalid end index!")

    await download(bot, message, start_index - 1, end_index)
    await query.message.delete()