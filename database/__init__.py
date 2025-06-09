from .users import UserDatabase
from bot.config import Config
from .config import ConfigDB
from .files import FilesDatabase

class Database:
    def __init__(self):
        self.users = UserDatabase(Config.DATABASE_URL, Config.DATABASE_NAME)
        self.config = ConfigDB(Config.DATABASE_URL, Config.DATABASE_NAME)
        self.files = FilesDatabase(Config.DATABASE_URL, Config.DATABASE_NAME)

db = Database()
