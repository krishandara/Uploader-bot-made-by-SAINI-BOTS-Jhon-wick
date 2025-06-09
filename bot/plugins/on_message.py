import os
import re
from pyrogram import Client, ContinuePropagation, filters, types
from bot.plugins.download import download
from bot.utils import check


@Client.on_message(
    filters.incoming & filters.private & (filters.document | filters.text)
)
@check
async def on_document_or_text(bot: Client, message: types.Message):
    sts = await message.reply_text("Processing...", quote=True)
    if message.document and message.document.mime_type == "text/plain":
        file = await message.download()
        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        os.remove(file)
    elif message.text and not message.text.startswith("/"):
        text = message.text
    else:
        await sts.delete()
        raise ContinuePropagation

    urls = re.findall(r"https?://\S+", text)
    if not urls:
        return await sts.edit("No URLs found in the text!")

    if len(urls) > 1:
        markup = types.InlineKeyboardMarkup(
            [
                [
                    types.InlineKeyboardButton(
                        text=f"Select Index (0 - {len(urls)})",
                        callback_data=f"select_index_{message.id}_{len(urls)}",
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text=f"Download All ({len(urls)})",
                        callback_data=f"download_{message.id}_0_{len(urls)}",
                    )
                ],
            ]
        )
        return await sts.edit(
            f"Multiple URLs found in the text ({len(urls)})!", reply_markup=markup
        )
    else:
        await sts.delete()
        await download(bot, message, 0, -1)