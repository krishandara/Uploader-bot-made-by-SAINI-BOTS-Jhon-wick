from pyrogram import Client, filters
from pyrogram.types import Message
from bot.config import Config


@Client.on_message(
    filters.command("admin") & filters.private & filters.user(Config.OWNER_ID)
)
async def admin(client: Client, message: Message):
    text = """
**Admin Commands**

/add - Add an admin
/admins - Get all admins
/remove - Remove an admin
/users - Get all users
/user - Get User Orders, Ban/Unban User, Add/Remove Balance, Delete User
/broadcast - Broadcast a message to all users
    """

    await message.reply_text(text)
