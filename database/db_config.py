import os
from motor.motor_asyncio import AsyncIOMotorClient


mongo_client : AsyncIOMotorClient = None

def get_mongo_client() -> AsyncIOMotorClient:
    try:
        global mongo_client
        mongo_client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
        print("database connected")
    except Exception as e:
        print(e)

def get_token_collection():
    database = mongo_client.get_database("desktoken")
    return database["token"]