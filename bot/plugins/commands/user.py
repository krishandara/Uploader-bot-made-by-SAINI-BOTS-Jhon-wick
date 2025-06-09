from pyrogram import Client, filters, types
from database import db
from bot.config import Config


@Client.on_message(
    filters.command("user")
    & filters.private
    & filters.incoming
    & filters.user(Config.OWNER_ID)
)
async def user_command(bot, message):
    if len(message.command) <= 1:
        return await message.reply_text(
            "Please specify a user id or username!\n\nExample: `/user 1234567890` or `/user @username`"
        )
    user_id = message.command[1]
    if user_id.isdigit():
        user_id = int(user_id)
    else:
        user_id = user_id.replace("@", "")
        try:
            user_id = (await bot.get_users(user_id)).id
        except Exception:
            return await message.reply_text("Invalid user id or username!")

    user = await db.users.get_user(user_id)
    try:
        tg_user = await bot.get_users(user_id)
    except Exception:
        tg_user = None
    if not user:
        return await message.reply_text("No user found with this id!")

    text = f"""
**User Details**
ID: {user['_id']}
Username: {tg_user.username if tg_user.username else 'Not Available'}
Banned: {user['banned']}
"""
    markup = types.InlineKeyboardMarkup(
        [
            [
                types.InlineKeyboardButton(
                    "Ban User" if not user["banned"] else "Unban User",
                    callback_data=f"ban_user_{user['_id']}",
                ),
            ]
        ]
    )
    await message.reply_text(text, reply_markup=markup)
    return


@Client.on_callback_query(filters.regex(r"ban_user_"))
async def ban_user(bot, cq):
    user_id = int(cq.data.split("_")[-1])
    user = await db.users.get_user(user_id)
    if not user:
        return await cq.answer("User not found in database!", show_alert=True)
    await db.users.update_user(user_id, {"banned": not user["banned"]})
    user = await db.users.get_user(user_id)
    await cq.answer(
        f"User {'banned' if user['banned'] else 'unbanned'} successfully!",
        show_alert=True,
    )
    await cq.message.delete()
    cq.message.from_user = cq.from_user

    cq.message.command = ["user", str(user_id)]
    await user_command(bot, cq.message)
    return