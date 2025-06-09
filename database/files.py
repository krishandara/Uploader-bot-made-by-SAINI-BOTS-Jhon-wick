from motor.motor_asyncio import AsyncIOMotorClient


class FilesDatabase:
    def __init__(self, uri, database_name):
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db["files"]

    async def create_file(self, message_id, chat_id, file_url, file_name, file_quality, is_media):
        return await self.col.insert_one(
            {
                "message_id": message_id,
                "chat_id": chat_id,
                "file_url": file_url,
                "file_name": file_name,
                "file_quality": file_quality,
                "is_media": is_media,
            }
        )

    async def filter_files(self, query):
        return await self.col.find(query).to_list(length=None)

    async def filter_file(self, query):
        return await self.col.find_one(query)