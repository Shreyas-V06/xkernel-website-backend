from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

def initialize_db():
    client = AsyncIOMotorClient(os.getenv("CONNECTION_STRING"))
    return client.get_database("xkerneldb")