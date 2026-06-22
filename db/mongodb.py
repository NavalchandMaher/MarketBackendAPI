from pymongo import MongoClient
from config import MONGO_URI, DATABASE_NAME

client = MongoClient(MONGO_URI)

db = client[DATABASE_NAME]

trades = db["trades"]
performance = db["performance"]
strategies = db["strategies"]