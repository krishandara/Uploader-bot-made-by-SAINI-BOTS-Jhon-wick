import asyncio
import os
import re
import time
import traceback
from pyrogram import Client, types, filters, errors
from bot.config import Config, Script
from bot.utils import (
    download_main,
    progress_for_pyrogram,
    create_thumbnail,
    get_video_details,
    format_url,
    format_caption,
    format_name,
    get_filename_from_headers,
)
from bot.utils.helpers import get_admins
from database import db


@Client.on_callback_query(filters.regex(r"download_(\d+)_(\d+)_(\d+)"))
async def callback_query_download(bot: Client, callback_query: types.CallbackQuery):
    # download_{message.id}_0_{len(urls)}
    message_id = int(callback_query.matches[0].group(1))
    start_index = int(callback_query.matches[0].group(2))
    end_index = int(callback_query.matches[0].group(3))
    message = await bot.get_messages(callback_query.message.chat.id, message_id)
    await callback_query.answer()
    await download(bot, message, start_index, end_index)


async def download(bot: Client, message: types.Message, start_index=0, end_index=-1):
    user_id = message.from_user.id
    if Config.CANCEL_DATA.get(user_id) is False:
        return await message.reply_text(
            "You have already started a download!, Please wait for it to complete."
        )

    if message.document:
        file = await message.download()
        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        batch_name = file.split(".")[0].split("/")[-1].replace("_", " ")
        os.remove(file)
    elif message.text:
        batch_name = ""
        text = message.text
    else:
        return await message.reply_text("Please send a text file or text with links!")

    pattern = re.compile(r"(?P<name>[^:]+):\s*(?P<link>https?://\S+)")
    matches = pattern.findall(text)
    urls = re.findall(r"https?://\S+", text)
    urls_with_names = {
        link: name.strip() if name.strip() else None for name, link in matches
    }

    raw_len = len(urls)
    end_index = len(urls) if end_index == -1 else end_index

    if start_index > end_index:
        return await message.reply_text(
            f"Start index must be less than end index ({end_index})!"
        )

    if end_index > len(urls):
        return await message.reply_text(
            f"End index must be less than the total number of URLs ({len(urls)})!"
        )

    urls = urls[start_index:end_index]

    if not urls:
        return await message.reply_text("No URLs found in the text!")

    out = await message.reply_text(f"Fetched {len(urls)} URLs!")
    files = []

    Config.CANCEL_DATA[user_id] = False

    cancel_markup = types.InlineKeyboardMarkup(
        [
            [
                types.InlineKeyboardButton(
                    text="Cancel All Downloads",
                    callback_data=f"cancel_all_{user_id}",
                )
            ]
        ]
    )

    for i, url in enumerate(urls, start=1):
        raw_index = start_index + i

        if not await is_admin(bot, message):
            return await out.delete()

        user = await db.users.get_user(message.from_user.id)
        drm_ext = user["ext"]
        og_url = url

        try:
            url = await format_url(url, user["quality"])
        except Exception as e:
            print(e)

        if bool(urls_with_names.get(url, "").replace(" ", "")):
            name = urls_with_names[url]
        elif bool(urls_with_names.get(og_url, "").replace(" ", "")):
            name = urls_with_names[og_url]
        else:
            try:
                name = get_filename_from_headers(url)
            except Exception as e:
                print(e)
                name = url.split("/")[-1].split("?")[0]

        name = format_name(name, url)

        edit_func = await message.reply_text(
            Script.DOWNLOADING.format(
                start_index=i,
                end_index=len(urls),
                link_no=i,
                name=name,
                orginal_start_index=raw_index,
                orginal_end_index=raw_len,
            ),
        )

        if Config.CANCEL_DATA.get(user_id) is True or user_id not in Config.CANCEL_DATA:
            cleanup(None, None, user_id)
            await edit_func.edit("Cancelled all downloads!")
            break

        try:
            output_path, is_media = await download_main(
                name, user["quality"], url, drm_ext
            )
            files.append(output_path)
            await edit_func.edit(f"Downloaded {name}!")
            start = time.time()

            if is_media:
                if not user["thumbnail_enabled"] or not user["thumbnail"]:
                    thumbnail = await create_thumbnail(output_path)
                else:
                    thumbnail = await bot.download_media(user["thumbnail"])
            else:
                if user["thumbnail_enabled"] and user["thumbnail"]:
                    thumbnail = await bot.download_media(user["thumbnail"])
                else:
                    thumbnail = None

            if drm_ext == "mp4" and output_path.endswith(".mp4"):
                func = bot.send_video
                width, height, duration = await get_video_details(output_path)
                kwargs = {
                    "video": output_path,
                    "duration": duration,
                    "width": width,
                    "height": height,
                    "chat_id": user["log_channel"] or message.chat.id,
                }
            else:
                func = bot.send_document
                kwargs = {"chat_id": user["log_channel"] or message.chat.id, "document": output_path}

            if thumbnail:
                kwargs["thumb"] = thumbnail

            if user["custom_caption_enabled"] and user["custom_caption"]:
                caption = format_caption(
                    custom_caption=user["custom_caption"],
                    output_path=output_path,
                    url=url,
                    is_media=is_media,
                    file_index=raw_index,
                    batch_name=batch_name,
                )
            else:
                caption = name

            log, reply_text = await floodwait_handler(
                func,
                caption=caption,
                progress=progress_for_pyrogram,
                progress_args=(start, edit_func.edit, user_id, cancel_markup),
                **kwargs,
            )

            if reply_text:
                await edit_func.edit(reply_text)
                cleanup(output_path, thumbnail, user_id)
                return

            if log is None:
                await edit_func.edit("Cancelled all downloads!")
                cleanup(output_path, thumbnail, user_id)
                break

            await copy_message(log, Config.LOG_CHANNEL, message)
            await add_file_to_db(log, url, name, user["quality"], is_media)
            await edit_func.delete()

            cleanup(output_path, thumbnail, None)

        except Exception as e:
            traceback.print_exc()
            await edit_func.edit(
                f"Failed to download {url}!\n\n{str(e).replace(url, '')}"
            )
            continue

    await message.reply_text("All downloads completed!", quote=True)
    await out.delete()

    cleanup(None, None, user_id)


async def floodwait_handler(func, *args, **kwargs):
    try:
        return await func(*args, **kwargs), ""
    except errors.FileReferenceExpired:
        return (
            None,
            "You are using an expired thumbnail, please upload a new one and try again!",
        )
    except errors.FloodWait as e:
        await asyncio.sleep(e.value)
        return await floodwait_handler(func, *args, **kwargs), ""


async def copy_message(
    message: types.Message, chat_id: int, user_message: types.Message
):
    caption = message.caption.html if message.caption else None
    try:
        copy_mes = await message.copy(chat_id, caption=caption)

        await copy_mes.reply_text(text, disable_web_page_preview=True)

    except Exception as e:
        print(e)


async def add_file_to_db(
    message: types.Message, file_url, file_name, file_quality, is_media
):
    chat_id = message.chat.id
    message_id = message.id
    await db.files.create_file(
        message_id, chat_id, file_url, file_name, file_quality, is_media
    )


async def is_admin(bot: Client, message: types.Message):
    chat_id = getattr(message.from_user, "id", None)
    admins = await get_admins()

    if chat_id not in admins:
        # <button> [Owner](t.me/Alonedada143)
        markup = types.InlineKeyboardMarkup(
            [[types.InlineKeyboardButton("Owner", url="https://t.me/The_real_xTaR")]]
        )
        await message.reply_text(
            "You are not allowed to use this bot. If you want to use me first talk to Owner to use me",
            reply_markup=markup,
        )
        cleanup(None, None, chat_id)
        return False

    banned_users = await db.users.filter_users({"banned": True})
    banned_users = [user["_id"] for user in banned_users]
    if chat_id in banned_users:
        await message.reply_text("You are banned from using the bot!")
        cleanup(None, None, chat_id)
        return False
    return True


def cleanup(file_path, thumbnail, user_id):
    file_path = str(file_path)
    thumbnail = str(thumbnail)
    os.remove(file_path) if os.path.exists(file_path) else None
    os.remove(thumbnail) if os.path.exists(thumbnail) else None
    if user_id:
        Config.CANCEL_DATA[user_id] = True
