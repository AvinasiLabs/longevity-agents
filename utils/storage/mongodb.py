from typing import Union
from pymongo import MongoClient


# local module
# from utils.storage import GLOBAL_CONFIG
from utils.config_wrapper import MongoConfig


class MongoStorage:
    def __init__(self, config: MongoConfig = None) -> None:
        self.config = config or MongoConfig()
        self.client = MongoClient(self.config.conn_str)
        db = self.client[self.config.db_name]
        self.collection = db[self.config.coll_name]

    def upsert(self, record: dict, is_on_insert=True):
        try:
            self.collection.update_one(
                {"_id": record["_id"]},
                {"$setOnInsert": record} if is_on_insert else {"$set": record},
                upsert=True,
            )
        except Exception as e:
            raise e

    def insert_one(self, record: dict):
        try:
            self.collection.insert_one(record)
        except Exception as e:
            raise e


MONGO = MongoStorage()
