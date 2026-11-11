
import os
import certifi

from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "sentinel_db")

client = MongoClient(
    MONGODB_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=20000,
    connectTimeoutMS=20000
)

# Test connection
try:
    client.admin.command("ping")

    print("MongoDB Atlas connected successfully!")

    db = client[DATABASE_NAME]

    transactions_collection = db["transactions"]
    customers_collection = db["customers"]

    print(f"Database: {DATABASE_NAME}")
    print("Collections ready!")

except Exception as e:
    print("MongoDB connection failed!")
    print(type(e).__name__, str(e))
    raise
