from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "medical_chatbot"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
chats_collection = db["chats"]

def save_chat(user_msg, bot_msg):
    chat_doc = {
        "user": user_msg,
        "bot": bot_msg
    }
    chats_collection.insert_one(chat_doc)
