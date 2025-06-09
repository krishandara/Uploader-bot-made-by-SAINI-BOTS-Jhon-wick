from motor.motor_asyncio import AsyncIOMotorClient



class ConfigDB:
    def __init__(self, uri, database_name):
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db["config"]

    async def add_config(self, name, value):
        item = {
            "name": name,
            "value": value,
        }
        return await self.col.insert_one(item)

    async def get_config(self, name):
        return await self.col.find_one({"name": name})

    async def delete_config(self, name):
        return await self.col.delete_one({"name": name})

    async def update_config(self, name, value):
        return await self.col.update_one({"name": name}, {"$set": {"value": value}})