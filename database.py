import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
# print(MongoClient)
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

try:
    client.admin.command("ping")
    print("MongoDB connected successfully!")
except (ConnectionFailure, ServerSelectionTimeoutError) as e:
    print("MongoDB connection failed:", e)
    sys.exit(1)

db = client["credit_risk"]
prediction_collection = db["predictions"]


